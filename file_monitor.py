import asyncio
import json
import time
import httpx
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Globals
PROCESSED_LISTING_IDS = set()
LISTINGS_FILE = "listings.json"
API_URL = "http://127.0.0.1:5050/make-call"

async def process_listings():
    """Reads the listings.json and triggers calls for new listings."""
    try:
        with open(LISTINGS_FILE, 'r', encoding='utf-8') as f:
            listings = json.load(f)

        tasks = []
        for listing in listings:
            listing_id = listing.get("listing_id")
            phone_number = listing.get("phone_number")

            if listing_id and phone_number and listing_id not in PROCESSED_LISTING_IDS:
                logger.info(f"New listing detected: {listing_id} | Calling {phone_number}")
                tasks.append(trigger_call(phone_number))
                PROCESSED_LISTING_IDS.add(listing_id)

        if tasks:
            await asyncio.gather(*tasks)

    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error reading {LISTINGS_FILE}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

async def trigger_call(phone_number: str):
    """Triggers the API call."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(API_URL, json={"to_phone_number": phone_number})
            response.raise_for_status()
            logger.info(f"Call triggered for {phone_number}: {response.json()}")
        except httpx.RequestError as e:
            logger.error(f"Request error for {phone_number}: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error for {phone_number}: {e.response.text}")

class ListingsFileHandler(FileSystemEventHandler):
    """Handles file modifications."""
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(LISTINGS_FILE):
            logger.info(f"{LISTINGS_FILE} modified. Checking for new listings...")
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(delayed_process())
            except RuntimeError:
                # No event loop in this thread, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(delayed_process())

async def delayed_process():
    await asyncio.sleep(0.5)  # Prevent race condition
    await process_listings()

def start_monitoring():
    """Starts monitoring listings.json."""
    logger.info("Initial scan of listings.json...")
    asyncio.run(process_listings())

    event_handler = ListingsFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path=".", recursive=False)
    observer.start()
    logger.info("Monitoring started...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
