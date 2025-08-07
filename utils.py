import aiohttp
from config import FILTER_KEYWORDS

class SessionManager:
    def __init__(self):
        self._session = None

    async def get_session(self):
        if self._session is None:
            connector = aiohttp.TCPConnector(
                limit=100,  # Total connections
                limit_per_host=20,  # Connections per host
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
        return self._session

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None

# Global session manager
session_manager = SessionManager()

def should_filter_job(job_title):
    """Check if job title contains any filter keywords"""
    job_lower = job_title.lower()
    return any(keyword.lower() in job_lower for keyword in FILTER_KEYWORDS)

async def send_telegram_message_async(bot_token, chat_id, message):
    """Send Telegram message asynchronously"""
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML',
    }
    
    session = await session_manager.get_session()
    async with session.post(url, data=payload) as response:
        return await response.json()

async def fetch_url_async(url, is_json=False):
    """Fetch URL asynchronously"""
    try:
        session = await session_manager.get_session()
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
            if is_json:
                return await response.json()
            return await response.text()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

async def post_url_async(url, data=None, json_data=None):
    """POST request asynchronously"""
    try:
        session = await session_manager.get_session()
        if json_data:
            async with session.post(url, json=json_data, timeout=aiohttp.ClientTimeout(total=10)) as response:
                return await response.json()
        elif data:
            async with session.post(url, data=data, timeout=aiohttp.ClientTimeout(total=10)) as response:
                return await response.json()
    except Exception as e:
        print(f"Error posting to {url}: {e}")
        return None 