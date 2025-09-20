from collections.abc import Iterator, Mapping
from typing import Any
from wdq.languages.literals import WikidataLanguageCode


class _BaseWikidataLD(Mapping[WikidataLanguageCode, str]):
    _unit: str = "unknown"

    def __init__(self, raw: Any, entity_id: str):
        self._raw = raw
        self._entity_id = entity_id

    def __getitem__(self, key: WikidataLanguageCode) -> str:
        try:
            return self._raw[key]
        except KeyError as err:
            try:
                # Try to fall back to the "mul" (multiple languages) label if available
                return self._raw["mul"]
            except KeyError:
                raise err from None

    def __iter__(self) -> Iterator[WikidataLanguageCode]:
        return iter(self._raw)

    def __len__(self) -> int:
        return len(self._raw)

    def __repr__(self) -> str:
        mul = self.default()
        header = f"Wikidata {self._entity_id}"
        return f"<{header}{f' ({mul!r})'}: {len(self._raw)} {self._unit}(s) in {len(self._raw)} language(s)>"

    def default(self, fallback_chain: list[WikidataLanguageCode] | None = None) -> str:
        if fallback_chain is None:
            fallback_chain = ["mul", "en"]
        for lang in fallback_chain:
            try:
                return self._raw[lang]
            except KeyError:
                continue
        return self._entity_id


class WikidataLabels(_BaseWikidataLD):
    _unit = "label"


class WikidataDescriptions(_BaseWikidataLD):
    _unit = "description"


class WikidataAliases(Mapping[WikidataLanguageCode, set[str]]):
    def __init__(self, raw: Any, entity_id: str):
        self._raw = raw
        self._entity_id = entity_id

    def __getitem__(self, key: WikidataLanguageCode) -> set[str]:
        try:
            return set(self._raw[key])
        except KeyError as err:
            try:
                # Try to fall back to the "mul" (multiple languages) aliases if available
                return set(self._raw["mul"])
            except KeyError:
                raise err from None

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
