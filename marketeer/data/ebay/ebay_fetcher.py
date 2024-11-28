import asyncio
import logging
import requests
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from itertools import chain
from prometheus_client import Gauge, Histogram

from observability.annotations import measure_exec_seconds
from settings import app_settings

logger = logging.getLogger(__name__)

item_labels = [
    "categoryId",
    "categoryName",
    "conditionDisplayName",
    "conditionId",
    "feedbackRatingStar",
    "itemId",
    "postalCode",
    "sellerUserName",
    "subtitle",
    "title",
    "topRatedListing",
    "topRatedSeller",
]
ebay_item_listing_age_days_gauge = Gauge("ebay_item_listing_age_days",
                                         "Number of days since an item listing was started", item_labels)
ebay_item_listing_age_days_histogram = Histogram("ebay_item_listing_age_days_histogram",
                                                 "Number of days since an item listing was started", item_labels,
                                                 buckets=[1, 3, 7, 14, 21, 30, 60, 90, 180])
ebay_item_listing_days_remaining_gauge = Gauge("ebay_item_listing_days_remaining",
                                               "Number of days remaining until an item listing ends", item_labels)
ebay_item_listing_days_remaining_histogram = Histogram("ebay_item_listing_days_remaining_histogram",
                                                       "Number of days remaining until an item listing ends", item_labels,
                                                       buckets=[1, 3, 7, 14, 21, 30, 60, 90, 180])
ebay_item_watch_count_gauge = Gauge("ebay_item_watch_count",
                                    "Number of people watching an item", item_labels)
ebay_item_watch_count_histogram = Histogram("ebay_item_watch_count_histogram",
                                            "Number of people watching an item", item_labels,
                                            buckets=[25, 50, 100, 200, 400, 800, 1600])


async def fetch():
    logger.info("Fetching items from Ebay")
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        tasks = [loop.run_in_executor(pool, do_ebay_keyword_search, blob)
                 for blob in app_settings.EBAY_MONITORED_KEYWORD_SEARCHES.keys()]
        results = list(chain.from_iterable(await asyncio.gather(*tasks)))


@measure_exec_seconds(use_logging=True, use_prometheus=True)
def do_ebay_keyword_search(blob: str):
    headers = {"X-EBAY-SOA-SECURITY-APPNAME": app_settings.EBAY_APP_ID}
    params = {**{
        "OPERATION-NAME": "findItemsByKeywords",
        "SERVICE-VERSION": "1.13.0",
        "RESPONSE-DATA-FORMAT": "JSON",
        "keywords": blob,
        "paginationInput.entriesPerPage": app_settings.EBAY_SEARCH_RESULTS_PER_PAGE,
    }, **app_settings.EBAY_MONITORED_KEYWORD_SEARCHES[blob]}
    response = requests.get(f"{app_settings.EBAY_API_ENDPOINT}/services/search/FindingService/v1",
                            headers=headers, params=params, timeout=30)
    response.raise_for_status()

    returned_items = []
    for item in response.json()["findItemsByKeywordsResponse"][0]["searchResult"][0]["item"]:
        watch_count = 0 if 'watchCount' not in item["listingInfo"][0] else int(item["listingInfo"][0]['watchCount'][0])
        if app_settings.EBAY_SEARCH_RESULTS_WATCHED_ITEM_ONLY and watch_count < 1:
            logger.debug(f"Filtered out item({item["itemId"][0]}) due to lack of watchers")
            continue

        listing_end_time_str = item["listingInfo"][0]["endTime"][0]
        listing_end_time = datetime.fromisoformat(listing_end_time_str.replace('Z', '+00:00'))
        listing_start_time_str = item["listingInfo"][0]["startTime"][0]
        listing_start_time = datetime.fromisoformat(listing_start_time_str.replace('Z', '+00:00'))
        current_time = datetime.now(timezone.utc)

        time_since_start_time = current_time - listing_start_time
        if time_since_start_time.days > app_settings.EBAY_SEARCH_RESULTS_MAX_AGE_DAYS:
            logger.debug(f"Filtered out item({item["itemId"][0]}) due to age({time_since_start_time.days}d)")
            continue

        label_map = {
            "categoryId": item["primaryCategory"][0]["categoryId"][0],
            "categoryName": item["primaryCategory"][0]["categoryName"][0],
            "conditionDisplayName": item["condition"][0]["conditionDisplayName"][0],
            "conditionId": item["condition"][0]["conditionId"][0],
            "feedbackRatingStar": item["sellerInfo"][0]["feedbackRatingStar"][0],
            "itemId": item["itemId"][0],
            "postalCode": "n/a" if "postalCode" not in item else item["postalCode"][0],
            "sellerUserName": item["sellerInfo"][0]["sellerUserName"][0],
            "subtitle": "n/a" if "subtitle" not in item else item["subtitle"][0],
            "title": item["title"][0],
            "topRatedListing": item["topRatedListing"][0],
            "topRatedSeller": item["sellerInfo"][0]["topRatedSeller"][0],
        }
        ebay_item_listing_age_days_gauge.labels(**label_map).set(time_since_start_time.days)
        ebay_item_listing_age_days_histogram.labels(**label_map).observe(time_since_start_time.days)

        time_until_end_time = listing_end_time - current_time
        ebay_item_listing_days_remaining_gauge.labels(**label_map).set(time_until_end_time.days)
        ebay_item_listing_days_remaining_histogram.labels(**label_map).observe(time_until_end_time.days)

        if 'watchCount' in item["listingInfo"][0]:
            watch_count = int(item["listingInfo"][0]['watchCount'][0])
            ebay_item_watch_count_gauge.labels(**label_map).set(watch_count)
            ebay_item_watch_count_histogram.labels(**label_map).observe(watch_count)
        returned_items.append(item)
    return returned_items


if __name__ == "__main__":
    from observability.logging import setup_logging
    setup_logging()

    for keywords_blob in app_settings.EBAY_MONITORED_KEYWORD_SEARCHES.keys():
        items = do_ebay_keyword_search(keywords_blob)
        logger.info(f"len(items) = {len(items)}")
