from main.packetOptimization.constructivePhase.geometryHelpers import *
from main.packetAdapter.helpers import getAverageWeight, getMinDim, getMaxWeight
from main.packetOptimization.randomizationAndSorting.sorting import sortingRefillingPhase
from copy import deepcopy
import random
import numpy as np
import math

np.set_printoptions(suppress=True)


# --------------------- Weight Limit - C1 -------------------------------------------------------------
def isWeightExceeded(newItem, truck):
    """
    This function checks is the weight allowed by the container has been exceeded.

    :param newItem: new item to be placed.
    :param truck: truck or container with weight limit.
    :return: True is the weight has been exceeded, False otherwise.
    """
    return truck["weight"] + newItem["weight"] > truck["tonnage"]


# ----------------- Weight Distribution and load balancing - C2 --------------------------------------
def getSubzoneLength(subzones):
    """
    Get subzone length supposing they are all equal.

    """
    return subzones[0]["brr"][2]


def getContainerSubzones(truck):
    """
    Getter for the truck subzones.

    :param truck: truck or container which has subzones.
    :return: subzones object.
    """
    return truck["subzones"]


def getItemSubzones(item):
    """
    Getter for the subzones an item is in.

    :param item: item object.
    :return: subzones object.
    """
    return list(map(lambda x: x[0], item["subzones"]))


def getPercentageOutSubzone(itemBRRz, subzoneBRRz, itemLength):
    """
    Gets the percentage of the base area of the item that is out of the subzone in which it was inserted.

    :param itemBRRz: z-coordinate of the item BRR corner.
    :param subzoneBRRz: z-coordinate of the subzone BRR corner.
    :param itemLength: item length.
    :return: percentage of the area out of the subzone.
    """
    return (itemBRRz - subzoneBRRz) / itemLength


def getNeededExtraSubzonesForItem(subzonesLength, itemLength, outSubzone):
    """
    Gets the number of subzones needed to fit the part of the item out of its BLF insertion subzone.

    :param subzonesLength: length of the subzones of the truck.
    :param itemLength: length of the item.
    :param outSubzone: percentage of the base area of the item that is out of the subzone in which it was inserted.
    :return: number of needed extra subzones.
    """
    # Percentage * length(m) / subzoneLength(m)
    return (outSubzone * itemLength) / subzonesLength


def setItemSubzones(subzones, item):
    """
    This function sets in which zones is the item, for those, it returns an array with the id and the percentage of the base in.
    - Example 1: item in one zone then [id_zone, percentageIn(1)]
    - Example 2: item in two zones then [[id_zone1, p], [id_zone2, (1-p)] ]

    :param subzones: the subzones of the truck.
    :param item: item object.
    :return: item object with subzones added.
    """
    item_blf_z = getBLF(item)[2]
    item_brr_z = getBRR(item)[2]
    subzonesLength = getSubzoneLength(subzones)
    itemSubzones = []
    for i in range(len(subzones)):
        # Check if it fits completely in one subzone.
        if subzones[i]["blf"][2] <= item_blf_z and subzones[i]["brr"][2] >= item_brr_z:
            itemSubzones.append([i + 1, 1])
            break
        # Get if the blf of an item is within the subzone, and include needed extra subzones.
        elif subzones[i]["blf"][2] <= item_blf_z < subzones[i]["brr"][2]:
            # Percentage of item base out of subzone in which was inserted.
            outSubzone = getPercentageOutSubzone(item_brr_z, subzones[i]["brr"][2], item["length"])
            # Decimal number with the needed extra subzones.
            neededExtraSubzonesForItem = getNeededExtraSubzonesForItem(subzonesLength, item["length"], outSubzone)
            # First subzone the item is in.
            itemSubzones = [[subzones[i]["id"], 1 - outSubzone]]
            for s in range(1, math.ceil(neededExtraSubzonesForItem) + 1):
                # Needed to calculate the percentage in the last subzone the item is in.
                if s == math.ceil(neededExtraSubzonesForItem):
                    # PercentageIn = subzoneLength*(decimalExtraSubzones - floorRoundedSubzones)/itemLength
                    itemSubzones.append([subzones[i]["id"] + s, (subzonesLength * (
                            neededExtraSubzonesForItem - math.floor(neededExtraSubzonesForItem))) / item[
                                             "length"]])
                # In case the item is in more than 2 subzones.
                else:
                    itemSubzones.append([subzones[i]["id"] + s, subzonesLength / item["length"]])
        else:
            continue
    item["subzones"] = itemSubzones
    return item


def addWeightContributionTo(item):
    """
    This function adds the weight contribution of an item for each of the subzones the item is at.
    - Input Item Subzone Format: item["subzones"]=[[id_subzone, percentageIn, contactAreaIn],...]

    :param item: item object.
    :return: Output Item Subzone Format: item["subzones"]=[[id_subzone, percentageIn, contactAreaIn, weightIn],...]

    """
    bottomPlaneArea = getBottomPlaneArea(item)
    for i in item["subzones"]:
        # Is not the same the contactAreaIn than the percentage because not all the percentage may be supported nor in contact.
        i.append((i[2] / bottomPlaneArea) * item["weight"])
    return item


def addItemWeightToTruckSubzones(itemSubzones, truck):
    """
    This function adds the item weight to the global truck weight and its respective subzones.

    :param itemSubzones: inserted item subzones object.
    :param truck: truck object.
    :return: modified truck.
    """
    for j in truck["subzones"]:
        for i in itemSubzones:
            if i[0] == j["id"]:
                j["weight"] = j["weight"] + i[3]
    truck["weight"] = sum(list(map(lambda x: x["weight"], truck["subzones"])))
    return truck


def itemContributionNotExceedingSubzonesWeightLimit(item, truckSubzones):
    """
    Checks if the weight contribution of a item in the subzones is on, exceeds their weight limits.

    :param item: item object.
    :param truckSubzones: truck subzones object.
    :return: ndarray with format [condition, item], where the condition is True if the contribution
    does not exceed the weight limits and False otherwise. The item is returned because it is modified
    with its contribution of weight broken down for each subzone.
    """
    # This list stores the state of the condition for each subzone.
    weightNotExceeded = []
    # Once known the contribution area(contactAreaIn), supposing an homogeneous density, calculate the weight contribution.
    itemWithWeightContribution = addWeightContributionTo(item)
    # Check if for each subzone the weight is exceeded.
    for i in item["subzones"]:
        weightNotExceeded.append(all(list(filter(lambda x: x is not None, map(
            lambda x: (i[3] + x["weight"]) <= x["weight_limit"] if i[0] == x["id"] else None,
            truckSubzones)))))
    return [weightNotExceeded[0], itemWithWeightContribution]


# ------------------ Stackability - C5 ---------------------------------------------
def isStackable(item, placedItems):
    """
    This function checks whether the stackability constraint is satisfied so the contributions
    of weight for every object underneath does not exceed certain conditions.

    :param item: item object.
    :param placedItems: list of placed items.
    :return: True is stackable, false otherwise.
    """
    # Reduce the scope of items to those sharing their top y Plane with bottom y Plane of the new item.
    sharePlaneItems = list(
        filter(lambda x: 0 <= abs(getBottomPlaneHeight(item) - getTopPlaneHeight(x)) <= 0.00151, placedItems))
    # This ndarray will store if the conditions are met for every item the newItem is above.
    stackableForSharePlaneItems = []
    for i in sharePlaneItems:
        # % of area between the newItem and the placed items underneath * newItem["weight"]
        itemWeightContribution = (generalIntersectionArea(getZXPlaneFor(i), getZXPlaneFor(item)) / getBottomPlaneArea(
            item)) * item["weight"]
        # Portion of weight above fragile item cannot be more than 50% of the weight of the fragile item.
        if i["fragility"] and itemWeightContribution <= 0.5 * i["weight"]:
            stackableForSharePlaneItems.append(True)
        elif not i["fragility"] and itemWeightContribution <= i["weight"]:
            stackableForSharePlaneItems.append(True)
        else:
            stackableForSharePlaneItems.append(False)
    return all(stackableForSharePlaneItems)


# ------------------ ADR cargo - C6 ------------------------------------------------
# This function returns True if the item in in a suitable position for ADR cargo, False otherwise.
def isADRSuitable(item, truckBRR_z):
    if item["ADR"]:
        itemBRR_z = getBRR(item)[2]
        # The item must have its extreme between the rear of the truck and one meter behind.
        # TODO, make tests on this predefined condition(1 meter).
        return (itemBRR_z >= truckBRR_z - 1) and (itemBRR_z <= truckBRR_z)
    else:
        return True


# ------------------ Stability - C7 ------------------------------------------------
def addContactAreaTo(item, placedItems):
    """
    This function returns the item modified including the contact area in each subzone for it.

    :param item: item object with subzone format [[id_subzone, percentageIn],...].
    :param placedItems: list of placed items.
    :return: item object with subzone format [[id_subzone, percentageIn, contactAreaIn],...].
    """
    newItem = deepcopy(item)
    itemSubzones = deepcopy(item["subzones"])
    # Go over the subzones the item is in.
    for i in itemSubzones:
        if isInFloor(item):
            totalContactAreaInSubzone = getBottomPlaneArea(item) * i[1]
        else:
            # Reduce the scope of items to those in the same subzone
            placedItemsSubzone = list(filter(lambda x: i[0] in getItemSubzones(x), placedItems))
            # Reduce the scope of items to those sharing their top y-axis Plane with bottom y-axis Plane of the new item.
            sharePlaneItems = list(
                filter(lambda x: 0 <= abs(getBottomPlaneHeight(item) - getTopPlaneHeight(x)) <= 0.02151,
                       placedItemsSubzone))
            # Calculate the area of intersection between the sharedPlaneItems and the new item in a subzone.
            itemZXPlane = getZXPlaneFor(item)
            totalContactAreaInSubzone = sum(
                list(map(lambda x: generalIntersectionArea(getZXPlaneFor(x), itemZXPlane), sharePlaneItems))) * i[1]
        # For each subzone the item is in we also have the contact area which is not the same as the percentage within the subzone.
        i.append(totalContactAreaInSubzone)
    newItem["subzones"] = itemSubzones
    return newItem


def isStable(item, placedItems, stage):
    """
    This function checks whether the stability constraint is satisfied.

    :param item: item object.
    :param placedItems: list of items.
    :param stage: the stage of the algorithm.
    :return: True if feasible, false otherwise.
    """
    threshold = 0.8 if stage == 1 else 0.75
    itemWithContactArea = addContactAreaTo(item, placedItems)
    totalItemContactArea = sum(list(map(lambda x: x[2], itemWithContactArea["subzones"])))
    contactAreaPercentage = totalItemContactArea / getBottomPlaneArea(item)
    if contactAreaPercentage >= threshold:
        return [1, itemWithContactArea]
    return [0, itemWithContactArea]


# ------------------ Physical constrains - Truck-related ----------------------------------------
def isWithinTruckLength(item, truckLength):
    """
    This function checks whether an item is within truck's length in an insertion.

    :param item: item object.
    :param truckLength: truck/container length.
    :return: True if within length, False otherwise.
    """
    return getBRR(item)[2] <= truckLength


def isWithinTruckWidth(item, truckWidth):
    """
    This function checks whether an item is withing truck's width in an insertion.

    :param item: item object.
    :param truckWidth: truck/container width.
    :return: True if within width, False otherwise.
    """
    return getBRR(item)[0] <= truckWidth


def isWithinTruckHeight(item, truckHeight):
    """
    This function checks whether an item is withing truck's height in an insertion.

    :param item: item object.
    :param truckHeight: truck/container height.
    :return: True if within height, False otherwise.
    """
    return getTopPlaneHeight(item) <= truckHeight


def isWithinTruckDimensionsConstrains(item, truckDimensions):
    """
    This function checks whether the item satisfies container dimension requirements.

    :param item: the item object.
    :param truckDimensions: dimensions of the container.
    :return: True if within bounds, false otherwise.
    """
    return isWithinTruckLength(item, truckDimensions["length"]) \
           and isWithinTruckWidth(item, truckDimensions["width"]) \
           and isWithinTruckHeight(item, truckDimensions["height"])


# ------------------ Physical constrains - Items-related ----------------------------------------
def overlapper(p1all, p2all):
    """
    This function checks whether an item overlaps other or not.

    :param p1all: triplet of 3 planes.
    :param p2all: triplet of 3 planes.
    :return: True if the item does not overlap, False otherwise.
    """
    for i, j in zip(p1all, p2all):
        if generalIntersectionArea(i, j):
            continue
        # If there is a plane that does not overlap then we conclude there is not overlapping (hyperplane separation theorem)
        else:
            return True
    return False


def getSurroundingItems(massCenter, placedItems, amountOfNearItems):
    """
    This function gets the neighbours of an item.

    :param massCenter: ndarray with the coordinates of an item mass center.
    :param placedItems: list of item objects.
    :param amountOfNearItems: int with the number of desired neighbours.
    :return: list of N neighbours, with N specified.
    """
    if placedItems:
        # Extract the mass center of all placed items.
        itemsMCs = np.asarray(list(map(lambda x: x["mass_center"], placedItems)))
        # Compute and sort the distances between the new item mass center and the rest.
        ndxDistances = getComputedDistIndexes(massCenter, itemsMCs)
        # Get the nearest mass centers and its items.
        return (np.asarray(placedItems)[ndxDistances[:min(len(placedItems), amountOfNearItems)]]).tolist()
    return []


def getComputedDistIndexes(massCenter, massCenters):
    return np.sqrt(np.sum(np.square(massCenter - massCenters), axis=1)).argsort()


def isNotOverlapping(item, placedItems):
    """
    This function checks if an item is overlapping others and vice versa.

    :param item: item object.
    :param placedItems: list of placed item objects.
    :return: True if the item does not overlap other items around it, False otherwise.
    """
    if len(placedItems):
        nearItems = getSurroundingItems(item["mass_center"].reshape(1, 3), placedItems, 15)
        # Generate points for item evaluated.
        p1all = getPlanesFor(item)
        # Validate overlapping conditions item vs. placedItems and vice versa.
        itemToNearItemsNotOverlapping = all(list(map(lambda x: overlapper(p1all, getPlanesFor(x)), nearItems)))
        return itemToNearItemsNotOverlapping
    else:
        return True


def physicalConstrains(placedItems, item, truck):
    """
    Checks whether the physical constraints are satisfied.

    :param placedItems: list of already packed items.
    :param item: item object.
    :param truck: truck object.
    :return: True if they are all satisfied, false otherwise.
    """
    return not isWeightExceeded(item, truck) \
           and isWithinTruckDimensionsConstrains(item, {"width": truck["width"], "height": truck["height"],
                                                        "length": truck["length"]}) \
           and isADRSuitable(item, getTruckBRR(truck)[2]) \
           and isNotOverlapping(item, placedItems)


# --------------------- Helpers to the main module function -----------------------------------
def isFeasible(potentialPoint, placedItems, newItem, minDim, truck, stage):
    """
    This function checks if a potential point is feasible for the insertion of an item, meaning it satisfies all the conditions.

    :param potentialPoint: list of cartesian points.
    :param newItem: item object representing the packet to be inserted.
    :param minDim: minimum size in any dimension (width, height, length) of any item of the cargo.
    :param placedItems: list of items that have been already placed inside the container.
    :param truck: truck object.
    :param stage: packing stage of the algorithm.
    :return: True if the item can be inserted in the potential point, False otherwise.
    """
    item = setItemMassCenter(newItem, potentialPoint, truck["width"], minDim)

    # Conditions to be checked sequentially to improve performance.
    if physicalConstrains(placedItems, item, truck):
        truckSubzones = getContainerSubzones(truck)
        itemWithSubzones = setItemSubzones(truckSubzones, item)
        # This item is [condition, itemWithContactAreaForEachSubzone]
        i3WithCondition = isStable(itemWithSubzones, placedItems, stage)
        # Checks if it is stable and stackable.
        if i3WithCondition[0] and isStackable(item, placedItems):
            # Way of keeping the modified object and if the condition state.
            i4WithCondition = itemContributionNotExceedingSubzonesWeightLimit(i3WithCondition[1], truckSubzones)
            if i4WithCondition[0]:
                return [1, i4WithCondition[1]]
            else:
                return [0, newItem]
        else:
            return [0, newItem]
    else:
        return [0, newItem]


def areaConstraint(currentAreas, maxAreas, item):
    """
    This function checks if the assigned area of a destination is exceeded after an insertion of a new packet.

    :param currentAreas: current area occupied for each destination.
    :param maxAreas: maximum area allowed to a certain destination.
    :param item: item object.
    :return: True if current area after insertion does not exceed the maximum allowed.
    """
    return currentAreas[0][item["dstCode"]] + getBottomPlaneArea(item) <= maxAreas[item["dstCode"]]


def feasibleInFillingBase(potentialPoint, placedItems, newItem, currentAreas, maxAreas, minDim, truck):
    """
    This function checks if a potential point is feasible for the insertion of an item, meaning it satisfies all the conditions.
    During the base filling stage.

    :param potentialPoint: list of cartesian points.
    :param newItem: item object representing the packet to be inserted.
    :param minDim: minimum size in any dimension (width, height, length) of any item of the cargo.
    :param placedItems: list of items that have been already placed inside the container.
    :param truck: truck object.
    :param currentAreas: current area occupied for each destination.
    :param maxAreas: maximum area allowed to a certain destination.
    :return: True if feasible for insertion, False otherwise. Plus the item adapted.
    """
    item = setItemMassCenter(newItem, potentialPoint, truck["width"], minDim)

    if areaConstraint(currentAreas, maxAreas, item):
        if physicalConstrains(placedItems, item, truck):
            truckSubzones = getContainerSubzones(truck)
            itemWithSubzones = setItemSubzones(truckSubzones, item)
            # This item is [condition, itemWithContactAreaForEachSubzone]
            i3WithCondition = isStable(itemWithSubzones, placedItems, 0)
            # Checks if it is stable and stackable.
            if i3WithCondition[0]:
                # Way of keeping the modified object and if the condition state.
                i4WithCondition = itemContributionNotExceedingSubzonesWeightLimit(i3WithCondition[1], truckSubzones)
                if i4WithCondition[0]:
                    return [1, i4WithCondition[1]]
                else:
                    return [0, newItem]
            else:
                return [0, newItem]
        return [0, newItem]
    return [0, newItem]


def areEnoughPlacedItemsOfTheCstCode(dstCode, placedItems, nItems):
    """
    This function checks whether there are enough items with a customer code.

    :param dstCode: The customer code to be checked.
    :param placedItems: Set of items already placed in the container.
    :param nItems: Threshold of items.
    :return: True if there are more items placed than the threshold for the same customer.
    """
    return len(list(filter(lambda x: dstCode == x["dstCode"], placedItems))) >= nItems


def fitnessFor(PP, item, placedItems, notPlacedMaxWeight, maxHeight, maxLength, stage, nDst):
    """
    This function computes the fitness value for a potential point.

    :param nDst: number of destinations.
    :param PP: potential point input, it only contains the coordinates in [x, y, z].
    :param item: item object.
    :param placedItems: set of placed items into the container.
    :param notPlacedMaxWeight: maximum weight of not yet placed items.
    :param maxHeight: maximum height of the truck.
    :param maxLength: maximum length of the truck.
    :param stage: stage in the algorithm.
    :return: potential point with fitness, format [x, y, z, fitness].
    """

    fitWeights = [[0.45, 0.45, 0.05, 0.05],
                  [0.3, 0.5, 0.1, 0.1],
                  [0.15, 0.6, 0.15, 0.1]] if nDst > 1 else [[0.4, 0.0, 0.3, 0.3],
                                                            [0.5, 0.0, 0.3, 0.2],
                                                            [0.5, 0.0, 0.3, 0.2]]
    # Take the weights of the stage.
    stageFW = fitWeights[stage - 1]
    # Length condition in the fitness function.
    lengthCondition = 1 - (PP[2] / maxLength)

    if nDst > 1:
        # For the surrounding customer code objects.
        nItems = 5
        nearItems = getSurroundingItems(item["mass_center"], placedItems, nItems)
        # Consider valid dst code the same or the previous.
        nearItemsWithValidDstCode = list(
            filter(lambda x: x["dstCode"] == item["dstCode"], nearItems))
        if not areEnoughPlacedItemsOfTheCstCode(item["dstCode"], placedItems, nItems):
            surroundingCondition = 1 - item["dstCode"] / (nDst - 1)
        elif len(nearItemsWithValidDstCode) <= 1:
            surroundingCondition = -0.30
        else:
            surroundingCondition = len(nearItemsWithValidDstCode) / max(len(nearItems), 1)
    else:
        surroundingCondition = 0

    # Height condition in the fitness function.
    heightWeightRelation = (item["mass_center"][1] / maxHeight) * (item["weight"] / notPlacedMaxWeight)

    # Item not in floor.
    if PP[1]:
        # Get the item that generated the potential point in which the new item is being inserted.
        sharePlaneItems = list(
            filter(lambda x: 0 <= abs(getBottomPlaneHeight(item) - getTopPlaneHeight(x)) <= 0.00151,
                   placedItems))
        itemBehind = getSurroundingItems(PP, sharePlaneItems, 1)[0]
        itemBehindCondition = int(itemBehind["dstCode"] == item["dstCode"])

        if stage == 3:
            surroundingCondition = -stageFW[3] if item["dstCode"] < itemBehind["dstCode"] else surroundingCondition
        # Check how similar are the areas between the item being inserted and the item behind.
        areaCondition = 1 - abs((getBottomPlaneArea(item) / getBottomPlaneArea(itemBehind)) - 1)
        areaCondition = areaCondition if (1 >= areaCondition >= 0) else 0
        fitvalue = lengthCondition * stageFW[0] + surroundingCondition * stageFW[1] + \
                   areaCondition * stageFW[2] + heightWeightRelation * stageFW[3]
        # Threshold in fitness value.
        if stage == 1:
            fitvalue = fitvalue if itemBehindCondition else 0
        else:
            fitvalue = fitvalue if fitvalue >= 0 else 0
        return np.concatenate((PP, np.array([fitvalue])))
    else:
        fitvalue = lengthCondition * stageFW[0] + surroundingCondition * stageFW[1] + \
                   stageFW[2] + heightWeightRelation * stageFW[3]
        # Threshold in fitness value. TODO, maybe change the threshold depending on the stage.
        fitvalue = fitvalue if fitvalue >= 0 else 0
        return np.concatenate((PP, np.array([fitvalue])))


def fitnessForBase(PP, item, containerLength, nDst, placedItems, maxWeight):
    """
    This function computes the fitness value for a potential point.

    :param maxWeight: maximum weight of the candidate list.
    :param nDst: number of destinations.
    :param PP: potential point input, it only contains the coordinates in [x, y, z].
    :param item: item object.
    :param placedItems: set of placed items into the container.
    :return: potential point with fitness, format [x, y, z, fitness].
    """
    fitWeights = [0.25, 0.25, 0.5] if nDst > 1 else [0.5, 0, 0.5]
    if nDst > 1:
        # For the surrounding customer code objects.
        nItems = 5
        nearItems = getSurroundingItems(item["mass_center"], placedItems, nItems)
        # Consider valid dst code the same or the previous.
        nearItemsWithValidDstCode = list(
            filter(lambda x: x["dstCode"] == item["dstCode"], nearItems))
        surroundingCondition = len(nearItemsWithValidDstCode) / max(len(nearItems), 1)
    else:
        surroundingCondition = 0
    fitnessValue = (item["weight"] / maxWeight) * fitWeights[0] + surroundingCondition * fitWeights[1] + (1-item["mass_center"][2]/containerLength) * fitWeights[2]
    return np.concatenate((PP, np.array([fitnessValue])))


def isBetterPP(newPP, currentBest):
    """
    This function decide which potential point is better. Criteria is:
    - Given same fitness, randomly choose one.
    - Choose the one with the best fitness value.

    :param newPP: potential point being evaluated.
    :param currentBest: current potential point for an item.
    :return: True if the newPP is better than the current best, False otherwise.
    """
    if newPP[3] == currentBest[3]:
        return random.getrandbits(1)
    return newPP[3] > currentBest[3]


def projectPPOverlapped(item, potentialPoints, placedItems):
    """
    This function projects potential point to the closest free surface above them.

    :param item: item object.
    :param potentialPoints: list of spatial coordinates.
    :param placedItems: list of placed items.
    :return: list of potential points projected.
    """
    potentialPointsOverlapped = list(
        filter(lambda x: pointInPlane(x, getBLF(item), getBRR(item)), potentialPoints.tolist()))
    newPotentialPoints = list(filter(lambda x: x not in potentialPointsOverlapped, deepcopy(potentialPoints.tolist())))
    for p in potentialPointsOverlapped:
        ppOut = list(map(lambda x: list(filter(lambda y: all(y == p), x["pp_out"])), placedItems))
        p[1] = getTopPlaneHeight(item) + 0.0015
        ppOut[1] = p[1]
        newPotentialPoints.append(p)
    return newPotentialPoints


def generateNewPPs(item, placedItems, truckHeight, truckWidth, minDim, stage):
    """
    This function creates a list of potential points from an packet after its insertion. Depending on the
    situation and the packet location it will generate the points including different corners.

    :param item: item object.
    :param truckHeight: truck/container height.
    :param truckWidth: truck/container width.
    :param minDim: minimum size in any dimension (width, height, length) of any item of the cargo.
    :param placedItems: list of items that have been already placed inside the container.
    :param stage: stage the packing is at.
    :return: array of new potential points.
    """
    # Add margin to z-coordinate.
    BLR = getBLR(item) + np.array([0, 0, 0.0015])
    # Logic: BRR if x >= truckWidth - minDim aprox, BRF otherwise
    BRF = getBRF(item) + np.array([0.0015, 0, 0])
    BRx = getBRR(item) + np.array([0, 0, 0.0015]) if BRF[0] >= truckWidth - minDim else BRF
    TLF = getTLF(item) + np.array([0, 0.0015, 0])
    TRF = getTRF(item) + np.array([0, 0.0015, 0])
    # Include TRF when we can ensure that the insertion of a new packet will be made from right to left.
    # Include TRF in last stage to maximize top insertions.
    if stage > 1 or TRF[0] >= truckWidth - minDim:
        result = np.array([TLF, TRF]) if TLF[1] < truckHeight - minDim else []
    else:
        result = np.array([TLF]) if TLF[1] < truckHeight - minDim else []
    if not isInFloor(item):
        # Reduce the scope of items to those sharing their top y-axis Plane with bottom y-axis Plane of the new item.
        sharePlaneItems = list(
            filter(lambda x: 0 <= abs(getBottomPlaneHeight(item) - getTopPlaneHeight(x)) <= 0.0016, placedItems))
        # Check which points are not supported.
        isBLRinPlane = any(list(map(lambda x: pointInPlane(BLR, getBLF(x), getBRR(x)), sharePlaneItems)))
        isBxFinPlane = any(list(map(lambda x: pointInPlane(BRF, getBLF(x), getBRR(x)), sharePlaneItems)))
        # Modify not supported points to its projection.
        if not isBxFinPlane:
            BRx = getNearestProjectionPointFor(BRx, placedItems)
        if not isBLRinPlane:
            BLR = getNearestProjectionPointFor(BLR, placedItems)
    if len(result):
        result = np.vstack((result, BLR, BRx))
    else:
        result.extend((BLR, BRx))
        result = np.asarray(result)
    return result


def fillListBase(candidateList, potentialPoints, truck, nDst, minDim, placedItems):
    """
    This function creates a solution from a list of packets and a given potential points in the base of the truck.

    :param candidateList: list of items to be packed.
    :param potentialPoints: list of cartesian points representing potential points.
    :param truck: truck object.
    :param nDst: number of destinations of the cargo.
    :param minDim: minimum size in any dimension (width, height, length) of any item of the cargo.
    :param placedItems: list of items that have been already placed inside the container.
    :return: dictionary with the packed items, non-packed items, current state of the truck and not used potential points.
    """
    # Fill number of items per destination.
    nItemDst = []
    for n in range(nDst):
        nItemDst.append(len(list(filter(lambda x: x["dstCode"] == n, candidateList))))
    # Average weight of candidateList.
    avgWeightGeneral = getAverageWeight(candidateList)
    # Obtain the maximum weight of the candidateList.
    maxWeight = getMaxWeight(candidateList)
    # Filter the candidates for each destination that are greater than half the average weight.
    filteredCandidates = []
    for d in list(range(nDst)):
        filteredCandidates.append(list(
            filter(lambda x: x["dstCode"] == d and x["weight"] >= avgWeightGeneral * 0.5, candidateList)))
    # Count amount of filtered for each destination.
    nFilteredDst = list(map(lambda x: len(x), filteredCandidates))
    # Group items that did not pass the filter.
    flattenedFilteredCandidates = [item for sublist in filteredCandidates for item in sublist]
    discardList = list(filter(lambda x: x not in flattenedFilteredCandidates, candidateList))
    # Update list with the items that passed the filter.
    candidateList = filteredCandidates
    # Create max area items of a destination can occupy within the container.
    maxAreas = generateMaxAreas(nItemDst, nFilteredDst, truck, nDst)
    # Initialize current areas.
    currentAreas = np.zeros((1, nDst))
    # Create new list for discarded PP.
    discardedPP = []
    # Auxiliary list to group PP that are not important in this stage(those that are not in the floor).
    notInFloorPP = []
    # Check the best item for each Potential Point in order of destination.
    for d in range(nDst):
        # The intention is to fill the max area of the container assigned to a destination,
        # so it checks this condition for each potential point, each item and each item orientation.
        while (currentAreas[0][d] <= maxAreas[d]) and len(potentialPoints):
            # Check if there is no item that satisfies fulfilling without exceeding max allowed area.
            if not any(list(map(lambda x: getBottomPlaneArea(x) + currentAreas[0][d] <= maxAreas[d], candidateList[d]))):
                break
            # Initialization of best point as the worst, in this context the TRR of the truck. And worse fitness value.
            ppBest = np.array([truck["width"], truck["height"], truck["length"], 0])
            # Get the potential point with lower z-coordinate (closest to the front of the container).
            pp = sorted(potentialPoints, key=lambda x: x[2])[0]
            # Gather in one list the current destination and the next.
            candidatesByDst = candidateList[d] + candidateList[d+1] if d!=nDst-1 else candidateList[d]
            # Only proceed with the search if the item is in the floor.
            if not pp[1]:
                for i in candidatesByDst:
                    # Pick one random orientation apart from the current.
                    # orientations = [i["or"], random.choice([o for o in i["feasibleOr"] if o != i["or"]])]
                    orientations = i["feasibleOr"]
                    for o in orientations:
                        if o != i["or"]:
                            i = changeItemOrientation(i, [o])
                        # Try to get the best PP for an item.
                        # [condition, item]
                        feasibility = feasibleInFillingBase(pp, placedItems, i, currentAreas, maxAreas, minDim, truck)
                        if feasibility[0]:
                            ppWithFitness = fitnessForBase(pp, feasibility[1], truck["length"], nDst, placedItems, maxWeight)
                            # Can use the same even thought the concept is different, in all cases the pp is going to be
                            # the same but with diff fitness functions so the highest will save the item.
                            if isBetterPP(ppWithFitness, ppBest):
                                ppBest = ppWithFitness
                                feasibleItem = feasibility[1]
                    # This condition is only important for the first two items.
                    if ppBest[3] == 1:
                        break
                # If the best is different from the worst there is a PP to insert the item.
                if ppBest[3] != 0:
                    currentAreas[0][feasibleItem["dstCode"]] = currentAreas[0][
                                                                   feasibleItem["dstCode"]] + getBottomPlaneArea(feasibleItem)
                    # Add pp in which the object is inserted.
                    feasibleItem["pp_in"] = ppBest[0:3]
                    # Remove item from candidate list.
                    candidateList[feasibleItem["dstCode"]] = list(filter(lambda x: feasibleItem["id"] != x["id"], candidateList[feasibleItem["dstCode"]]))
                    # Remove pp_best from potentialPoints list.
                    potentialPoints = np.array(list(filter(lambda x: any(x != ppBest[0:3]), potentialPoints)))
                    # Generate new PPs to add to item and potentialPoints.
                    newPPs = generateNewPPs(feasibleItem, placedItems, truck["height"], truck["width"], minDim, 0)
                    feasibleItem["pp_out"] = newPPs
                    if potentialPoints.shape[0]:
                        potentialPoints = np.vstack((potentialPoints, newPPs)) if len(newPPs) else potentialPoints
                    else:
                        potentialPoints = newPPs
                    # Add insertion order to item.
                    feasibleItem["in_id"] = len(placedItems)
                    # Add item to placedItems.
                    placedItems.append(feasibleItem)
                    # Update truck weight status
                    truck = addItemWeightToTruckSubzones(feasibleItem["subzones"], truck)
                else:
                    # There is no item and item orientation for this potential point.
                    discardedPP.append(pp)
                    potentialPoints = np.array(list(filter(lambda x: any(x != pp[0:3]), potentialPoints)))
            else:
                # Add potential point that is not on the floor.
                notInFloorPP.append(pp)
                potentialPoints = np.array(list(filter(lambda x: any(x != pp[0:3]), potentialPoints)))
                continue
    # Update the list with the items that have not been packed.
    discardList = discardList + [item for sublist in candidateList for item in sublist]
    # Keep the potential points that are not in the floor(which should be full).
    potentialPoints = np.asarray(notInFloorPP)
    return {"placed": placedItems, "discard": discardList,
            "truck": truck, "potentialPoints": potentialPoints}


def fillList(candidateList, potentialPoints, truck, retry, stage, nDst, minDim, placedItems):
    """
    This function creates a solution from a list of packets and a given potential points above the first layer
    base of items of the truck.

    :param candidateList:
    :param potentialPoints:
    :param truck: truck object.
    :param retry: binary condition to reorient each item in their insertion evaluation.
    :param stage: number indicating the packing stage, options: [1, 2, 3]
    :param nDst: number of destinations of the cargo.
    :param minDim: minimum size in any dimension (width, height, length) of any item of the cargo.
    :param placedItems: list of items that have been already placed inside the container.
    :return: dictionary with the packed items, non-packed items, current state of the truck and not used potential points.
    """
    discardList = []
    for i in candidateList:
        # Update average list excluding those items which have been already placed.
        notPlacedMaxWeight = getMaxWeight(list(filter(lambda x: x not in placedItems, candidateList)))
        # Using the method as a retryList fill.
        if retry:
            i = reorient(i)
        # Initialization of best point as the worst, in this context the TRR of the truck. And worse fitness value.
        ppBest = np.array([truck["width"], truck["height"], truck["length"], 0])
        # Try to get the best PP for an item.
        for pp in potentialPoints:
            # [condition, item]
            feasibility = isFeasible(pp, placedItems, i, minDim, truck, stage)
            if feasibility[0]:
                ppWithFitness = fitnessFor(pp, feasibility[1], placedItems, notPlacedMaxWeight, truck["height"],
                                           truck["length"], stage, nDst)
                if isBetterPP(ppWithFitness, ppBest):
                    ppBest = ppWithFitness
                    feasibleItem = feasibility[1]
        # If the best is different from the worst there is a PP to insert the item.
        if ppBest[3] != 0:
            # Add pp in which the object is inserted.
            feasibleItem["pp_in"] = ppBest[0:3]
            # Remove pp_best from potentialPoints list.
            potentialPoints = np.array(list(filter(lambda x: any(x != ppBest[0:3]), potentialPoints)))
            # Generate new PPs to add to item and potentialPoints.
            potentialPoints = projectPPOverlapped(feasibleItem, potentialPoints, placedItems)
            newPPs = generateNewPPs(feasibleItem, placedItems, truck["height"], truck["width"], minDim, stage)
            feasibleItem["pp_out"] = newPPs
            potentialPoints = np.vstack((potentialPoints, newPPs)) if len(newPPs) else potentialPoints
            # Add insertion order to item.
            feasibleItem["in_id"] = len(placedItems)
            # Add item to placedItems.
            placedItems.append(feasibleItem)
            # Update truck weight status
            truck = addItemWeightToTruckSubzones(feasibleItem["subzones"], truck)
        else:
            discardList.append(i)
    return {"placed": placedItems, "discard": discardList,
            "truck": truck, "potentialPoints": potentialPoints}


def createAndProjectNewPPs(placedItems, potentialPoints):
    """
    This function creates new potential points and projects the overlapped ones.

    :param placedItems: set of placed items that 
    :param potentialPoints: set of potential points from later phases.
    :return: set of potential points with a projection in those that were overlapped.
    """
    potentialPoints = potentialPoints.tolist()
    for p in potentialPoints:
        if not p[1]:
            surroundingItems = getSurroundingItems(np.array(p), placedItems, 4)
            itemsAbove = list(filter(lambda x: pointInPlane(np.array(p), getBLF(x), getBRR(x)), surroundingItems))
            itemAbove = itemsAbove[0] if len(itemsAbove) else None
            if itemAbove is not None:
                p[1] = getTopPlaneHeight(itemAbove)
    for i in placedItems:
        if not isInFloor(i):
            BRR = getBRR(i) + np.array([0, 0, 0.0015])
            nPPs = len(i["pp_out"].tolist())
            ppOut = deepcopy(i["pp_out"])
            if len(ppOut[np.all(ppOut != BRR, axis=1), :].tolist()) < nPPs:
                ppOut = ppOut.tolist()
                # Reduce the scope of items to those sharing their top y-axis Plane with bottom y-axis Plane of the new item.
                sharePlaneItems = list(
                    filter(lambda x: 0 <= abs(getBottomPlaneHeight(i) - getTopPlaneHeight(x)) <= 0.0016, placedItems))
                isBRRinPlane = any(list(map(lambda x: pointInPlane(BRR, getBLF(x), getBRR(x)), sharePlaneItems)))
                if not isBRRinPlane:
                    BRR = getNearestProjectionPointFor(BRR, placedItems)
                ppOut.append(BRR)
                potentialPoints.append(BRR)
                i["pp_out"] = np.asarray(ppOut)
    return np.asarray(potentialPoints)


def checkSubgroupingCondition(packets):
    """
    Check if there is as many subgroup ids as items otherwise there is subgrouping.

    :param packets: list of packets.
    :return: True if there is subgrouping, False otherwise.
    """
    return len(list(map(lambda x: x["subgroupId"], packets))) < len(packets)


def main_cp(truck, candidateList, nDst):
    """
    This function is the main part of the core of the solution builder.

    :param truck: truck object.
    :param candidateList: list of objects representing the cargo.
    :param nDst: number of destinations in the cargo.
    :return: dictionary with the packed items, non-packed items, current state of the truck and not used potential points.
    """

    potentialPoints = truck["pp"]
    minDim = getMinDim(candidateList)

    # Determine if there is relevant subgrouping conditions
    subgrouping = checkSubgroupingCondition(candidateList)
    stage = 0
    #    startTime0 = time.time()
    fillingBase = fillListBase(candidateList, potentialPoints, truck, nDst, minDim, [])
    # ----- DEBUG-INFO ------
    #    print("Time stage " + str(time.time() - startTime0))
    #    print("Number of items packed after stage" + len(filling0["placed"]))
    #    startTime1 = time.time()
    # ----- DEBUG-INFO ------

    stage = stage + 1
    fillingS1 = fillList(sortingRefillingPhase(fillingBase["discard"], fillingBase["placed"], subgrouping, nDst),
                         np.unique(fillingBase["potentialPoints"], axis=0), truck, 0, stage,
                         nDst, getMinDim(fillingBase["discard"]), fillingBase["placed"])
    newPPs = createAndProjectNewPPs(fillingS1["placed"], fillingS1["potentialPoints"])
    stage = stage + 1

    # ----- DEBUG-INFO ------
    #    print("Time stage " + str(time.time() - startTime1))
    #    startTime2 = time.time()
    #    print("Number of items packed after stage" + len(filling1["placed"]))
    # ----- DEBUG-INFO ------

    filling = fillList(fillingS1["discard"],
                       np.unique(newPPs, axis=0),
                       fillingS1["truck"], 1, stage, nDst,
                       getMinDim(fillingS1["discard"]), fillingS1["placed"])
    # ----- DEBUG-INFO ------
    #    print("Time stage " + str(time.time() - startTime2))
    #    startTime3 = time.time()
    #    print("Number of items packed after stage" + len(filling["placed"]))
    # ----- DEBUG-INFO ------

    stage = stage + 1

    # Got to do a few more tests to check if this additional phase is really relevant.
    if len(candidateList) < 300:
        filling = fillList(filling["discard"],
                           np.unique(filling["potentialPoints"], axis=0),
                           filling["truck"], 1, stage, nDst,
                           getMinDim(filling["discard"]), filling["placed"])
    # ----- DEBUG-INFO ------
    #    print("Number of items packed after stage" + len(fillingSA["placed"]))
    #    print("Stage time: " + str(time.time() - startTime3))
    # ----- DEBUG-INFO ------
    return filling
