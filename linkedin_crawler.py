import requests
from bs4 import BeautifulSoup
import time
import random
import json
from datetime import datetime, timedelta
from html import escape
from urllib.parse import urlsplit, urlunsplit
import os

# =================================================================
# CẤU HÌNH BIẾN (DỄ DÀNG CHỈNH SỬA)
# =================================================================
BOT_TOKEN = '8155238330:AAH2t2i3zk7v8yzGnP73bw0PiJTmpgI-Ovw'
CHAT_ID = '5713801301'
TEAMS_WEBHOOK_URL = "https://fptsoftware362.webhook.office.com/webhookb2/26922374-936a-4890-b276-d4701bde91c1@f01e930a-b52e-42b1-b70f-a8882b5d043b/IncomingWebhook/31e6be510e8a4087989eff7b374fb25f/d72401ca-9be2-4344-96a7-ba1e3dac2b04/V2TDZIHACKWGODI7iLWtFvHFUHFL-pt28H0Eww2c_gQuo1"

LOG_FILE = "job_log.json"
MAX_LOG_DAYS = 3  # Xóa job trong log nếu cũ hơn n ngày
TIME_RANGE = "r172800"  # r172800 = 2 ngày (48 giờ)
KEYWORDS = "%22Java%22"
GEO_IDS = [103697962, 90010187, 102267004] # VN, HCM Metro, ...

COMPANY_LIST = [
    {"id": "31297705", "name": "Zalopay"},
    {"id": "22329726", "name": "NAB"},
    {"id": "2357", "name": "NAB"},
    {"id": "2489430", "name": "Axon Active"},
    {"id": "13688376", "name": "MoMo (M_Service)"},
    {"id": "89884185", "name": "Spartan"},
    {"id": "18339701", "name": "Zalo"},
    {"id": "1059735", "name": "VNG"},
    {"id": "18004637", "name": "DXC"},
    {"id": "157356", "name": "Thoughtworks"},
    {"id": "276383", "name": "WorldQuant"},
    {"id": "76831356", "name": "NAVER VIETNAM"},
    {"id": "13406864", "name": "CMC"},
    {"id": "72489539", "name": "HCLTech Vietnam"},
    {"id": "3804922", "name": "ShopBack"},
    {"id": "208401", "name": "FPT Software"},
    {"id": "231909", "name": "KMS Technology"},
    {"id": "9707", "name": "Endava"},
    {"id": "96646073", "name": "Ant"},
    {"id": "5382086", "name": "Grab"},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
TELEGRAM_MAX_LENGTH = 4096

# =================================================================
# CÁC HÀM XỬ LÝ LOG & DỮ LIỆU
# =================================================================

def clean_and_load_log():
    """Tải log và xóa các entry cũ hơn MAX_LOG_DAYS."""
    if not os.path.exists(LOG_FILE):
        return {}
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            log_data = json.load(f)
        
        # Logic dọn dẹp log
        now = datetime.now()
        threshold = now - timedelta(days=MAX_LOG_DAYS)
        
        new_log = {}
        removed_count = 0
        for link, info in log_data.items():
            sent_at = datetime.fromisoformat(info.get("sent_at"))
            if sent_at > threshold:
                new_log[link] = info
            else:
                removed_count += 1
        
        if removed_count > 0:
            print(f"🧹 Đã dọn dẹp {removed_count} job cũ khỏi log.")
            save_job_log(new_log)
            
        return new_log
    except Exception as e:
        print(f"⚠️ Lỗi load log: {e}")
        return {}

def save_job_log(log_data):
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)

def normalize_linkedin_url(url):
    if not url: return ""
    clean_url = url.strip().split('?')[0]
    parts = urlsplit(clean_url)
    netloc = "linkedin.com" if "linkedin.com" in parts.netloc else parts.netloc
    return urlunsplit((parts.scheme or "https", netloc, parts.path, "", ""))

# =================================================================
# CÁC HÀM GỬI THÔNG BÁO
# =================================================================

def send_telegram_message(message_html):
    payload = {"chat_id": CHAT_ID, "text": message_html, "parse_mode": "HTML", "disable_web_page_preview": True}
    try:
        requests.post(TELEGRAM_API_URL, data=payload, timeout=20)
    except:
        print("❌ Lỗi gửi Telegram")

def send_teams_message(message_text):
    payload = {"text": message_text}
    headers = {"Content-Type": "application/json"}
    try:
        requests.post(TEAMS_WEBHOOK_URL, data=json.dumps(payload), headers=headers, timeout=20)
    except:
        print("❌ Lỗi gửi Teams")

def build_report_message(all_results):
    scan_time = datetime.now().strftime("%H:%M")
    header = f"<b>🔔 PHÁT HIỆN JOB JAVA MỚI ({scan_time})</b>\n\n"
    body = []
    total = 0
    for company_name, jobs in all_results:
        if not jobs: continue
        body.append(f"<b>🏢 {escape(company_name.upper())}</b>")
        for index, job in enumerate(jobs, start=1):
            total += 1
            body.append(f"{index}. <b>[{escape(job['post_date'])}]</b> <a href=\"{escape(job['link'])}\">{escape(job['title'])}</a>")
        body.append("")
    
    if total == 0: return None
    footer = f"\n<b>🚀 Tổng số job mới:</b> {total}"
    return header + "\n".join(body) + footer

# =================================================================
# LOGIC CRAWLER
# =================================================================

def fetch_html(c_id, geo_id):
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?f_C={c_id}&keywords={KEYWORDS}&f_TPR={TIME_RANGE}&geoId={geo_id}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code == 200:
            return res.text
    except:
        pass
    return None

def crawl_linkedin_multi_company():
    job_log = clean_and_load_log()
    all_final_results = []
    
    print(f"🚀 Bắt đầu quét {len(COMPANY_LIST)} công ty...")

    for company in COMPANY_LIST:
        c_id, c_name = company["id"], company["name"]
        company_jobs = []
        found_in_geo = None

        # Chạy lần lượt từng geoId
        for geo_id in GEO_IDS:
            print(f" 🔍 Quét {c_name} | Vùng: {geo_id}...", end=" ")
            html = fetch_html(c_id, geo_id)

            time.sleep(random.randint(3, 6)) # Nghỉ từ 5-10 giây sau mỗi lần gọi URL

            if not html:
                print("Lỗi/Không data")
                continue
            
            soup = BeautifulSoup(html, "html.parser")
            job_items = soup.find_all("li")
            
            if job_items:
                print(f"Tìm thấy {len(job_items)} items.")
                # Xử lý lấy job
                for item in job_items:
                    title_tag = item.find("h3", class_="base-search-card__title")
                    link_tag = item.find("a", class_=["base-card__full-link", "base-search-card--link"])
                    
                    if title_tag and link_tag:
                        link = normalize_linkedin_url(link_tag.get("href"))
                        # Kiểm tra xem job này đã gửi chưa
                        if link and link not in job_log:
                            time_tag = item.find("time") or item.find("span", class_="job-search-card__listdate--new")
                            post_date = time_tag.text.strip() if time_tag else "Vừa đăng"
                            
                            company_jobs.append({
                                "title": title_tag.text.strip(),
                                "link": link,
                                "post_date": post_date
                            })
                
                # Nếu sau khi lọc qua log mà vẫn có job mới ở vùng này
                if company_jobs:
                    found_in_geo = geo_id
                    break # Dừng không quét các geoId sau cho công ty này
            else:
                print("Trống.")

        if company_jobs:
            all_final_results.append((c_name, company_jobs))

    # Xử lý báo cáo
    msg_html = build_report_message(all_final_results)
    if msg_html:
        # Gửi Telegram
        lines = msg_html.split("\n")
        current_chunk = []
        for line in lines:
            if len("\n".join(current_chunk + [line])) > TELEGRAM_MAX_LENGTH:
                send_telegram_message("\n".join(current_chunk))
                current_chunk = [line]
            else:
                current_chunk.append(line)
        if current_chunk:
            send_telegram_message("\n".join(current_chunk))
        
        # Gửi Teams
        teams_text = msg_html.replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", "")
        teams_text = teams_text.replace("<a href=\"", "").replace("\">", " - ").replace("</a>", "")
        # send_teams_message(teams_text)

        # Cập nhật log
        now_str = datetime.now().isoformat()
        for c_name, jobs in all_final_results:
            for job in jobs:
                job_log[job["link"]] = {
                    "title": job["title"],
                    "company": c_name,
                    "sent_at": now_str,
                    "post_date": job["post_date"]
                }
        save_job_log(job_log)
        print(f"✅ Đã gửi báo cáo và cập nhật log. Tổng job mới: {len(job_log)}")
    else:
        print("😴 Không có job nào mới so với log.")

if __name__ == "__main__":
    crawl_linkedin_multi_company()