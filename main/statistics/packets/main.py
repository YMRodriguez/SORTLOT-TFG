import pandas as pd
import json


def main(items, ID):
    """
    This function analyses a set of items.

    :param items: unprocessed items.
    :return: object with insights from the set of items.
    """
    items = pd.DataFrame(items)
    return {"ID": ID, "items": len(items),
            "unique": len(items[['width', "length", "height", "weight"]].drop_duplicates()),
            "max_dim": items.width.max(), "min_dim": items.width.min(),
            "max_w": items.weight.max(), "min_w": items.weight.min(), "max_v": items.volume.max(),
            "min_v": items.volume.min(), "n_dst": items.dst_code.unique().shape[0],
            "n_prio": items.priority.value_counts().sort_index().to_dict()[1],
            "n_br": items.breakability.value_counts().sort_index().to_dict()[1],
            }

ID=5
its = json.load(open('/Users/yamilmateorodriguez/Developtment/TFG/SORTLOT-TFG/main/scenarios/packetsDatasets/5-D80-30mx100x100x100-n180-dst1-ADR0-S0.json'))

with open("./holo", 'w') as f:
    json.dump(main(its, ID), f, indent=2, ensure_ascii=False)
