from playwright.async_api import async_playwright
from utils import should_filter_job, send_telegram_message_async
from config import BOT_TOKEN, CHAT_ID, today

async def crawl_zalo_jobs():
    """Crawl Zalo jobs"""
    print("Crawling Zalo jobs...")
    all_titles_zalo = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])  # --no-sandbox for GitHub Actions
        page = await browser.new_page()

        for page_num in range(1, 6):
            url = f"https://zalo.careers/job-list?page={page_num}&locations=ho-chi-minh&teams=engineering"

            try:
                await page.goto(url, timeout=5000)  # 5s timeout
                await page.wait_for_selector('h2.text.line-clamp-2', timeout=5000)  # wait for selector (JS render)
                titles = await page.locator('h2.text.line-clamp-2').all_text_contents()

                for title in titles:
                    job_title = title.strip()
                    if not should_filter_job(job_title):
                        all_titles_zalo.append(f"• {job_title}")

            except Exception as e:
                print(f"Failed to load page {page_num}: {e}")

        await browser.close()

    message_zalo = f"📢 <b><a href='https://zalo.careers/job-list?teams=engineering&page=1&locations=ho-chi-minh'>ZALO</a> hôm nay ({today}):</b>\n" + '\n'.join(all_titles_zalo)
    await send_telegram_message_async(BOT_TOKEN, CHAT_ID, message_zalo)
        
    print(f"Zalo: Found {len(all_titles_zalo)} jobs") 