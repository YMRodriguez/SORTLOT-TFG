import random

from main.packetAdapter.helpers import changeItemOrientation
from main.packetOptimization.constructivePhase.geometryHelpers import getBottomPlaneArea
from main.packetAdapter.helpers import getAverageWeight, getWeightStandardDeviation


# ------------------ Taxability --------------------------------------------
# This function takes the taxability from a given item
def getTaxability(item, alpha):
    return max(item["weight"], alpha * item["volume"])


# This function takes the taxability from a given item
def setTaxability(item, alpha):
    item["taxability"] = getTaxability(item, alpha)
    return item


# This function sets taxability for each item in a group of items
def addTaxToDataset(items, alpha):
    return list(map(lambda x: setTaxability(x, alpha), items))


# This function returns if a group of items are taxed or not
def areTaxed(items):
    return all(list(map(lambda x: "taxability" in x, items)))


# ------------------- Orientation -------------------------------
def changeOrientationToBest(avgWeight, weightStdDev, item):
    """
    This function changes the item orientation to the one which maximizes the
    stackability.

    :param weightStdDev: standard deviation of the dataset's weight distribution.
    :param avgWeight: average weight from a set of items.
    :param item: item to be evaluated.
    :return: item with the best orientation from the feasible ones.
    """
    itemInOrientations = []
    for i in item["f_orient"]:
        itemInOrientations.append(changeItemOrientation(item, [i]))
    itemInOrientations = sorted(itemInOrientations, key=lambda x: getBottomPlaneArea(x))
    if len(itemInOrientations) == 6:
        if avgWeight - weightStdDev <= item["weight"] <= avgWeight + weightStdDev:
            return random.choice(itemInOrientations[2:-2])
        elif item["weight"] < avgWeight - weightStdDev:
            return random.choice(itemInOrientations[:2])
        else:
            return random.choice(itemInOrientations[-2:])
    else:
        if item["weight"] >= avgWeight:
            return random.choice(itemInOrientations[-2:])
        else:
            return random.choice(itemInOrientations[:2])


# -------------------- Adapter ----------------------------------------
def adaptPackets(items, alpha):
    """
    This function adapts items to be taxed and have the orientation that
    maximizes the stackability.
    :param items: list of items to be packed.
    :param alpha: parameter dependant of the type of transport.
    :return: list of adapted items.
    """
    avgWeight = getAverageWeight(items)
    weiStdDev = getWeightStandardDeviation(items)
    items = list(map(lambda x: changeOrientationToBest(avgWeight, weiStdDev, x), items))
    if not areTaxed(items):
        return addTaxToDataset(items, alpha)
    else:
        print("Items are already taxed")


def cleanDestinationAndSource(items):
    """
    This function return set of items without destination and source strings.
    :param items: set of packets.
    :return: cleaned packets.
    """
    for i in items:
        del i["dst"]
        del i["src"]
    return items
