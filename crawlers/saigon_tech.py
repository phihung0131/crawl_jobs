from utils import should_filter_job, send_telegram_message_async, fetch_url_async
from config import BOT_TOKEN, CHAT_ID, today

async def crawl_saigon_tech_jobs():
    """Crawl Saigon Technology jobs"""
    print("Crawling Saigon Technology jobs...")
    all_titles_saigon = []

    # API URL with query parameters
    url = 'https://careers.saigontechnology.com/api/jobs?page=1&limit=20&location%5B0%5D=Ho%20Chi%20Minh'
    
    try:
        # Set custom headers for API request
        response = await fetch_url_async(url, is_json=True)
        if response and 'jobs' in response:
            jobs = response['jobs']
            for job in jobs:
                job_title = job.get('title', '')
                if not should_filter_job(job_title):
                    # Add location and contract type for more details
                    job_info = f"• {job_title} ({job.get('location', '')}, {job.get('contractType', '')})"
                    all_titles_saigon.append(job_info)

    except Exception as e:
        print(f"Failed to load Saigon Technology jobs: {e}")

    message_saigon = f"📢 <b><a href='https://careers.saigontechnology.com/opening-jobs?location=Ho%20Chi%20Minh&job_level=Fresher%2CJunior'>Saigon Technology</a> hôm nay ({today}):</b>\n" + '\n'.join(all_titles_saigon)
    await send_telegram_message_async(BOT_TOKEN, CHAT_ID, message_saigon)
    print(f"Saigon Technology: Found {len(all_titles_saigon)} jobs") 