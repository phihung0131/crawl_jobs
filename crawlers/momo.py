from bs4 import BeautifulSoup
from utils import should_filter_job, send_telegram_message_async, fetch_url_async
from config import BOT_TOKEN, CHAT_ID, today

async def crawl_momo_jobs():
    """Crawl MoMo jobs"""
    print("Crawling MoMo jobs...")
    all_titles_momo = []
    url = 'https://momo.careers/jobs-opening?location=PJL.0001&groups=DGM.0001&levelGroups=LEV.002%2CLEV.003%2CLEV.004%2CLEV.005%2CLEV.006%2CLEV.007%2CLEV.008%2CLEV.009%2CLEV.001%2CLEV.020%2CLEVEL.0022'
    
    response = await fetch_url_async(url)
    if response:
        soup = BeautifulSoup(response, 'html.parser')
        job_titles = soup.find_all('div', class_='text-base font-semibold duration-300 group-hover:text-pink-500 md:text-lg')

        for title in job_titles:
            job_title = title.get_text(strip=True)
            if not should_filter_job(job_title):
                all_titles_momo.append(f'• {job_title}')

    message_momo = f"📢 <b><a href='https://momo.careers/jobs-opening?location=PJL.0001&groups=DGM.0001&levelGroups=LEV.002%2CLEV.003%2CLEV.004%2CLEV.005%2CLEV.006%2CLEV.007%2CLEV.008%2CLEV.009%2CLEV.001%2CLEV.020%2CLEVEL.0022'>MoMo</a> hôm nay ({today}):</b>\n" + '\n'.join(all_titles_momo)
    await send_telegram_message_async(BOT_TOKEN, CHAT_ID, message_momo)
    print(f"MoMo: Found {len(all_titles_momo)} jobs") 