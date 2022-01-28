from main.packetOptimization.constructivePhase.geometryHelpers import *
from main.packetAdapter.helpers import getStatsForBase, getMinDim, getMaxWeight
from main.packetOptimization.randomizationAndSorting.sorting import reSortingPhase
from copy import deepcopy
import random
import numpy as np
import math
import time

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
        filter(lambda x: 0 <= abs(getBottomPlaneHeight(item) - getTopPlaneHeight(x)) <= 0.0016, placedItems))
    # Store if we can stack an item above others.
    stackableForSharePlaneItems = []
    for i in sharePlaneItems:
        # % of area between the newItem and the placed items underneath * newItem["weight"]
        itemWeightContribution = (generalIntersectionArea(getZXPlaneFor(i), getZXPlaneFor(item)) / getBottomPlaneArea(
            item)) * item["weight"]
        # Portion of weight above fragile item cannot be more than 50% of the weight of the fragile item.
        if i["fragility"] and itemWeightContribution <= 0.5 * i["weight"]:
            stackableForSharePlaneItems.append(True)
        # Weight above an item must not exceed its weight.
        elif not i["fragility"] and itemWeightContribution <= i["weight"]:
            stackableForSharePlaneItems.append(True)
        else:
            stackableForSharePlaneItems.append(False)
    return all(stackableForSharePlaneItems)


# ------------------ ADR cargo - C6 ------------------------------------------------
def isADRSuitable(item, truckBRR_z):
    """
    Checks whether an ADR packet can go into the container.

    :param item: packet.
    :param truckBRR_z: greater z coordinate of the container.
    :return: True if the packet can be introduced, False otherwise.
    """
    if item["ADR"]:
        # This condition would really depend on the regulation. There are cases in which ADR packets can not be staked
        # However, since this condition is just binary lets consider that
        return max([item["width"], item["height"], item["length"]]) >= truckBRR_z - item["mass_center"][2]
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
                filter(lambda x: 0 <= abs(getBottomPlaneHeight(item) - getTopPlaneHeight(x)) <= 0.0151,
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
        ndxDistances = getComputedDistancesIndexes(massCenter, itemsMCs)
        # Get the nearest mass centers and its items.
        return (np.asarray(placedItems)[ndxDistances[:min(len(placedItems), amountOfNearItems)]]).tolist()
    return []


def getComputedDistancesIndexes(massCenter, massCenters):
    return np.sqrt(np.sum(np.square(massCenter - massCenters), axis=1)).argsort()


def isNotOverlapping(item, placedItems):
    """
    This function checks if an item is overlapping others and vice versa.

    :param item: item object.
    :param placedItems: list of placed item objects.
    :return: True if the item does not overlap other items around it, False otherwise.
    """
    if len(placedItems):
        nearItems = getSurroundingItems(item["mass_center"].reshape(1, 3), placedItems,
                                        max(int(len(placedItems) * 0.15), 25))
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


def fitnessFor(PP, item, placedItems, notPlacedMaxWeight, maxHeight, maxLength, stage, nDst, coeffs):
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

    fitWeights = [coeffs[:4],
                  coeffs[4:],
                  coeffs[4:]] if nDst > 1 else [[coeffs[0], 0, coeffs[2], coeffs[3]],
                                                 [coeffs[4], 0, coeffs[6], coeffs[7]],
                                                 [coeffs[4], 0, coeffs[6], coeffs[4]]]
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
        surroundingCondition = len(nearItemsWithValidDstCode) / max(len(nearItems), 1)
    else:
        surroundingCondition = 0

    # Height condition in the fitness function.
    heightWeightRelation = (item["mass_center"][1] / maxHeight) * (item["weight"] / notPlacedMaxWeight)

    # Item not in floor.
    if PP[1]:
        # Get the item that generated the potential point in which the new item is being inserted.
        sharePlaneItems = list(
            filter(lambda x: 0 <= abs(getBottomPlaneHeight(item) - getTopPlaneHeight(x)) <= 0.0016,
                   placedItems))
        itemBehind = getSurroundingItems(PP, sharePlaneItems, 1)[0]

        # This is a way to avoid mistaken subgrouping in the latest packing stages.
        if stage == 3:
            surroundingCondition = -stageFW[3] if item["dstCode"] < itemBehind["dstCode"] else surroundingCondition
        # Check how similar are the areas between the item being inserted and the item behind.
        areaCondition = 1 - abs((getBottomPlaneArea(item) / getBottomPlaneArea(itemBehind)) - 1)
        areaCondition = areaCondition if (1 >= areaCondition >= 0) else 0
        fitvalue = lengthCondition * stageFW[0] + surroundingCondition * stageFW[1] + \
                   areaCondition * stageFW[2] + heightWeightRelation * stageFW[3]
        fitvalue = fitvalue if fitvalue >= 0 else 0
        return [PP, fitvalue]
    else:
        fitvalue = lengthCondition * stageFW[0] + surroundingCondition * stageFW[1] + \
                   stageFW[2] + heightWeightRelation * stageFW[3]
        # Threshold in fitness value. TODO, maybe change the threshold depending on the stage.
        fitvalue = fitvalue if fitvalue >= 0 else 0
        return [PP, fitvalue]


def fitnessForBase(PP, item, containerLength, nDst, placedItems, maxWeight, coefficients):
    """
    This function computes the fitness value for a potential point.

    :param maxWeight: maximum weight of the candidate list.
    :param nDst: number of destinations.
    :param PP: potential point input, it only contains the coordinates in [x, y, z].
    :param item: item object.
    :param placedItems: set of placed items into the container.
    :return: potential point with fitness, format [x, y, z, fitness].
    """
    fitWeights = coefficients if nDst > 1 else [coefficients[0], 0, coefficients[2]]
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
    fitnessValue = (item["weight"] / maxWeight) * fitWeights[0] + surroundingCondition * fitWeights[1] + (
            1 - item["mass_center"][2] / containerLength) * fitWeights[2]
    return [PP, fitnessValue]


def isBetterPP(newPP, currentBest):
    """
    This function decide which potential point is better. Criteria is:
    - Given same fitness, randomly choose one.
    - Choose the one with the best fitness value.

    :param newPP: potential point being evaluated.
    :param currentBest: current potential point for an item.
    :return: True if the newPP is better than the current best, False otherwise.
    """
    if newPP[1] == currentBest[1]:
        return random.getrandbits(1)
    return newPP[1] > currentBest[1]


def generateNewPPs(item, placedItems, truckHeight, truckWidth, minDim, stage):
    """
    This function creates a list of potential points from a packet after its insertion. Depending on the
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
    BRR = getBRR(item) + np.array([0, 0, 0.0015])
    BRx = BRR if BRF[0] >= truckWidth - minDim else BRF
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
        isBLRInPlane = any(list(map(lambda x: pointInPlane(BLR, getBLF(x), getBRR(x)), sharePlaneItems)))
        isBRxInPlane = any(list(map(lambda x: pointInPlane(BRF, getBLF(x), getBRR(x)), sharePlaneItems)))
        # Modify not supported points to its projection.
        if not isBRxInPlane:
            BRx = getNearestProjectionPointFor(BRx, placedItems)
        if not isBLRInPlane:
            BLR = getNearestProjectionPointFor(BLR, placedItems)
    if len(result):
        if not stage:
            result = np.vstack((result, BLR, BRR, BRF))
        else:
            result = np.vstack((result, BLR, BRx))
    else:
        if not stage:
            result.extend((BLR, BRR, BRF))
            result = np.asarray(result)
        else:
            result.extend((BLR, BRx))
            result = np.asarray(result)
    return result


def getCandidatesByDestination(candidates, nDst, index):
    if nDst == 1:
        return candidates[index]
    elif nDst == 2:
        return candidates[index]
    else:
        if index == (nDst - 1):
            return candidates[index]
        elif index == (nDst - 2):
            return candidates[index] + candidates[index + 1]
        else:
            return candidates[index]


def loadBase(candidateList, potentialPoints, truck, nDst, minDim, placedItems, coefficients):
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
    # Statistics on the candidateList.
    meanDim, avgWeight, stdDev = getStatsForBase(candidateList)
    # Obtain the maximum weight of the candidateList.
    maxWeight = getMaxWeight(candidateList)
    # Filter the candidates for each destination that are greater than half the average weight.
    filteredCandidates = []
    for d in range(nDst):
        filteredCandidates.append(list(
            filter(lambda x: x["dstCode"] == d and x["weight"] >= avgWeight - stdDev / 2, candidateList)))
    # Count amount of filtered for each destination.
    nFilteredDst = list(map(lambda x: len(x), filteredCandidates))
    # Create max area items of a destination can occupy within the container.
    maxAreas = generateMaxAreas(nItemDst, nFilteredDst, truck, nDst)
    # Make sure there are not too many packets nor very few caused by a really low std dev.
    for d in range(nDst):
        nItemsEstimation = int(maxAreas[d] / (meanDim[d] ** 2))
        # Added filtered candidates based on estimation.
        filteredCandidates[d] = list(filter(lambda x: x["dstCode"] == d, candidateList))[:int(nItemsEstimation * 1.5)]
    # Initialize current areas.
    currentAreas = np.zeros((1, nDst))
    # Group items that did not pass the filter.
    flattenedFilteredCandidates = [item for sublist in filteredCandidates for item in sublist]
    discardList = list(filter(lambda x: x not in flattenedFilteredCandidates, candidateList))
    # Update list with the items that passed the filter.
    candidateList = filteredCandidates
    # Auxiliary list to group PP that are not important in this stage(those that are not in the floor).
    notInFloorPPByDst = list(map(lambda x: [], range(nDst)))
    # Check the best item for each Potential Point in order of destination.
    for d in range(nDst):
        # Add to next destination the potential points of the previous destination.
        if d:
            potentialPoints.append(np.array(potentialPoints[d - 1]))
        # The intention is to fill the max area of the container assigned to a destination,
        # so it checks this condition for each potential point, each item and each item orientation.
        while (currentAreas[0][d] <= maxAreas[d]) and len(potentialPoints[d]):
            # Check if there is no item that satisfies fulfilling without exceeding max allowed area.
            if not any(
                    list(map(lambda x: getBottomPlaneArea(x) + currentAreas[0][d] <= maxAreas[d], candidateList[d]))):
                break
            # Initialization of best point as the worst, in this context the TRR of the truck. And worse fitness value.
            ppBest = [np.array([truck["width"], truck["height"], truck["length"]]), 0]
            # Get the potential point with lower z-coordinate (closest to the front of the container).
            pp = sorted(potentialPoints[d], key=lambda x: x[:][2])[0]
            # Gather in one list the current destination and the next.
            # TODO, keep in mind this alternative: getCandidatesByDestination()
            candidatesByDst = candidateList[d]
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
                            ppWithFitness = fitnessForBase(pp, feasibility[1], truck["length"], nDst, placedItems,
                                                           maxWeight, coefficients)
                            # Can use the same even thought the concept is different, in all cases the pp is going to be
                            # the same but with diff fitness functions so the highest will save the item.
                            if isBetterPP(ppWithFitness, ppBest):
                                ppBest = ppWithFitness
                                feasibleItem = feasibility[1]
                    # This condition is only important for the first two items.
                    if ppBest[1] == 1:
                        break
                # If the best is different from the worst there is a PP to insert the item.
                if ppBest[1]:
                    currentAreas[0][feasibleItem["dstCode"]] = currentAreas[0][
                                                                   feasibleItem["dstCode"]] + getBottomPlaneArea(
                        feasibleItem)
                    # Add pp in which the object is inserted.
                    feasibleItem["pp_in"] = ppBest[0]
                    # Remove item from candidate list.
                    candidateList[feasibleItem["dstCode"]] = list(
                        filter(lambda x: feasibleItem["id"] != x["id"], candidateList[feasibleItem["dstCode"]]))
                    # Remove pp_best from potentialPoints list.
                    potentialPoints[d] = potentialPoints[d][~(potentialPoints[d] == ppBest[0]).all(axis=1)]
                    # Generate new PPs to add to item and potentialPoints.
                    newPPs = generateNewPPs(feasibleItem, placedItems, truck["height"], truck["width"], minDim, 0)
                    feasibleItem["pp_out"] = newPPs
                    # In case there are no potential points left, the operation is not a vertical stack.
                    if potentialPoints[d].shape[0]:
                        # Need to keep numpy matrix structure in each dst of PPs to make the erasing operation.
                        potentialPoints[d] = np.vstack((potentialPoints[d], newPPs)) if len(newPPs) else \
                            potentialPoints[d]
                    else:
                        potentialPoints[d] = newPPs[d]
                    # Add insertion order to item.
                    feasibleItem["in_id"] = len(placedItems)
                    # Add item to placedItems.
                    placedItems.append(feasibleItem)
                    # Update truck weight status
                    truck = addItemWeightToTruckSubzones(feasibleItem["subzones"], truck)
                else:
                    # There is no item and item orientation for this potential point.
                    # Delete it from the list of potential points.
                    potentialPoints[d] = potentialPoints[d][~(potentialPoints[d] == pp).all(axis=1)]
            else:
                # Add potential point that is not on the floor.
                notInFloorPPByDst[d].append(pp)
                potentialPoints[d] = potentialPoints[d][~(potentialPoints[d] == pp).all(axis=1)]
                continue
    # Update the list with the items that have not been packed.
    discardList = discardList + [item for sublist in candidateList for item in sublist]
    # Keep the potential points that are not in the floor.
    return {"placed": placedItems, "discard": discardList,
            "truck": truck, "potentialPoints": list(map(lambda x: np.asarray(x), notInFloorPPByDst))}


def getMixedPotentialPoints(potentialPoints):
    """
    This function sorts potential points by the length of the container
    and makes a distribution depending on the number of destinations, maximising success in feasibility and minimizing time.
    Format in explanations: [dstCode, dstCode+] where +/- is upper/lower half of z ordered potential points.

    :param potentialPoints: list of potential points.
    :return: potential points of interest in each destination.
    """
    newPPs = []
    sortedPPByZ = list(
        map(lambda y: np.asarray(y), list(map(lambda x: sorted(x, key=lambda y: y[:][2]), potentialPoints))))
    # One destination case.
    if len(potentialPoints) == 1:
        return sortedPPByZ
    else:
        # Two destinations case.
        if len(potentialPoints) == 2:
            # [[0,1-], [0+, 1]] potential points from destinations.
            return [np.vstack((sortedPPByZ[0], sortedPPByZ[1][:int(len(potentialPoints[1]) / 2)])),
                    np.vstack((sortedPPByZ[0][-int(len(potentialPoints[0]) / 2):], sortedPPByZ[1]))]
        # More than two destinations.
        else:
            for i in range(len(potentialPoints)):
                # For the first destination -> [0, 1-]
                if not i:
                    newPPs.append(np.vstack((sortedPPByZ[i], sortedPPByZ[i + 1][:int(len(potentialPoints[i]) / 2)])))
                # [(nDst-2)+, (nDst-1)] = [(dstCode-1)+, (dstCode)]
                elif i == len(potentialPoints) - 1:
                    newPPs.append(
                        np.vstack((sortedPPByZ[i - 1][-int(len(potentialPoints[i - 1]) / 2):], sortedPPByZ[i])))
                # [(dstCode-1)+, dstCode, (dstCode+1)-]
                else:
                    newPPs.append(np.vstack((sortedPPByZ[i - 1][-int(len(potentialPoints[i - 1]) / 2):], sortedPPByZ[i],
                                             sortedPPByZ[i + 1][:int(len(potentialPoints[i + 1]) / 2)])))
    return newPPs


def getPossiblePPsOverlapped(potentialPoints, dstCode):
    if dstCode:
        return np.vstack(
            (potentialPoints[dstCode], np.asarray(sorted(potentialPoints[dstCode - 1], key=lambda x: x[:][2])[:10])))
    return potentialPoints[dstCode]


def load(candidateList, potentialPoints, truck, retry, stage, nDst, minDim, placedItems, coefficients):
    """
    This function creates a solution from a list of packets and a given potential points above the first layer
    base of items of the truck.

    :param candidateList: discard list from previous phase.
    :param potentialPoints:
    :param truck: truck object.
    :param retry: binary condition to reorient each item in their insertion evaluation.
    :param stage: number indicating the packing stage, options: [1, 2, 3]
    :param nDst: number of destinations of the cargo.
    :param minDim: minimum size in any dimension (width, height, length) of any item of the cargo.
    :param placedItems: list of items that have been already placed inside the container.
    :return: dictionary with the packed items, non-packed items, current state of the truck and not used potential points.
    """
    discardedPackets = []
    # TODO, try sorting from the front to the rear the potential points in stage 1.
    potentialPoints = potentialPoints if stage == 1 else getMixedPotentialPoints(potentialPoints)
    for i in candidateList:
        # Update average list excluding those items which have been already placed.
        notPlacedMaxWeight = getMaxWeight(candidateList)
        # Using the method as a retryList fill.
        if retry:
            i = reorient(i)
        # Initialization of best point as the worst, in this context the TRR of the truck. And worse fitness value.
        ppBest = [np.array([[truck["width"], truck["height"], truck["length"]]]), 0]
        # Try to get the best PP for an item.
        for pp in potentialPoints[i["dstCode"]]:
            # [condition, item]
            feasibility = isFeasible(pp, placedItems, i, minDim, truck, stage)
            if feasibility[0]:
                ppWithFitness = fitnessFor(pp, feasibility[1], placedItems, notPlacedMaxWeight, truck["height"],
                                           truck["length"], stage, nDst, coefficients)
                if isBetterPP(ppWithFitness, ppBest):
                    ppBest = ppWithFitness
                    feasibleItem = feasibility[1]
        # If the best is different from the worst there is a PP to insert the item.
        if ppBest[1] != 0:
            # Add pp in which the object is inserted.
            feasibleItem["pp_in"] = ppBest[0]
            # Remove pp_best from potentialPoints list.
            potentialPoints[i["dstCode"]] = potentialPoints[i["dstCode"]][
                ~(potentialPoints[i["dstCode"]] == ppBest[0]).all(axis=1)]
            # Generate new PPs to add to item and potentialPoints.
            potentialPoints = projectPPOverlapped(feasibleItem, potentialPoints)
            newPPs = generateNewPPs(feasibleItem, placedItems, truck["height"], truck["width"], minDim, stage)
            feasibleItem["pp_out"] = newPPs
            # Append new potential points to general potential points
            potentialPoints[i["dstCode"]] = np.vstack((potentialPoints[i["dstCode"]], newPPs)) if len(newPPs) else \
                potentialPoints[i["dstCode"]]
            # Add insertion order to item.
            feasibleItem["in_id"] = len(placedItems)
            # Add item to placedItems.
            placedItems.append(feasibleItem)
            # Update truck weight status
            truck = addItemWeightToTruckSubzones(feasibleItem["subzones"], truck)
        else:
            discardedPackets.append(i)
    return {"placed": placedItems, "discard": discardedPackets,
            "truck": truck, "potentialPoints": potentialPoints}


def createNewPPs(placedItems, potentialPoints):
    """
    This function creates new potential point, BRR in last stages.

    :param placedItems: set of placed items that 
    :param potentialPoints: set of potential points from later phases.
    :return: set of potential points with a projection in those that were overlapped.
    """
    for i in placedItems:
        if not isInFloor(i):
            BRR = getBRR(i) + np.array([0, 0, 0.0015])
            if not any(list(map(lambda x: all(BRR == x), i["pp_out"]))):
                # Reduce the scope of items to those sharing their top y-axis Plane with bottom y-axis Plane of the new item.
                sharePlaneItems = list(
                    filter(lambda x: 0 <= abs(getBottomPlaneHeight(i) - getTopPlaneHeight(x)) <= 0.0016, placedItems))
                isBRRinPlane = any(list(map(lambda x: pointInPlane(BRR, getBLF(x), getBRR(x)), sharePlaneItems)))
                if not isBRRinPlane:
                    BRR = getNearestProjectionPointFor(BRR, placedItems)
                potentialPoints[i["dstCode"]] = np.vstack((potentialPoints[i["dstCode"]], BRR))
    return potentialPoints


def checkSubgroupingCondition(packets):
    """
    Check if there is as many subgroup ids as items otherwise there is subgrouping.

    :param packets: list of packets.
    :return: True if there is subgrouping, False otherwise.
    """
    return len(set(map(lambda x: x["subgroupId"], packets))) < len(packets)


def main_cp(truck, candidateList, nDst, coefficients, subgroupingEnabled=1):
    """
    This function is the main part of the core of the solution builder.

    :param subgroupingEnabled: 0 to force omitting subgrouping condition.
    :param truck: truck object.
    :param candidateList: list of objects representing the cargo.
    :param nDst: number of destinations in the cargo.
    :return: dictionary with the packed items, non-packed items, current state of the truck and not used potential points.
    """
    # Map the coefficients.
    coefficientsResorting = coefficients[0:2]
    coefficientsBase = coefficients[2:5]
    coefficientsLoading = coefficients[5:]

    # Fetch the new potential points from the truck.
    potentialPoints = truck["pp"]
    # Add these potential points to the first batch.
    potentialPointsByDst = [potentialPoints]
    minDim = getMinDim(candidateList)

    # Determine if there is relevant subgrouping conditions
    subgrouping = checkSubgroupingCondition(candidateList) if subgroupingEnabled else 0
    stage = 0
    # startTime0 = time.time()
    loadedBase = loadBase(candidateList, potentialPointsByDst, truck, nDst, minDim, [], coefficientsBase)
    # ----- DEBUG-INFO ------
    # print("Time stage " + str(time.time() - startTime0))
    #    print("Number of items packed after stage" + len(fillingBase["placed"]))
    #    startTime1 = time.time()
    # ----- DEBUG-INFO ------

    stage = stage + 1
    loadedS1 = load(reSortingPhase(loadedBase["discard"], loadedBase["placed"], subgrouping, nDst, coefficientsResorting),
                    list(map(lambda x: np.unique(x, axis=0), loadedBase["potentialPoints"])), loadedBase["truck"], 0,
                    stage,
                    nDst, getMinDim(loadedBase["discard"]), loadedBase["placed"], coefficientsLoading)
    newPPs = createNewPPs(loadedS1["placed"], loadedS1["potentialPoints"])
    stage = stage + 1

    # ----- DEBUG-INFO ------
    #    print("Time stage " + str(time.time() - startTime1))
    #    startTime2 = time.time()
    #    print("Number of items packed after stage" + len(filling1["placed"]))
    # ----- DEBUG-INFO ------

    loadingRest = load(reSortingPhase(loadedS1["discard"], loadedS1["placed"], subgrouping, nDst, coefficientsResorting),
                       list(map(lambda x: np.unique(x, axis=0), newPPs)),
                       loadedS1["truck"], 1, stage, nDst,
                       getMinDim(loadedS1["discard"]), loadedS1["placed"], coefficientsLoading)
    # ----- DEBUG-INFO ------
    #    print("Time stage " + str(time.time() - startTime2))
    #    startTime3 = time.time()
    #    print("Number of items packed after stage" + len(filling["placed"]))
    # ----- DEBUG-INFO ------

    stage = stage + 1

    # Got to do a few more tests to check if this additional phase is really relevant.
    # TODO, would be nice to make a estimation of time increase and decide on that instead of this fixed number.
    if len(candidateList) < 300:
        loadingRest = load(loadingRest["discard"],
                           np.unique(loadingRest["potentialPoints"], axis=0),
                           loadingRest["truck"], 1, stage, nDst,
                           getMinDim(loadingRest["discard"]), loadingRest["placed"], coefficientsLoading)
    # ----- DEBUG-INFO ------
    #    print("Number of items packed after stage" + len(fillingSA["placed"]))
    #    print("Stage time: " + str(time.time() - startTime3))
    # ----- DEBUG-INFO ------
    return loadingRest
