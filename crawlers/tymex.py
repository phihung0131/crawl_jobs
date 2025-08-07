from bs4 import BeautifulSoup
from utils import should_filter_job, send_telegram_message_async, post_url_async
from config import BOT_TOKEN, CHAT_ID, today

async def crawl_tymex_jobs():
    """Crawl TymeX jobs"""
    print("Crawling TymeX jobs...")
    all_titles_tymex = []
    url = 'https://vietnam.tyme.com/wp-admin/admin-ajax.php?mona-ajax'
    
    form_data = {
        'action': 'mona_ajax_pagination',
        'form': 'term[category_recruitment_location]=ho-chi-minh&keyword=&per_paged=100&tab=engineering'
    }
    
    response = await post_url_async(url, data=form_data)
    if response and response.get('success') and response.get('data', {}).get('contents'):
        html_content = response['data']['contents']
        soup = BeautifulSoup(html_content, 'html.parser')
        job_titles = soup.find_all('h3', class_='job-name')
        
        for title in job_titles:
            job_title = title.get_text(strip=True)
            if not should_filter_job(job_title):
                all_titles_tymex.append(f'• {job_title}')
    
    if (len(all_titles_tymex) > 0):
        message_tymex = f"📢 <b><a href='https://vietnam.tyme.com/#sec-career'>TymeX</a> hôm nay ({today}):</b>\n" + '\n'.join(all_titles_tymex)
        await send_telegram_message_async(BOT_TOKEN, CHAT_ID, message_tymex)
    print(f"TymeX: Found {len(all_titles_tymex)} jobs") 