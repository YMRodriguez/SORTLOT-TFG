import pandas as pd


def main(items):
    """
    This function analyses set of items.
    :param items: unprocessed items.
    :return: object with insights from the set of items.
    """
    items = pd.DataFrame(items)
    return {"describe": items.describe(),
            "unique": len(items[['width', "length", "height", "weight"]].drop_duplicates())}


