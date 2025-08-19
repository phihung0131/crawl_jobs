import asyncio
from utils import should_filter_job, send_telegram_message_async, fetch_url_async
from config import BOT_TOKEN, CHAT_ID, today

async def crawl_shopee_jobs():
    """Crawl Shopee jobs with parallel requests"""
    print("Crawling Shopee jobs...")
    all_titles_shopee = []
    
    tasks = []
    url = f'https://ats.workatsea.com/ats/api/v1/user/job/list/?limit=50&offset=0&city_ids=34&department_ids=6&employment_ids=4&employment_ids=1&employment_ids=2'
    tasks.append(fetch_url_async(url, is_json=True))
    
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    for response in responses:
        if isinstance(response, Exception) or response is None:
            continue
            
        if response.get('code') == 0 and response.get('message') == 'success':
            job_list = response.get('data', {}).get('job_list', [])
            
            for job in job_list:
                job_title = job.get('job_name', '')
                if not should_filter_job(job_title):
                    all_titles_shopee.append(f'• {job_title}')

    message_shopee = f"📢 <b><a href='https://careers.shopee.vn/jobs?region_id=34&dept_id=&level=4,1,2&limit=50&offset=50'>Shopee</a> hôm nay ({today}):</b>\n" + '\n'.join(all_titles_shopee)
    await send_telegram_message_async(BOT_TOKEN, CHAT_ID, message_shopee)
    print(f"Shopee: Found {len(all_titles_shopee)} jobs") 