from playwright.async_api import async_playwright
from utils import should_filter_job, send_telegram_message_async
from config import BOT_TOKEN, CHAT_ID, today

async def crawl_kms_jobs():
    print("Crawling KMS jobs...")
    all_titles_kms = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page()

        url = 'https://careers.kms-technology.com/job/?keyword=fresher&location=Ho%20Chi%20Minh&jobs_type=Fresher'

        try:
            # Đặt User-Agent giống trình duyệt thật
            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
            })

            await page.goto(url, timeout=20000)

            # Đợi Cloudflare challenge qua (khác "Just a moment...")
            await page.wait_for_function("document.title !== 'Just a moment...'", timeout=20000)

            # Đợi job title xuất hiện
            await page.wait_for_selector('h6.job_title', timeout=10000)

            titles = await page.locator('h6.job_title').all_text_contents()

            for title in titles:
                job_title = title.strip()
                if not should_filter_job(job_title):
                    all_titles_kms.append(f"• {job_title}")

        except Exception as e:
            print(f"Failed to load KMS jobs: {e}")
            # debug content nếu cần
            content = await page.content()
            print("Page snapshot:", content[:1000])

        await browser.close()

    message_kms = f"📢 <b><a href='{url}'>KMS Technology</a> hôm nay ({today}):</b>\n" + '\n'.join(all_titles_kms)
    await send_telegram_message_async(BOT_TOKEN, CHAT_ID, message_kms)
    print(f"KMS: Found {len(all_titles_kms)} jobs")
