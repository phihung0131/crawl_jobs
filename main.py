import requests
from bs4 import BeautifulSoup
from datetime import datetime

BOT_TOKEN = '8155238330:AAH2t2i3zk7v8yzGnP73bw0PiJTmpgI-Ovw' 
CHAT_ID = '5713801301'   

# Hash ngày thành chuỗi MD5
today = datetime.now().strftime('%d-%m-%Y')

# Hàm gửi tin nhắn Telegram với màu nền
def send_telegram_message(bot_token, chat_id, message):
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML',
    }
    requests.post(url, data=payload)

# Hàm crawl công việc VNG
def crawl_vng_jobs():
    all_titles_vng = []
    for page in range(1, 11):  # Crawl từ trang 1 đến 10
        url = f'https://career.vng.com.vn/tim-kiem-viec-lam?job_group=385%7C418&page={page}'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Tìm tất cả thẻ <a> có class="group relative go-to-detail"
        job_links = soup.find_all('a', class_='group relative go-to-detail')

        for tag in job_links:
            title = tag.get_text(strip=True)
            all_titles_vng.append(f'• {title}')

    # Lấy ngày hiện tại
    today = datetime.now().strftime('%d-%m-%Y')

    # Gộp danh sách thành 1 chuỗi cho VNG
    message_vng = f"📢 <b>Danh sách job VNG hôm nay ({today}):</b>\n" + '\n'.join(all_titles_vng)

    # Gửi thông báo về Telegram cho VNG
    send_telegram_message(BOT_TOKEN, CHAT_ID, message_vng)

# Hàm crawl công việc Zalo
def crawl_zalo_jobs():
    all_titles_zalo = []
    # for page in range(1, 11):  # Crawl từ trang 1 đến 10
    #     url = f'https://zalo.careers/job-list?teams=engineering&page={page}&locations=ho-chi-minh'
    #     response = requests.get(url)
    #     soup = BeautifulSoup(response.text, 'html.parser')

    #     # Tìm tất cả thẻ <h2> có class="text line-clamp-2"
    #     job_titles = soup.find_all('h2', class_='text line-clamp-2')

    #     for title in job_titles:
    #         all_titles_zalo.append(f'• {title.get_text(strip=True)}')

    # Gộp danh sách thành 1 chuỗi cho Zalo
    message_zalo = f"📢 <b>Danh sách job Zalo hôm nay ({today}):</b>\n" + 'https://zalo.careers/job-list?teams=engineering&page=1&locations=ho-chi-minh'

    # Gửi thông báo về Telegram cho Zalo
    send_telegram_message(BOT_TOKEN, CHAT_ID, message_zalo)

# Hàm crawl công việc Grab
def crawl_grab_jobs():
    all_titles_grab = []
    url = 'https://www.grab.careers/en/jobs/?search=&team=Engineering&team=Internship&team=Technology+Solutions&country=Vietnam&pagesize=100#results'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Tìm tất cả thẻ <a> có class="stretched-link js-view-job"
    job_links = soup.find_all('a', class_='stretched-link js-view-job')

    for tag in job_links:
        title = tag.get_text(strip=True)
        all_titles_grab.append(f'• {title}')

    # Gộp danh sách thành 1 chuỗi cho Grab
    message_grab = f"📢 <b>Danh sách job Grab hôm nay ({today}):</b>\n" + '\n'.join(all_titles_grab)

    # Gửi thông báo về Telegram cho Grab
    send_telegram_message(BOT_TOKEN, CHAT_ID, message_grab)

# Hàm crawl công việc từ NAB API
def crawl_nab_jobs():
    all_titles_nab = []
    offset = 0  # Bắt đầu với offset là 0
    while True:
        # Payload cho API POST với limit = 20 và offset thay đổi
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

        # Gửi POST request tới API của NAB
        url = "https://nab.wd3.myworkdayjobs.com/wday/cxs/nab/nab_careers/jobs"
        response = requests.post(url, json=payload)
        data = response.json()

        # Lấy danh sách công việc từ response JSON
        job_postings = data.get('jobPostings', [])

        # Nếu không còn công việc, dừng lại
        if offset >= 100:
            break

        # Lấy tiêu đề công việc
        for job in job_postings:
            title = job.get('title', 'No Title')
            all_titles_nab.append(f'• {title}')

        # Cập nhật offset để lấy 20 công việc tiếp theo
        offset += 20

    # Gộp danh sách thành 1 chuỗi cho NAB
    message_nab = f"📢 <b>Danh sách job NAB hôm nay ({today}):</b>\n" + '\n'.join(all_titles_nab)

    # Gửi thông báo về Telegram cho NAB
    send_telegram_message(BOT_TOKEN, CHAT_ID, message_nab)

# # Gọi hàm để chạy
# crawl_vng_jobs()
crawl_zalo_jobs()
# crawl_grab_jobs()
# crawl_nab_jobs()
