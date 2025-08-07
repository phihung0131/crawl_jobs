import asyncio
import time
from utils import session_manager

# Import crawlers
from crawlers.vng import crawl_vng_jobs
from crawlers.zalo import crawl_zalo_jobs
from crawlers.grab import crawl_grab_jobs
from crawlers.nab import crawl_nab_jobs
from crawlers.momo import crawl_momo_jobs
from crawlers.shopee import crawl_shopee_jobs
from crawlers.tymex import crawl_tymex_jobs
from crawlers.kms import crawl_kms_jobs
from crawlers.saigon_tech import crawl_saigon_tech_jobs

async def main():
    """Main function to run all crawlers in parallel"""
    try:
        start_time = time.time()
        print("Starting job crawling...")
        
        # Run all crawlers in parallel
        await asyncio.gather(
            crawl_vng_jobs(),
            crawl_zalo_jobs(),
            crawl_grab_jobs(),
            crawl_nab_jobs(),
            crawl_momo_jobs(),
            crawl_shopee_jobs(),
            crawl_tymex_jobs(),
            crawl_kms_jobs(),
            crawl_saigon_tech_jobs(),
            return_exceptions=True
        )
        
        end_time = time.time()
        print(f"Completed in {end_time - start_time:.2f} seconds")
        
    finally:
        await session_manager.close()

if __name__ == "__main__":
    # Run async main function
    asyncio.run(main())