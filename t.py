import wdq
import wdq.models


def test() -> None:
    cc = wdq.item("Q882")
    for s in cc.statements.all():
        if isinstance(s.value, wdq.models.WikidataValue):
            print(s.property.id, s.property.data_type)
            print(s.value.type)
            print(s.value.raw_content)


if __name__ == "__main__":
    test()
