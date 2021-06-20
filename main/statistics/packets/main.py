import pandas as pd
import glob
import os
import json


def getDatasetFromJSONWith(ID):
    """
    This function gets a dataset file by its id.

    :param ID: the id of the dataset, not the name.
    :return: list of items from the specified file.
    """
    filepath = glob.glob(os.path.dirname(__file__) + "/../../scenarios/packetsDatasets/" + str(ID) + "-*.json")[0]
    return json.load(open(filepath))


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
            "w_mean": round(items.weight.mean(), 2), "w_median": round(items.weight.median(), 2),
            "w_std": round(items.weight.std(), 2), "t_weight": round(items.weight.sum(), 2),
            "max_v": items.volume.max(), "min_v": items.volume.min(),
            "v_mean": round(items.volume.mean(), 2), "v_median": round(items.volume.median(), 2),
            "v_std": round(items.volume.std(), 2), "t_vol": round(items.volume.sum(), 2),
            "n_dst": items.dst_code.unique().shape[0],
            "n_prio": 0 if n_prio[0] == len(items) else n_prio[1],
            "n_br": 0 if n_break[0] == len(items) else n_break[1],
            }


def updateStatistics(ID):
    packets_dataset = getDatasetFromJSONWith(ID)
    if ID > 1:
        with open(os.path.dirname(__file__) + "/../../scenarios/packetsDatasets/description/stats.json", "r+") as f:
            data = json.load(f)
        with open(os.path.dirname(__file__) + "/../../scenarios/packetsDatasets/description/stats.json", "w+") as f:
            data.append(datasetStats(packets_dataset, ID))
            json.dump(data, f, indent=2, ensure_ascii=False)
    elif ID == 1:
        with open(os.path.dirname(__file__) + "/../../scenarios/packetsDatasets/description/stats.json", "r+") as f:
            data = json.load(f)
        with open(os.path.dirname(__file__) + "/../../scenarios/packetsDatasets/description/stats.json", "w+") as f:
            stats = [data, datasetStats(packets_dataset, ID)]
            json.dump(stats, f, indent=2, ensure_ascii=False)
    else:
        with open(os.path.dirname(__file__) + "/../../scenarios/packetsDatasets/description/stats.json", "w+") as f:
            json.dump(datasetStats(packets_dataset, ID), f, indent=2, ensure_ascii=False)


for i in range(30):
    updateStatistics(i)