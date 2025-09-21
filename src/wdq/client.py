from typing import Any
import httpx

WIKIDATA_REST_API_URL = "https://www.wikidata.org/w/rest.php"
CLIENT = httpx.Client(
    headers={
        "User-Agent": "wdq (https://github.com/DinhHuy2010/wdq)"
    }
)

def fetch_item(qid: str) -> Any:
    url = f"{WIKIDATA_REST_API_URL}/wikibase/v1/entities/items/{qid}"
    response = CLIENT.get(url)
    response.raise_for_status()
    return response.json()

def fetch_property(pid: str) -> Any:
    url = f"{WIKIDATA_REST_API_URL}/wikibase/v1/entities/properties/{pid}"
    response = CLIENT.get(url)
    response.raise_for_status()
    return response.json()
