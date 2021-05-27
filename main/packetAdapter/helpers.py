import random
from copy import deepcopy
import numpy as np

# This function return the average weight for a list of items.
def getAverageWeight(items):
    return sum(list(map(lambda x: x["weight"], items))) / len(items)


# This function return the average weight for a list of items.
def getAverageVolume(items):
    return sum(list(map(lambda x: x["volume"], items))) / len(items)


# This function return the average priority for a list of items.
def getAveragePriority(items):
    return sum(list(map(lambda x: x["priority"], items))) / len(items)


# This function calculates the average taxability from a group of items
def getAverageTaxability(items):
    return sum(list(map(lambda x: x["taxability"] if "taxability" in x else 0, items))) / len(items)


# This function returns max taxability value in a list of items.
def getMaxTaxability(items):
    return max(item["taxability"] for item in items)


# This function returns max priority value in a list of items.
def getMaxPriority(items):
    return max(item["priority"] for item in items)


# This function returns max volume value in a list of items.
def getMaxVolume(items):
    return max(item["volume"] for item in items)


# This function returns max weight value in a list of items.
def getMaxWeight(items):
    return max(item["weight"] for item in items)


# This function randomly chooses a feasible orientation with equal probability
# Orientation equivalences (x, y, z) ---> |o1 -> (w, h, l) |
#                                        |o2 -> (l, h, w) |
#                                        |o3 -> (w, l, h) |
#                                        |o4 -> (h, l, w) |
#                                        |o5 -> (l, w, h) |
#                                        |o6 -> (h, w, l) |
def changeItemOrientation(item, validOrientations):
    orientation = random.choice(validOrientations)
    i = deepcopy(item)
    i2 = deepcopy(item)
    i2["orientation"] = orientation
    if orientation == 2:
        i2["width"] = i["length"]
        i2["height"] = i["height"]
        i2["length"] = i["width"]
    elif orientation == 3:
        i2["width"] = i["width"]
        i2["height"] = i["length"]
        i2["length"] = i["height"]
    elif orientation == 4:
        i2["width"] = i["height"]
        i2["height"] = i["length"]
        i2["length"] = i["width"]
    elif orientation == 5:
        i2["width"] = i["length"]
        i2["height"] = i["width"]
        i2["length"] = i["height"]
    elif orientation == 6:
        i2["width"] = i["height"]
        i2["height"] = i["width"]
        i2["length"] = i["length"]
    else:
        pass
    return i2


def getWeightStandardDeviation(items):
    """
    This function gets the standard deviation of a set of items.
    :param items: set of items.
    :return: standard deviation
    """
    return np.std(np.array(list(map(lambda x: x["weight"], items))))
