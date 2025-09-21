from abc import ABC
from builtins import property as pyproperty
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


class WikidataStatementRank(Enum):
    """Rank of a Wikidata statement."""

    PREFERRED = "preferred"
    NORMAL = "normal"
    DEPRECATED = "deprecated"


@dataclass
class WikidataPropertyReference:
    id: str
    data_type: str

    def resolve(self) -> "WikidataProperty":
        from wdq import property as fetch_property

        return fetch_property(self.id)


class BaseWikidataStatement(ABC):
    @pyproperty
    def property(self) -> WikidataPropertyReference:
        raise NotImplementedError("This entity type does not implement property()")

    @pyproperty
    def value(self) -> Any:
        raise NotImplementedError("This entity type does not implement value()")


class WikidataQualifier(BaseWikidataStatement):
    def __init__(self, data: Any):
        self._raw = data

    @pyproperty
    def property(self) -> WikidataPropertyReference:
        prop = self._raw["property"]
        return WikidataPropertyReference(id=prop["id"], data_type=prop["data_type"])

    @pyproperty
    def value(self) -> "BaseWikidataValue":
        return _resolve_wikidata_value(self.property, self._raw["value"])


class WikidataReferencePart(BaseWikidataStatement):
    def __init__(self, data: Any):
        self._raw = data

    @pyproperty
    def property(self) -> WikidataPropertyReference:
        prop = self._raw["property"]
        return WikidataPropertyReference(id=prop["id"], data_type=prop["data_type"])

    @pyproperty
    def value(self) -> "BaseWikidataValue":
        return _resolve_wikidata_value(self.property, self._raw["value"])


class WikidataReference:
    def __init__(self, data: Any):
        self._raw = data

    @property
    def hash(self) -> str:
        return self._raw["hash"]

    @property
    def parts(self) -> list[WikidataReferencePart]:
        return [WikidataReferencePart(data) for data in self._raw.get("parts", [])]


class BaseWikidataValue:
    def __init__(self, data, type="unknown"):
        self._raw = data
        self._type = type

    @property
    def type(self) -> str:
        return self._type

    @property
    def raw_content(self) -> Any:
        return self._raw["content"]


class WikidataValue(BaseWikidataValue): ...


class WikidataSomeValue(BaseWikidataValue): ...


class WikidataNoValue(BaseWikidataValue): ...


class WikidataItemValue(BaseWikidataValue):
    @property
    def id(self) -> str:
        return self._raw["content"]

    def resolve(self) -> "WikidataItem":
        from wdq import item as fetch_item

        return fetch_item(self.id)


class WikidataExternalIdentifierValue(BaseWikidataValue):
    def __init__(self, data, prop, type="unknown"):
        super().__init__(data, type)
        self._prop = prop

    @property
    def id(self) -> str:
        return self._raw["content"]

    @property
    def property(self) -> WikidataPropertyReference:
        return self._prop


def _resolve_wikidata_value(
    prop: WikidataPropertyReference, value: Any
) -> BaseWikidataValue:
    if value["type"] == "somevalue":
        return WikidataSomeValue(value, "somevalue")
    elif value["type"] == "novalue":
        return WikidataNoValue(value, "novalue")

    if prop.data_type == "wikibase-item":
        return WikidataItemValue(value, "wikibase-item")
    if prop.data_type == "external-id":
        return WikidataExternalIdentifierValue(value, prop, "external-id")
    return WikidataValue(value, prop.data_type)


class WikidataStatement(BaseWikidataStatement):
    def __init__(self, data: Any):
        self._raw = data

    @pyproperty
    def id(self) -> str:
        return self._raw["id"]

    @pyproperty
    def rank(self) -> WikidataStatementRank:
        return WikidataStatementRank(self._raw.get("rank", "normal"))

    @pyproperty
    def property(self) -> WikidataPropertyReference:
        prop = self._raw["property"]
        return WikidataPropertyReference(id=prop["id"], data_type=prop["data_type"])

    @pyproperty
    def value(self) -> BaseWikidataValue:
        return _resolve_wikidata_value(self.property, self._raw["value"])

    @pyproperty
    def qualifiers(self) -> list[WikidataQualifier]:
        return [WikidataQualifier(data) for data in self._raw.get("qualifiers", [])]

    @pyproperty
    def references(self) -> list[WikidataReference]:
        return [WikidataReference(data) for data in self._raw.get("references", [])]


class WikidataStatements:
    def __init__(self, data: Any, qid: str):
        self._raw = data
        self._qid = qid

    def _filter_by_rank(
        self,
        statements: list[WikidataStatement],
        ranks: list[WikidataStatementRank] | None,
    ) -> list[WikidataStatement]:
        return [s for s in statements if ranks is None or s.rank in ranks]

    def property(
        self, property_id: str, *, ranks: list[WikidataStatementRank] | None = None
    ) -> list[WikidataStatement]:
        statements = self._raw.get(property_id, [])
        statements = [WikidataStatement(statement) for statement in statements]
        return self._filter_by_rank(statements, ranks)

    def all(
        self, *, ranks: list[WikidataStatementRank] | None = None
    ) -> list[WikidataStatement]:
        statements = [
            WikidataStatement(statement) for s in self._raw.values() for statement in s
        ]
        return self._filter_by_rank(statements, ranks)

    def __len__(self) -> int:
        return sum(len(s) for s in self._raw.values())

    def __repr__(self):
        total_statements = len(self)
        unique_properties = len(self._raw)
        return f"<Wikidata {self._qid}: {total_statements} statement(s) across {unique_properties} unique property(ies)>"


class WikidataEntity:
    def __init__(self, data: Any):
        self._raw = data

    @property
    def id(self) -> str:
        return self._raw["id"]

    @property
    def labels(self) -> WikidataLabels:
        return WikidataLabels(self._raw.get("labels", {}), self.id)

    @property
    def descriptions(self) -> WikidataDescriptions:
        return WikidataDescriptions(self._raw.get("descriptions", {}), self.id)

    @property
    def aliases(self) -> WikidataAliases:
        return WikidataAliases(self._raw.get("aliases", {}), self.id)

    @property
    def statements(self) -> WikidataStatements:
        return WikidataStatements(self._raw.get("statements", {}), self.id)


class WikidataItem(WikidataEntity):
    @property
    def sitelinks(self) -> WikidataSitelinks:
        return make_sitelinks(self._raw.get("sitelinks", {}), self.id)


class WikidataProperty(WikidataEntity):
    @property
    def type(self) -> str:
        return self._raw["data_type"]
