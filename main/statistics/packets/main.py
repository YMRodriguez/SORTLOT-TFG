import pandas as pd


def datasetStats(items, ID):
    """
    This function analyses a set of items.

    :param ID: ID of the dataset.
    :param items: unprocessed items.
    :return: object with insights from the set of items.
    """
    items = pd.DataFrame(items)
    n_prio = items.priority.value_counts().sort_index().to_dict()
    n_break = items.breakability.value_counts().sort_index().to_dict()
    return {"ID": ID,
            "items": len(items),
            "unique": len(items[['width', "length", "height", "weight"]].drop_duplicates()),
            "max_dim": items.width.max(), "min_dim": items.width.min(),
            "max_w": items.weight.max(), "min_w": items.weight.min(),
            "t_weight": items.weight.sum(),
            "max_v": items.volume.max(), "min_v": items.volume.min(),
            "t_vol": items.volume.sum(),
            "n_dst": items.dst_code.unique().shape[0],
            "n_prio": 0 if n_prio[0] == len(items) else n_prio[1],
            "n_br": 0 if n_break[0] == len(items) else n_break[1],
            }
