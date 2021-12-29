import random
import numpy as np
import pandas as pd


def getAverageWeight(items):
    """
    This function gets the average weight for a list of items.

    :param items: set of items.
    :return: average weight in kilograms.
    """
    return sum(list(map(lambda x: x["weight"], items))) / len(items)


def getStatsForBase(items):
    df = pd.DataFrame(items)
    return df.groupby(["dstCode"])[["width", "height", "length"]].mean().mean(axis=1), df["weight"].mean(), df["weight"].std(ddof=0)


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
            And taking o1 as reference        |o2 -> (l, h, w) |
                                              |o3 -> (w, l, h) |
                                              |o4 -> (h, l, w) |
                                              |o5 -> (l, w, h) |
                                              |o6 -> (h, w, l) |

    :param item: item object.
    :param validOrientations: allowed orientations.
    :return: item object with a randomly different orientation
    """
    orientation = random.choice(validOrientations)
    # First we need to normalize the measures to o1.
    dim = sorted([item["width"], item["height"], item["length"]])
    o1width, o1height, o1length = dim[2], dim[0], dim[1]
    item["or"] = orientation
    if orientation == 2:
        item["width"] = o1length
        item["height"] = o1height
        item["length"] = o1width
    elif orientation == 3:
        item["width"] = o1width
        item["height"] = o1length
        item["length"] = o1height
    elif orientation == 4:
        item["width"] = o1height
        item["height"] = o1length
        item["length"] = o1width
    elif orientation == 5:
        item["width"] = o1length
        item["height"] = o1width
        item["length"] = o1height
    elif orientation == 6:
        item["width"] = o1height
        item["height"] = o1width
        item["length"] = o1length
    else:
        item["width"] = o1width
        item["height"] = o1height
        item["length"] = o1length
    return item


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


def getVolumeDistributionByDst(items, nDst, containerVol):
    distribution = []
    for d in range(nDst):
        distribution.append((len(list(map(lambda x: x["dstCode"] == d, items))) / len(items)) * containerVol)
    return distribution
