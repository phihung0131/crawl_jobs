import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
import time
import asyncio
from playwright.async_api import async_playwright

BOT_TOKEN = '8155238330:AAH2t2i3zk7v8yzGnP73bw0PiJTmpgI-Ovw' 
CHAT_ID = '5713801301'   

# Hash ngày thành chuỗi MD5
today = datetime.now().strftime('%d-%m-%Y')

# Từ khóa cần lọc chung cho tất cả công ty
FILTER_KEYWORDS = ['Senior', 'Middle', 'Lead', 'Manager', 'Head', 'Mid', 'Associate', 'Analyst', 
                   'Medior', 'Consultant', 'Principal', 'Solution', 'Director', 'Customer', 
                   'Business', 'PMO', 'Affiliate', 'Recruiter', 'Master']

# Session cho tái sử dụng kết nối
session = None

def should_filter_job(job_title):
    """Kiểm tra job title có chứa từ khóa cần lọc không"""
    job_lower = job_title.lower()
    return any(keyword.lower() in job_lower for keyword in FILTER_KEYWORDS)

async def send_telegram_message_async(bot_token, chat_id, message):
    """Gửi tin nhắn Telegram bất đồng bộ"""
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML',
    }
    
    async with session.post(url, data=payload) as response:
        return await response.json()

async def fetch_url_async(url, is_json=False):
    """Fetch URL bất đồng bộ"""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
            if is_json:
                return await response.json()
            return await response.text()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

async def post_url_async(url, data=None, json_data=None):
    """POST request bất đồng bộ"""
    try:
        if json_data:
            async with session.post(url, json=json_data, timeout=aiohttp.ClientTimeout(total=10)) as response:
                return await response.json()
        elif data:
            async with session.post(url, data=data, timeout=aiohttp.ClientTimeout(total=10)) as response:
                return await response.json()
    except Exception as e:
        print(f"Error posting to {url}: {e}")
        return None

async def crawl_vng_jobs():
    """Crawl VNG jobs với parallel requests"""
    print("Crawling VNG jobs...")
    all_titles_vng = []
    
    # Tạo các URL cho tất cả trang
    urls = [f'https://career.vng.com.vn/tim-kiem-viec-lam?job_group=385%7C418&page={page}' 
            for page in range(1, 11)]
    
    # Fetch tất cả trang song song
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

async def crawl_zalo_jobs():
    """Crawl Zalo jobs"""
    print("Crawling Zalo jobs...")
    all_titles_zalo = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])  # --no-sandbox giúp chạy trên GitHub Actions
        page = await browser.new_page()

        for page_num in range(1, 6):
            url = f"https://zalo.careers/job-list?page={page_num}&locations=ho-chi-minh&teams=engineering"

            try:
                await page.goto(url, timeout=5000)  # timeout 5s
                await page.wait_for_selector('h2.text.line-clamp-2', timeout=5000)  # đợi selector hiển thị (JS render)
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

async def crawl_nab_jobs():
    """Crawl NAB jobs với parallel requests"""
    print("Crawling NAB jobs...")
    all_titles_nab = []
    url = "https://nab.wd3.myworkdayjobs.com/wday/cxs/nab/nab_careers/jobs"
    
    # Tạo payload cho các offset khác nhau
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

    message_nab = f"📢 <b><a href='https://nab.wd3.myworkdayjobs.com/nab_careers?locationCountry=db69e8c8446c11de98360015c5e6daf6&locations=25e34c7b3e6410009a643b05986b0000&locations=2b5ebaf8c9281000c02f3491eccc0000&jobFamilyGroup=28c588c0cf7a100144e1f2afbffe0000'>NAB</a> hôm nay ({today}):</b>\n" + '\n'.join(all_titles_nab)
    await send_telegram_message_async(BOT_TOKEN, CHAT_ID, message_nab)
    print(f"NAB: Found {len(all_titles_nab)} jobs")

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

async def crawl_shopee_jobs():
    """Crawl Shopee jobs với parallel requests"""
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
    
    message_tymex = f"📢 <b><a href='https://vietnam.tyme.com/#sec-career'>TymeX</a> hôm nay ({today}):</b>\n" + '\n'.join(all_titles_tymex)
    await send_telegram_message_async(BOT_TOKEN, CHAT_ID, message_tymex)
    print(f"TymeX: Found {len(all_titles_tymex)} jobs")

async def main():
    """Main function để chạy tất cả crawlers song song"""
    global session
    
    # Cấu hình session với connection pooling
    connector = aiohttp.TCPConnector(
        limit=100,  # Tổng số connection
        limit_per_host=20,  # Số connection per host
        keepalive_timeout=30,
        enable_cleanup_closed=True
    )
    
    timeout = aiohttp.ClientTimeout(total=30)
    session = aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    
    try:
        start_time = time.time()
        print("Starting job crawling...")
        
        # Chạy tất cả crawlers song song
        await asyncio.gather(
            # crawl_vng_jobs(),
            crawl_zalo_jobs(),
            # crawl_grab_jobs(),
            # crawl_nab_jobs(),
            # crawl_momo_jobs(),
            # crawl_shopee_jobs(),
            # crawl_tymex_jobs(),
            return_exceptions=True
        )
        
        end_time = time.time()
        print(f"Completed in {end_time - start_time:.2f} seconds")
        
    finally:
        await session.close()

if __name__ == "__main__":
    # Chạy async main function
    asyncio.run(main())