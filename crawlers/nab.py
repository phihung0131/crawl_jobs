import asyncio
from utils import should_filter_job, send_telegram_message_async, post_url_async
from config import BOT_TOKEN, CHAT_ID, today

async def crawl_nab_jobs():
    """Crawl NAB jobs with parallel requests"""
    print("Crawling NAB jobs...")
    all_titles_nab = []
    url = "https://nab.wd3.myworkdayjobs.com/wday/cxs/nab/nab_careers/jobs"
    
    # Create payloads for different offsets
    offsets = range(0, 100, 20)
    tasks = []
    
    for offset in offsets:
        payload = {
            "appliedFacets": {
                "locationCountry": ["db69e8c8446c11de98360015c5e6daf6"],
                "locations": [
                    "25e34c7b3e6410009a643b05986b0000",
                    "2b5ebaf8c9281000c02f3491eccc0000"
                ],
                "jobFamilyGroup": [
                    "28c588c0cf7a100144e1f2afbffe0000"
                ]
            },
            "limit": 20,
            "offset": offset,
            "searchText": ""
        }
        tasks.append(post_url_async(url, json_data=payload))
    
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    for response in responses:
        if isinstance(response, Exception) or response is None:
            continue
            
        job_postings = response.get('jobPostings', [])
        for job in job_postings:
            title = job.get('title', 'No Title')
            if not should_filter_job(title):
                all_titles_nab.append(f'• {title}')

    if (len(all_titles_nab) > 0):
        message_nab = f"📢 <b><a href='https://nab.wd3.myworkdayjobs.com/nab_careers?locationCountry=db69e8c8446c11de98360015c5e6daf6&locations=25e34c7b3e6410009a643b05986b0000&locations=2b5ebaf8c9281000c02f3491eccc0000&jobFamilyGroup=28c588c0cf7a100144e1f2afbffe0000'>NAB</a> hôm nay ({today}):</b>\n" + '\n'.join(all_titles_nab)
        await send_telegram_message_async(BOT_TOKEN, CHAT_ID, message_nab)
    print(f"NAB: Found {len(all_titles_nab)} jobs") 