import requests
from bs4 import BeautifulSoup
import time
import random
from datetime import datetime
from html import escape
from urllib.parse import urlsplit, urlunsplit

from config import BOT_TOKEN, CHAT_ID

# --- CẤU HÌNH MẢNG ID CÔNG TY ---
# Bạn chỉ cần thêm ID các công ty muốn theo dõi vào mảng này
COMPANY_LIST = [
    {"id": "31297705", "name": "Zalopay"},
    {"id": "22329726", "name": "NAB"},
    # {"id": "2357", "name": "NAB"},
    # {"id": "2489430", "name": "Axon Active"},
    # {"id": "13688376", "name": "MoMo (M_Service)"},
    # {"id": "89884185", "name": "Spartan"},
    # {"id": "18339701", "name": "Zalo"},
    # {"id": "1059735", "name": "VNG"},
    # {"id": "18004637", "name": "DXC"},
    # {"id": "157356", "name": "Thoughtworks"},
    # {"id": "276383", "name": "WorldQuant"},
    # {"id": "76831356", "name": "NAVER VIETNAM"},
    # {"id": "13406864", "name": "CMC"},
    # {"id": "72489539", "name": "HCLTech Vietnam"},
    # {"id": "3804922", "name": "ShopBack"},
    # {"id": "208401", "name": "FPT Software"},
    # {"id": "231909", "name": "KMS Technology"},
    # {"id": "9707", "name": "Endava"},
    # {"id": "96646073", "name": "Ant"},
]

# --- THÔNG SỐ CRAWL ---
# r1209600 tương đương 1.209.600 giây = 14 ngày (2 tuần)
TIME_RANGE = "r1209600"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


def normalize_linkedin_url(url):
    """Normalize linkedin domains from *.linkedin.com to linkedin.com and drop query params."""
    if not url:
        return ""

    clean_url = url.strip()
    parts = urlsplit(clean_url)
    netloc = parts.netloc

    if netloc.endswith(".linkedin.com") and netloc != "linkedin.com":
        netloc = "linkedin.com"

    # Keep only scheme/netloc/path so output link is clean and stable.
    return urlunsplit((parts.scheme or "https", netloc, parts.path, "", ""))


def send_telegram_message(message_html):
    payload = {
        "chat_id": CHAT_ID,
        "text": message_html,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    response = requests.post(TELEGRAM_API_URL, data=payload, timeout=20)
    response.raise_for_status()


def build_report_message(all_jobs, scan_time):
    header = [
        "<b>📌 BÁO CÁO JOB JAVA - 2 TUẦN GẦN ĐÂY</b>",
        f"<i>🕒 Thời gian quét: {scan_time}</i>",
        "",
    ]

    body = []
    no_job_companies = []
    total_jobs = 0
    for company_name, jobs in all_jobs:
        if not jobs:
            no_job_companies.append(company_name)
            continue

        body.append(f"<b>🟢 {escape(company_name.upper())}</b>")
        for index, job in enumerate(jobs, start=1):
            total_jobs += 1
            line = (
                f"{index}. <b>[{escape(job['post_date'])}]</b> "
                f"<a href=\"{escape(job['link'])}\">{escape(job['title'])}</a>"
            )
            body.append(line)
        body.append("")

    if no_job_companies:
        no_job_text = ", ".join(escape(name) for name in no_job_companies)
        body.append("<b>📭 Các công ty không có job phù hợp:</b>")
        body.append(no_job_text)
        body.append("")

    if total_jobs == 0:
        body.append("Không tìm thấy job phù hợp trong khoảng thời gian đã chọn.")

    footer = [f"<b>✅ Tổng số job:</b> {total_jobs}"]
    return "\n".join(header + body + footer).strip()

def crawl_linkedin_multi_company():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    all_jobs = []

    for company in COMPANY_LIST:
        c_id = company["id"]
        c_name = company["name"]

        print(f"Dang quet {c_name} (ID: {c_id})...")

        url = (
            "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
            f"?f_C={c_id}&keywords=%22Java%22&f_TPR={TIME_RANGE}&geoId=103697962"
        )

        company_jobs = []
        try:
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code != 200:
                print(f" Loi truy cap {c_name}: {res.status_code}")
                all_jobs.append((c_name, company_jobs))
                continue

            soup = BeautifulSoup(res.text, "html.parser")
            job_items = soup.find_all("li")

            if not job_items:
                print(f" Khong tim thay job nao cho {c_name}.")
                all_jobs.append((c_name, company_jobs))
                continue

            for item in job_items:
                title_tag = item.find("h3", class_="base-search-card__title")
                if not title_tag:
                    continue
                title = title_tag.text.strip()

                link_tag = item.find("a", class_="base-card__full-link")
                raw_link = link_tag["href"] if link_tag and link_tag.get("href") else ""
                link = normalize_linkedin_url(raw_link)
                if not link:
                    continue

                time_tag = item.find("time", class_="job-search-card__listdate")
                if not time_tag:
                    time_tag = item.find("span", class_="job-search-card__listdate--new")
                post_date = time_tag.text.strip() if time_tag else "Vua dang"

                company_jobs.append(
                    {
                        "title": title,
                        "link": link,
                        "post_date": post_date,
                    }
                )

            print(f" Da tim thay {len(company_jobs)} job phu hop.")
            all_jobs.append((c_name, company_jobs))

        except Exception as e:
            print(f" Loi khi xu ly {c_name}: {e}")
            all_jobs.append((c_name, company_jobs))

        # Nghỉ ngẫu nhiên để tránh bị block IP
        time.sleep(random.randint(3, 7))

    scan_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    message_html = build_report_message(all_jobs, scan_time)

    # Telegram allows up to 4096 chars per message.
    if len(message_html) > 4096:
        message_html = f"{message_html[:3950]}\n\n... (noi dung bi cat do vuot gioi han 1 tin nhan)"

    send_telegram_message(message_html)
    print("\nHoan tat! Da gui ket qua qua Telegram.")

if __name__ == "__main__":
    crawl_linkedin_multi_company()