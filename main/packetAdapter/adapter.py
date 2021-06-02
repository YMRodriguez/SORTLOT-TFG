import random

from main.packetAdapter.helpers import changeItemOrientation
from main.packetOptimization.constructivePhase.geometryHelpers import getBottomPlaneArea
from main.packetAdapter.helpers import getAverageWeight


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
def changeOrientationToBest(avgWeight, item, feasibleOrientations):
    """
    This function changes the item orientation to the one which maximizes the
    stackability.
    :param feasibleOrientations: feasible orientations for the item.
    :param avgWeight: average weight from a set of items.
    :param item: item to be evaluated.
    :return: item with the best orientation from the feasible ones.
    """
    itemInOrientations = []
    for i in feasibleOrientations:
        itemInOrientations.append(changeItemOrientation(item, [i]))
    itemInOrientations = sorted(itemInOrientations, key=lambda x: getBottomPlaneArea(x))
    pivot = len(itemInOrientations)
    if 0.8 <= item["weight"]/avgWeight <= 1.2:
        return random.choice([itemInOrientations[int(pivot/2)],
                              itemInOrientations[int(pivot/2)-1]])
    elif 0.65 <= item["weight"]/avgWeight < 0.8 or 1.2 < item["weight"]/avgWeight <= 1.25:
        return random.choice([itemInOrientations[1], itemInOrientations[-2]])
    elif item["weight"]/avgWeight < 0.65:
        return itemInOrientations[0]
    else:
        return itemInOrientations[-1]


# -------------------- Adapter ----------------------------------------
def adaptPackets(items, alpha, feasibleOrientations=None):
    """
    This function adapts items to be taxed and have the orientation that
    maximizes the stackability.
    :param feasibleOrientations: feasible orientations for an item.
    :param items: list of items to be packed.
    :param alpha: parameter dependant of the type of transport.
    :return: list of adapted items.
    """
    if feasibleOrientations is None:
        feasibleOrientations = [1, 2, 3, 4, 5, 6]
    avgWeight = getAverageWeight(items)
    items = list(map(lambda x: changeOrientationToBest(avgWeight, x, feasibleOrientations), items))
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
