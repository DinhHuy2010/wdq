from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any
from wdq.languages.literals import WikidataLanguageCode
from wdq.sites import WikidataConnectedGroups, WikidataConnectedSite, identify_group


class _BaseWikidataLD(Mapping[WikidataLanguageCode, str]):
    _unit: str = "unknown"

    def __init__(self, raw: Any, entity_id: str):
        self._raw = raw
        self._entity_id = entity_id

    def __getitem__(self, key: WikidataLanguageCode) -> str:
        lang, label = self.default([key, "mul", "en"], raise_error=False)
        if lang is None:
            raise KeyError(key)
        return label

    def __iter__(self) -> Iterator[WikidataLanguageCode]:
        return iter(self._raw)

    def __len__(self) -> int:
        return len(self._raw)

    def __repr__(self) -> str:
        lang, label = self.default()
        header = f"Wikidata {self._entity_id}"
        return f"<{header}{f' ({label!r} ({lang}))'}: {len(self._raw)} {self._unit}(s) in {len(self._raw)} language(s)>"

    def default(
        self,
        fallback_chain: list[WikidataLanguageCode] | None = None,
        raise_error: bool = False,
    ) -> tuple[WikidataLanguageCode | None, str]:
        if fallback_chain is None:
            fallback_chain = ["mul", "en"]
        for lang in fallback_chain:
            try:
                return lang, self._raw[lang]
            except KeyError:
                continue
        if raise_error:
            raise KeyError(
                f"No {self._unit} found in fallback chain {fallback_chain!r}"
            )
        return None, self._entity_id


class WikidataLabels(_BaseWikidataLD):
    _unit = "label"


class WikidataDescriptions(_BaseWikidataLD):
    _unit = "description"


class WikidataAliases(Mapping[WikidataLanguageCode, set[str]]):
    def __init__(self, raw: Any, entity_id: str):
        self._raw = raw
        self._entity_id = entity_id

    def __getitem__(self, key: WikidataLanguageCode) -> set[str]:
        return self.default([key, "mul"])

    def __iter__(self) -> Iterator[WikidataLanguageCode]:
        return iter(self._raw)

    def naliases(self) -> int:
        return sum(len(aliases) for aliases in self._raw.values())

    def default(
        self, fallback_chain: list[WikidataLanguageCode] | None = None
    ) -> set[str]:
        if fallback_chain is None:
            fallback_chain = ["mul", "en"]
        union: set[str] = set()
        for lang in fallback_chain:
            union.update(self._raw.get(lang, set()))
        return union

    def all(self) -> set[str]:
        """Get all aliases in all languages."""
        union: set[str] = set()
        for aliases in self._raw.values():
            union.update(aliases)
        return union

    def __len__(self) -> int:
        return len(self._raw)

    def __repr__(self) -> str:
        muls = self.get("mul", set())
        header = f"Wikidata {self._entity_id}"
        return f"<{header} ({' | '.join(muls)}): {self.naliases()} alias(es) in {len(self._raw)} language(s)>"


class WikidataSitelinkBadge(Enum):
    """Badge for a Wikidata sitelink."""

    GOOD_ARTICLE = "Q17437798"
    FEATURED_ARTICLE_BADGE = "Q17437796"
    RECOMMENDED_ARTICLE = "Q17559452"
    FEATURED_LIST = "Q17506997"
    FEATURED_PORTAL = "Q17580674"
    NOT_PROOFREAD = "Q20748091"
    PROBLEMATIC = "Q20748094"
    PROOFREAD = "Q20748092"
    VALIDATED = "Q20748093"
    DIGITAL_DOCUMENT = "Q28064618"
    GOOD_LIST = "Q51759403"
    SITELINK_TO_REDIRECT = "Q70893996"
    INTENTIONAL_SITELINK_TO_REDIRECT = "Q70894304"


@dataclass
class WikidataSitelink:
    title: str
    badges: list[WikidataSitelinkBadge]
    url: str

    @classmethod
    def from_raw(cls, raw: Any) -> "WikidataSitelink":
        title = raw["title"]
        badges = [WikidataSitelinkBadge(badge_id) for badge_id in raw.get("badges", [])]
        url = raw["url"]
        return cls(title=title, badges=badges, url=url)


class WikidataSitelinks(Mapping[WikidataConnectedSite, WikidataSitelink]):
    def __init__(self, raw: Any, item: str):
        self._raw = raw
        self._item = item

    def __getitem__(self, key: WikidataConnectedSite) -> WikidataSitelink:
        return self._raw[key]

    def __iter__(self) -> Iterator[WikidataConnectedSite]:
        return iter(self._raw)

    def __len__(self) -> int:
        return len(self._raw)

    def __repr__(self) -> str:
        return f"<WikidataSitelinks: {len(self._raw)} sitelink(s) from {self._item}>"

    def by_group(
        self, group: WikidataConnectedGroups
    ) -> dict[WikidataConnectedSite, WikidataSitelink]:
        """Get sitelinks by group."""
        return {
            site: link
            for site, link in self._raw.items()
            if identify_group(site) == group
        }


def make_sitelinks(raw: Any, item: str) -> WikidataSitelinks:
    sitelinks = {site: WikidataSitelink.from_raw(data) for site, data in raw.items()}
    return WikidataSitelinks(sitelinks, item)
