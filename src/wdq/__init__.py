from wdq.client import fetch_item, fetch_property
from wdq.models import WikidataItem, WikidataProperty


def item(qid: str) -> WikidataItem:
    data = fetch_item(qid)
    return WikidataItem(data)


def property(pid: str) -> WikidataProperty:
    data = fetch_property(pid)
    return WikidataProperty(data)
