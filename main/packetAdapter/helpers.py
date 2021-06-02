import random
from copy import deepcopy
import numpy as np


def getAverageWeight(items):
    """
    This function gets the average weight for a list of items.

    :param items: set of items.
    :return: average weight in kilograms.
    """
    return sum(list(map(lambda x: x["weight"], items))) / len(items)


def getAverageVolume(items):
    """
    This function gets the average weight for a list of items.

    :param items: set of items.
    :return: average volume in cubic meters.
    """
    return sum(list(map(lambda x: x["volume"], items))) / len(items)


def getAveragePriority(items):
    """
    This function gets the average priority for a list of items.

    :param items: set of items.
    :return: average priority.
    """
    return sum(list(map(lambda x: x["priority"], items))) / len(items)


def getAverageTaxability(items):
    """
    This function gets the average taxability from a group of items.

    :param items: set of items.
    :return: average taxability in kilograms.
    """
    return sum(list(map(lambda x: x["taxability"] if "taxability" in x else 0, items))) / len(items)


def getMaxTaxability(items):
    """
    This function gets the maximum taxability from a group of items.

    :param items: set of items.
    :return: maximum taxability in kilograms.
    """
    return max(item["taxability"] for item in items)


def getMaxPriority(items):
    """
    This function gets the maximum priority from a group of items.

    :param items: set of items.
    :return: maximum priority.
    """
    return max(item["priority"] for item in items)


def getMaxVolume(items):
    """
    This function returns maximum volume value in a list of items.

    :param items: set of items.
    :return: maximum volume in cubic meters.
    """
    return max(item["volume"] for item in items)


def getMaxWeight(items):
    """
    This function returns maximum weight value in a list of items.

    :param items: set of items.
    :return: maximum weight in kilograms.
    """
    return max(item["weight"] for item in items)


def changeItemOrientation(item, validOrientations):
    """
    This function randomly chooses a feasible orientation with equal probability.
    # Orientation equivalences (x, y, z) ---> |o1 -> (w, h, l) |
                                              |o2 -> (l, h, w) |
                                              |o3 -> (w, l, h) |
                                              |o4 -> (h, l, w) |
                                              |o5 -> (l, w, h) |
                                              |o6 -> (h, w, l) |

    :param item: item object.
    :param validOrientations: allowed orientations.
    :return: item object with a randomly different orientation
    """
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


def getMinDim(items):
    """
    This function gets the minimum dimension from a set of items.

    :param items: set of items
    :return: minimum dimension in metres.
    """
    return np.min(np.array(list(map(lambda x: (x["width"], x["height"], x["length"]), items))))
