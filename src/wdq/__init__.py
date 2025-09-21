from abc import ABC, abstractmethod
from typing import Any

import httpx

from wdq.models import (
    WikidataAliases,
    WikidataDescriptions,
    WikidataLabels,
    WikidataSitelinks,
    make_sitelinks,
)

WIKIDATA_REST_API_URL = "https://www.wikidata.org/w/rest.php"


def _fetch_item(qid):
    url = f"{WIKIDATA_REST_API_URL}/wikibase/v1/entities/items/{qid}"
    response = httpx.get(url)
    return response.json()


class WikidataEntity(ABC):
    @property
    @abstractmethod
    def id(self) -> str:
        """Get the unique identifier of this Wikidata entity."""
        raise NotImplementedError("This entity type does not implement id()")


class WikidataItem(WikidataEntity):
    def __init__(self, data: Any):
        self._wd_raw_data = data

    @property
    def id(self) -> str:
        return self._wd_raw_data["id"]

    @property
    def labels(self) -> WikidataLabels:
        return WikidataLabels(self._wd_raw_data.get("labels", {}), self.id)

    @property
    def descriptions(self) -> WikidataDescriptions:
        return WikidataDescriptions(self._wd_raw_data.get("descriptions", {}), self.id)

    @property
    def aliases(self) -> WikidataAliases:
        return WikidataAliases(self._wd_raw_data.get("aliases", {}), self.id)

    @property
    def sitelinks(self) -> WikidataSitelinks:
        return make_sitelinks(self._wd_raw_data.get("sitelinks", {}), self.id)


def item(qid: str) -> WikidataItem:
    data = _fetch_item(qid)
    return WikidataItem(data)
