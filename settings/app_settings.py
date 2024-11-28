import os
import yaml


def hydrate_ebay_item_search_filters(compact_filters: dict) -> dict:
    hydrated_filters = {}
    for filter_idx, filter_pair in enumerate(compact_filters.items()):
        hydrated_filters[f"itemFilter({filter_idx}).name"] = filter_pair[0]
        if isinstance(filter_pair[1], list):
            for value_idx, value_idx_value in enumerate(filter_pair[1]):
                hydrated_filters[f"itemFilter({filter_idx}).value({value_idx})"] = value_idx_value
        else:
            hydrated_filters[f"itemFilter({filter_idx}).value"] = filter_pair[1]
    return hydrated_filters


# EBay

ebay_yaml_fd = open("/src/ebay.yaml")
ebay_yaml = yaml.safe_load(ebay_yaml_fd)
ebay_yaml_fd.close()

ebay_yaml_items = ebay_yaml.get("items", {})
ebay_yaml_items_filters = ebay_yaml_items.get("filters", {})
ebay_yaml_items_searches = ebay_yaml_items.get("searches", {})

EBAY_API_ENDPOINT = os.getenv("EBAY_API_ENDPOINT", "https://svcs.ebay.com")
EBAY_APP_ID = os.getenv("EBAY_APP_ID", "oops")

EBAY_DEFAULT_KEYWORD_FILTER_CRITERIA = {
    'sortOrder': ebay_yaml_items.get("sortOrder", "BestMatch"),
    **{f"outputSelector({idx})": selector for idx, selector in enumerate(
        ebay_yaml_items.get("outputSelector", ["SellerInfo"]))},
}
EBAY_MONITORED_KEYWORD_SEARCHES = {
    keywords_blob: {
        **EBAY_DEFAULT_KEYWORD_FILTER_CRITERIA,
        **hydrate_ebay_item_search_filters({**ebay_yaml_items_filters, **override_filters})
    } for keywords_blob, override_filters in ebay_yaml_items_searches.items()}

EBAY_SEARCH_RESULTS_MAX_AGE_DAYS = ebay_yaml_items.get("max_age_days", 14)
EBAY_SEARCH_RESULTS_PER_PAGE = ebay_yaml_items.get("results_per_page", 100)
EBAY_SEARCH_RESULTS_WATCHED_ITEM_ONLY = ebay_yaml_items.get("watched_items_only", True)

# Observability

LOG_LEVEL = os.getenv("APP_LOG_LEVEL", "INFO")

# PostgreSQL

DB_HOST = os.getenv("DB_HOST", "oops")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "oops")
POSTGRES_USER = os.getenv("POSTGRES_USER", "oops")
