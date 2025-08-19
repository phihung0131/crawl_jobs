from bs4 import BeautifulSoup
from utils import should_filter_job, send_telegram_message_async, fetch_url_async
from config import BOT_TOKEN, CHAT_ID, today

async def crawl_grab_jobs():
    """Crawl Grab jobs"""
    print("Crawling Grab jobs...")
    all_titles_grab = []
    url = 'https://www.grab.careers/en/jobs/?search=&team=Engineering&team=Internship&team=Technology+Solutions&country=Vietnam&pagesize=100#results'
    
    response = await fetch_url_async(url)
    if response:
        soup = BeautifulSoup(response, 'html.parser')
        job_links = soup.find_all('a', class_='stretched-link js-view-job')

        for tag in job_links:
            title = tag.get_text(strip=True)
            if not should_filter_job(title):
                all_titles_grab.append(f'• {title}')

    message_grab = f"📢 <b><a href='https://www.grab.careers/en/jobs/?search=&team=Engineering&team=Internship&team=Technology+Solutions&country=Vietnam&pagesize=100#results'>GRAB</a> hôm nay ({today}):</b>\n" + '\n'.join(all_titles_grab)
    await send_telegram_message_async(BOT_TOKEN, CHAT_ID, message_grab)
    print(f"Grab: Found {len(all_titles_grab)} jobs") 