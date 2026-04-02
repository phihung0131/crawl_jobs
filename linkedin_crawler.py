import requests
from bs4 import BeautifulSoup
import time
import random
import json
from datetime import datetime
from html import escape
from urllib.parse import urlsplit, urlunsplit
import os

BOT_TOKEN = '8155238330:AAH2t2i3zk7v8yzGnP73bw0PiJTmpgI-Ovw'
CHAT_ID = '5713801301'
TEAMS_WEBHOOK_URL = "https://fptsoftware362.webhook.office.com/webhookb2/26922374-936a-4890-b276-d4701bde91c1@f01e930a-b52e-42b1-b70f-a8882b5d043b/IncomingWebhook/31e6be510e8a4087989eff7b374fb25f/d72401ca-9be2-4344-96a7-ba1e3dac2b04/V2TDZIHACKWGODI7iLWtFvHFUHFL-pt28H0Eww2c_gQuo1"
LOG_FILE = "job_log.json"

# --- CẤU HÌNH MẢNG ID CÔNG TY ---
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
]

# --- THÔNG SỐ CRAWL ---
TIME_RANGE = "r1209600"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
TELEGRAM_MAX_LENGTH = 4096


def load_job_log():
    if not os.path.exists(LOG_FILE):
        return {}

    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_job_log(log_data):
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)


def is_job_sent(job_link, log_data):
    return job_link in log_data


def mark_job_as_sent(job_link, job_info, log_data):
    log_data[job_link] = {
        "title": job_info["title"],
        "company": job_info.get("company", ""),
        "sent_at": datetime.now().isoformat(),
        "post_date": job_info["post_date"],
    }


def filter_new_jobs(all_jobs, log_data):
    filtered_jobs = []

    for company_name, jobs in all_jobs:
        new_jobs = [
            job for job in jobs
            if not is_job_sent(job["link"], log_data)
        ]
        if new_jobs:
            filtered_jobs.append((company_name, new_jobs))

    return filtered_jobs


def normalize_linkedin_url(url):
    if not url:
        return ""

    clean_url = url.strip()
    parts = urlsplit(clean_url)
    netloc = parts.netloc

    if netloc.endswith(".linkedin.com") and netloc != "linkedin.com":
        netloc = "linkedin.com"

    return urlunsplit((parts.scheme or "https", netloc, parts.path, "", ""))


def send_telegram_message(message_html):
    payload = {
        "chat_id": CHAT_ID,
        "text": message_html,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    response = requests.post(TELEGRAM_API_URL, data=payload, timeout=20)

    if response.status_code != 200:
        raise RuntimeError(f"Telegram API error {response.status_code}: {response.text}")


def send_teams_message(message_text):
    payload = {"text": message_text}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(
            TEAMS_WEBHOOK_URL,
            data=json.dumps(payload),
            headers=headers,
            timeout=20,
        )

        if response.status_code != 200:
            raise RuntimeError(f"Teams API error {response.status_code}: {response.text}")

    except Exception as e:
        raise RuntimeError(f"Error sending Teams message: {e}")


def strip_html_tags(html_text):
    text = html_text
    text = text.replace("<b>", "").replace("</b>", "")
    text = text.replace("<i>", "").replace("</i>", "")
    text = text.replace("<a href=\"", "").replace("\">", " - ").replace("</a>", "")
    return text


def split_message_for_telegram(message_html):
    lines = message_html.split("\n")
    chunks = []
    current = []

    for line in lines:
        candidate = "\n".join(current + [line]).strip()

        if len(candidate) <= TELEGRAM_MAX_LENGTH:
            current.append(line)
            continue

        if current:
            chunks.append("\n".join(current).strip())
            current = [line]
        else:
            chunks.append(line[:TELEGRAM_MAX_LENGTH])
            current = []

    if current:
        chunks.append("\n".join(current).strip())

    return [chunk for chunk in chunks if chunk]


def build_report_message(all_jobs, scan_time):
    header_lines = [
        "<b>📌 BÁO CÁO JOB JAVA - 2 TUẦN GẦN ĐÂY</b>",
        f"<i>🕒 Thời gian quét: {scan_time}</i>",
        "",
    ]

    body_lines = []
    no_job_companies = []
    total_jobs = 0

    def build_message(candidate_body, current_total_jobs, extra_footer=None):
        footer_lines = ["", f"<b>✅ Tổng số job:</b> {current_total_jobs}"]
        if extra_footer:
            footer_lines.append(extra_footer)
        return "\n".join(header_lines + candidate_body + footer_lines).strip()

    for company_name, jobs in all_jobs:
        if not jobs:
            no_job_companies.append(company_name)
            continue

        company_heading = f"<b>🟢 {escape(company_name.upper())}</b>"
        body_lines.append(company_heading)

        for index, job in enumerate(jobs, start=1):
            total_jobs += 1
            line = (
                f"{index}. <b>[{escape(job['post_date'])}]</b> "
                f"<a href=\"{escape(job['link'])}\">{escape(job['title'])}</a>"
            )
            body_lines.append(line)

        body_lines.append("")

    if no_job_companies:
        no_job_text = ", ".join(escape(name) for name in no_job_companies)
        body_lines.extend([
            "<b>📭 Các công ty không có job phù hợp:</b>",
            no_job_text,
            "",
        ])

    if total_jobs == 0:
        body_lines.append("Không có job mới.")

    return build_message(body_lines, total_jobs)


def crawl_linkedin_multi_company():
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8",
    }

    job_log = load_job_log()
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

                company_jobs.append({
                    "title": title,
                    "link": link,
                    "post_date": post_date,
                    "company": c_name,
                })

            print(f" Da tim thay {len(company_jobs)} job phu hop.")
            all_jobs.append((c_name, company_jobs))

        except Exception as e:
            print(f" Loi khi xu ly {c_name}: {e}")
            all_jobs.append((c_name, company_jobs))

        time.sleep(random.randint(3, 7))

    new_jobs = filter_new_jobs(all_jobs, job_log)

    scan_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    message_html = build_report_message(new_jobs, scan_time)
    messages = split_message_for_telegram(message_html)

    for idx, msg in enumerate(messages, start=1):
        if len(messages) > 1:
            part_prefix = f"<b>(Phần {idx}/{len(messages)})</b>\n"
            if len(part_prefix) + len(msg) <= TELEGRAM_MAX_LENGTH:
                send_telegram_message(part_prefix + msg)
            else:
                send_telegram_message(msg)
        else:
            send_telegram_message(msg)

    print(f"\nHoàn tất! Đã gửi {len(messages)} tin nhắn qua Telegram.")

    if TEAMS_WEBHOOK_URL:
        teams_message = strip_html_tags(message_html)
        send_teams_message(teams_message)
        print("Đã gửi báo cáo qua Teams webhook.")

    if new_jobs and any(jobs for _, jobs in new_jobs):
        for company_name, jobs in new_jobs:
            for job in jobs:
                mark_job_as_sent(job["link"], job, job_log)

        save_job_log(job_log)
        print(f"Đã update log file. Tổng số job đã gửi: {len(job_log)}")
    else:
        print(f"\n✓ Không có job mới. Log file hiện có {len(job_log)} job.")


if __name__ == "__main__":
    crawl_linkedin_multi_company()