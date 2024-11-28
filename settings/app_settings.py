import os

# EBay

EBAY_API_ENDPOINT = "https://svcs.ebay.com"
EBAY_APP_ID = os.getenv("EBAY_APP_ID", "oops")
# TODO: Generate programmatically
EBAY_DEFAULT_KEYWORD_FILTER_CRITERIA = {
    'sortOrder': 'BestMatch',
    'outputSelector(0)': 'SellerInfo',  # Include seller information in the results
    'itemFilter(0).name': 'FreeShippingOnly',
    'itemFilter(0).value': 'true',  # Free shipping only
    'itemFilter(1).name': 'ListingType',
    'itemFilter(1).value(0)': 'FixedPrice',  # "Buy It Now" listings
    'itemFilter(2).name': 'ReturnsAcceptedOnly',
    'itemFilter(2).value': 'true',  # Items that accept returns
    'itemFilter(3).name': 'LocatedIn',
    'itemFilter(3).value': 'US',  # Items located in the US
    'itemFilter(4).name': 'MinPrice',
    'itemFilter(4).value': '400',
}
EBAY_SEARCH_RESULTS_MAX_AGE_DAYS = 14
EBAY_SEARCH_RESULTS_PER_PAGE = 100
EBAY_SEARCH_RESULTS_WATCHED_ITEM_ONLY = True
EBAY_MONITORED_KEYWORD_SEARCHES = {
    "Apple Macbook Pro": {**EBAY_DEFAULT_KEYWORD_FILTER_CRITERIA, **{
        'itemFilter(4).name': 'MinPrice',
        'itemFilter(4).value': '700',
    }},
    "Apple iPhone": {**EBAY_DEFAULT_KEYWORD_FILTER_CRITERIA, },
    "designer handbags": {**EBAY_DEFAULT_KEYWORD_FILTER_CRITERIA, },
}

# Observability

LOG_LEVEL = os.getenv("APP_LOG_LEVEL", "INFO")

# PostgreSQL

DB_HOST = os.getenv("DB_HOST", "oops")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "oops")
POSTGRES_USER = os.getenv("POSTGRES_USER", "oops")
