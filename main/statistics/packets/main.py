import pandas as pd
import json


def main(items):
    """
    This function analyses a set of items.

    :param items: unprocessed items.
    :return: object with insights from the set of items.
    """
    items = pd.DataFrame(items)
    return {"min_w": items.weight.min(), "max_w": items.weight.max(), "min_v": items.volume.min(),
            "max_v": items.volume.max(), "n_by_dst": items.dst_code.value_counts().sort_index().to_dict(),
            "n_by_prio": items.priority.value_counts().sort_index().to_dict(),
            "n_by_br": items.breakability.value_counts().sort_index().to_dict(),
            "unique": len(items[['width', "length", "height", "weight"]].drop_duplicates())}


its = json.load(open('/Users/yamilmateorodriguez/Developtment/TFG/SORTLOT-TFG/main/scenarios/packetsDatasets/7-D30-30mx100x100x100-n200-dst5-ADR0-S0.json'))
a = main(its)
