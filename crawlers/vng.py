import asyncio
from bs4 import BeautifulSoup
from utils import should_filter_job, send_telegram_message_async, fetch_url_async
from config import BOT_TOKEN, CHAT_ID, today

async def crawl_vng_jobs():
    """Crawl VNG jobs with parallel requests"""
    print("Crawling VNG jobs...")
    all_titles_vng = []
    
    # Create URLs for all pages
    urls = [f'https://career.vng.com.vn/tim-kiem-viec-lam?job_group=385%7C418&page={page}' 
            for page in range(1, 11)]
    
    # Fetch all pages in parallel
    tasks = [fetch_url_async(url) for url in urls]
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    for response in responses:
        if isinstance(response, Exception) or response is None:
            continue
            
        soup = BeautifulSoup(response, 'html.parser')
        job_links = soup.find_all('a', class_='group relative go-to-detail')

        for tag in job_links:
            title = tag.get_text(strip=True)
            if not should_filter_job(title):
                all_titles_vng.append(f'• {title}')

    message_vng = f"📢 <b><a href='https://career.vng.com.vn/tim-kiem-viec-lam?job_group=385%7C418&page=1'>VNG</a> hôm nay ({today}):</b>\n" + '\n'.join(all_titles_vng)
    await send_telegram_message_async(BOT_TOKEN, CHAT_ID, message_vng)
    print(f"VNG: Found {len(all_titles_vng)} jobs") 