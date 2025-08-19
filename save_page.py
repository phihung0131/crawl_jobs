import argparse, time, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

JS_VISIBILITY_LOCK = r"""
// luôn coi như tab đang visible (ngăn unmount khi mất focus)
try {
  Object.defineProperty(Document.prototype, 'hidden', { get: () => false });
  Object.defineProperty(Document.prototype, 'visibilityState', { get: () => 'visible' });
} catch(e){}
document.addEventListener = new Proxy(document.addEventListener, {
  apply(t, thisArg, args) {
    if (args && args[0] === 'visibilitychange') return; // nuốt đăng ký visibilitychange
    return Reflect.apply(t, thisArg, args);
  }
});
"""

JS_DISABLE_ANIM_HIDE = r"""
// tắt animation/transition và bỏ ẩn phổ biến
const style = document.createElement('style');
style.textContent = `
 *{animation:none!important;transition:none!important}
 .cdk-visually-hidden{position:static!important;width:auto!important;height:auto!important;overflow:visible!important;clip:auto!important}
 [hidden]{display:block!important}
 [style*="display:none"]{display:block!important}
`;
document.head.appendChild(style);
document.querySelectorAll('[aria-hidden="true"]').forEach(e => e.setAttribute('aria-hidden','false'));
"""

JS_EAGER_MEDIA = r"""
// ép ảnh/iframe lazy thành eager, thay data-src/srcset
document.querySelectorAll('img').forEach(img => {
  if (img.dataset.src) img.src = img.dataset.src;
  if (img.dataset.srcset) img.srcset = img.dataset.srcset;
  img.loading = 'eager';
});
document.querySelectorAll('iframe').forEach(f => {
  if (f.dataset.src) f.src = f.dataset.src;
  f.loading = 'eager';
});
"""

JS_FORCE_IO_VISIBLE = r"""
// IntersectionObserver hack: coi như luôn intersecting
(() => {
  if (window.__io_patched__) return;
  const _IO = window.IntersectionObserver;
  window.IntersectionObserver = class extends _IO {
    constructor(cb, options){
      super((entries, obs) => {
        const forced = entries.map(e => Object.assign({}, e, { isIntersecting: true, intersectionRatio: 1 }));
        cb(forced, obs);
      }, options);
    }
  };
  window.__io_patched__ = true;
})();
"""

JS_SNAPSHOT_OVERLAY = r"""
// clone overlay của Angular Material nếu có
(() => {
  const overlay = document.querySelector('.cdk-overlay-container');
  let snap = document.querySelector('#snapshot-all-items');
  if (!snap) {
    snap = document.createElement('div');
    snap.id = 'snapshot-all-items';
    snap.style.cssText='max-width:1200px;margin:24px auto;padding:12px;border:1px dashed #bbb;background:#fff';
    const title = document.createElement('h2');
    title.textContent = 'SNAPSHOT – All items (cloned while scrolling)';
    title.style.cssText='font:600 20px/1.4 system-ui;margin:0 0 12px';
    snap.appendChild(title);
    document.body.prepend(snap);
  }
  if (overlay) snap.appendChild(overlay.cloneNode(true));
})();
"""

JS_MAKE_ABSOLUTE_BASE = r"""
// đặt <base> để khi mở file local thì URL tương đối vẫn trỏ đúng domain gốc
(() => {
  const old = document.querySelector('base');
  if (old) old.remove();
  const base = document.createElement('base');
  base.href = location.origin + location.pathname;
  document.head.prepend(base);
})();
"""

def auto_scroll(page, step_ratio=0.9, pause_ms=350, max_loops=150, item_selector=None):
    """Cuộn xuống dần cho đến khi chiều cao trang không tăng thêm 3 lần liên tiếp
       hoặc đạt max_loops. Nếu có item_selector, dùng nó để trigger render thêm."""
    prev_h = 0
    stable = 0
    for i in range(max_loops):
        page.evaluate(f"window.scrollBy(0, Math.floor(window.innerHeight*{step_ratio}))")
        page.dispatch_event("body", "scroll")
        page.wait_for_timeout(pause_ms)

        # Nếu có container virtual scroll phổ biến, thử cuộn nhẹ trong đó
        for sel in ("cdk-virtual-scroll-viewport, .cdk-virtual-scroll-viewport",
                    "[style*='overflow: auto'],[style*='overflow:auto']"):
            try:
                vps = page.query_selector_all(sel)
                for vp in vps:
                    # cuộn 80% chiều cao viewport
                    page.evaluate("(el)=>{ el.scrollTop = el.scrollTop + el.clientHeight*0.8 }", vp)
            except:
                pass

        curr_h = page.evaluate("document.body.scrollHeight")
        if curr_h == prev_h:
            stable += 1
        else:
            stable = 0
            prev_h = curr_h
        if stable >= 3:
            break

    # cuộn ngược vài bước để kích lazy lần nữa
    for _ in range(6):
        page.evaluate(f"window.scrollBy(0, Math.floor(-window.innerHeight*{step_ratio}))")
        page.dispatch_event("body", "scroll")
        page.wait_for_timeout(180)

    # nếu có item selector, cố gắng lướt nhanh để “quét” thêm
    if item_selector:
        try:
            page.wait_for_selector(item_selector, timeout=3000)
        except:
            pass

def main():
    ap = argparse.ArgumentParser(description="Save fully-rendered HTML (handles lazy/virtual scroll).")
    ap.add_argument("url", help="Trang cần lưu")
    ap.add_argument("--out", default="page_saved.html", help="Tên file đầu ra (HTML)")
    ap.add_argument("--max-loops", type=int, default=150, help="Số bước cuộn tối đa")
    ap.add_argument("--item", default=None, help="Selector của 1 item trong list (tăng độ chắc chắn)")
    ap.add_argument("--headful", action="store_true", help="Mở browser có giao diện")
    args = ap.parse_args()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headful,
                                    args=["--disable-web-security", "--disable-blink-features=AutomationControlled"])
        ctx = browser.new_context(accept_downloads=True, viewport={"width": 1400, "height": 1000})
        page = ctx.new_page()

        # vào trang và chờ network idle
        page.goto(args.url, wait_until="networkidle", timeout=180_000)

        # tiêm các patch trước khi scroll
        for js in (JS_VISIBILITY_LOCK, JS_DISABLE_ANIM_HIDE, JS_EAGER_MEDIA, JS_FORCE_IO_VISIBLE, JS_MAKE_ABSOLUTE_BASE):
            page.add_init_script(js)
            page.evaluate(js)

        # auto scroll (kể cả trong virtual scroll container)
        auto_scroll(page, max_loops=args.max_loops, item_selector=args.item)

        # chờ yên 2s
        page.wait_for_timeout(2000)

        # thử clone overlay nếu có
        try:
            page.evaluate(JS_SNAPSHOT_OVERLAY)
        except:
            pass

        # lấy DOM sau render
        html = page.content()

        Path(args.out).write_text(html, encoding="utf-8")
        print(f"[OK] Saved to {args.out}")

        browser.close()

if __name__ == "__main__":
    main()
