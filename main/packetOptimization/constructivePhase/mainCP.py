from main.packetOptimization.constructivePhase.geometryHelpers import *
from main.packetAdapter.helpers import getAverageWeight, getMinDim, getMaxWeight
from main.packetOptimization.randomizationAndSorting.sorting import sortingRefillingPhase
from copy import deepcopy
from scipy.spatial import distance
import random
import numpy as np
import math
import time

np.set_printoptions(suppress=True)


# --------------------- Weight Limit - C1 -------------------------------------------------------------
# This function returns if adding an item does not satisfy weight limit
def isWeightExceeded(placedItems, newItem, truck):
    return sum(list(map(lambda x: x["weight"], placedItems))) + newItem["weight"] > truck["tonnage"]


# This function gives the amount of weight exceeded
def amountWeightExceeded(placedItems, newItem, truck):
    return sum(list(map(lambda x: x["weight"], placedItems))) + newItem["weight"] - truck["tonnage"]


# ----------------- Weight Distribution and load balancing - C2 --------------------------------------
# This function gets subzone length.
def getSubzoneLength(subzones):
    return subzones[0]["brr"][2]


# TODO, we may want to modify the subzones to reduce the difficulty of the constrain and get better solutions. Maybe balance differently.

# This function returns the subzones of a truck.
def getContainerSubzones(truck):
    return truck["subzones"]


# This function returns a list with the subzones the item is in.
def getItemSubzones(item):
    return list(map(lambda x: x[0], item["subzones"]))


# This function returns the percentage of the item for a specified subzone.
def getPercentageOutSubzone(itemBRRz, subzoneBRRz, itemLength):
    return (itemBRRz - subzoneBRRz) / itemLength


# This function returns the amount of subzones needed to fit the part of the item out of its initial zone.
def getNeededExtraSubzonesForItem(subzonesLength, itemLength, outSubzone):
    # Percentage * length(m)
    outzoneItemLength = outSubzone * itemLength
    return outzoneItemLength / subzonesLength


# This function sets in which zones is the item, for those, it returns an array with the id and the percentage of the base in.
# Example 1: item in one zone then [id_zone, percentageIn(1)]
# Example 2: item in two zones then [[id_zone1, p], [id_zone2, (1-p)] ]
def setItemSubzones(subzones, item):
    item_blf_z = getBLF(item)[2]
    item_brr_z = getBRR(item)[2]
    # TODO, this may go inside the for block if the length of the subzones is not equal.
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
            # Decimal number.
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
    item["subzones"] = np.asarray(itemSubzones)
    return item


# This function calculates the weight contribution of an object which has the contactArea for each subzone.
# Input Item Subzone Format: item["subzones"]=[[id_subzone, percentageIn, contactAreaIn],...]
# Output Item Subzone Format: item["subzones"]=[[id_subzone, percentageIn, contactAreaIn, weightIn],...]
def addWeightContributionTo(item):
    itemSubzones = item["subzones"].tolist()
    bottomPlaneArea = getBottomPlaneArea(item)
    for i in itemSubzones:
        # WeightContributionInSubzone = (contactAreaIn/totalArea) * weight
        # Is not the same the contactAreaIn than the percentage because not all the percentage may be supported nor in contact.
        i.append((i[2] / bottomPlaneArea) * item["weight"])
    item["subzones"] = np.asarray(itemSubzones)
    return item


# This function adds the item weight to the global truck weight and to each subzone.
def addItemWeightToTruckSubzones(itemSubzones, truck):
    for j in truck["subzones"]:
        for i in itemSubzones:
            if i[0] == j["id"]:
                j["weight"] = j["weight"] + i[3]
    return truck


# This function returns a ndarray with the modified item and true if not any weight limit of a subzone is exceeded, false otherwise.
# If the item is in the floor the weight contribution is direct to a subzone.
# If the item is on top of others the weight contribution to a subzone is proportional to the bottom Plane in contact of the item.
# Output Format: [condition, item]
def itemContributionExceedsSubzonesWeightLimit(item, truckSubzones):
    # This list stores the state of the condition for each subzone.
    weightNotExceeded = []
    # Once known the contribution area(contactAreaIn), supposing an homogeneous density, calculate the weight contribution.
    itemWithWeightContribution = addWeightContributionTo(item)
    # Check if for each subzone the weight is exceeded.
    for i in item["subzones"]:
        weightNotExceeded.append(all(list(filter(lambda x: x is not None, map(
            lambda x: (i[3] + x["weight"]) <= x["weight_limit"] if i[0] == x["id"] else None,
            truckSubzones)))))
    return np.array([[weightNotExceeded[0], itemWithWeightContribution]])


# ------------------ Stackability - C5 ---------------------------------------------
# This function returns true if a item is stackable, false otherwise.
# An item is stackable if the contributions of weight for every object underneath does not exceed certain conditions.
def isStackable(item, placedItems):
    # Reduce the scope of items to those sharing their top y Plane with bottom y Plane of the new item.
    sharePlaneItems = list(
        filter(lambda x: 0 <= abs(getBottomPlaneHeight(item) - getTopPlaneHeight(x)) <= 0.00151, placedItems))
    # This ndarray will store if the conditions are met for every item the newItem is above.
    stackableForSharePlaneItems = []
    for i in sharePlaneItems:
        # % of area between the newItem and the placed items underneath * newItem["weight"]
        itemWeightContribution = (getIntersectionArea(i, item) / getBottomPlaneArea(item)) * item["weight"]
        # Portion of weight above fragile item cannot be more than 50% of the weight of the fragile item.
        if i["breakability"] and itemWeightContribution <= 0.5 * i["weight"]:
            stackableForSharePlaneItems.append(True)
        elif not i["breakability"] and itemWeightContribution <= i["weight"]:
            stackableForSharePlaneItems.append(True)
        else:
            stackableForSharePlaneItems.append(False)
    return np.all(np.asarray(stackableForSharePlaneItems))


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
# This function returns the item modified including the contact area in each subzone for it.
# Input Item Subzone Format: [[id_subzone, percentageIn],...]
# Output Item Subzone Format: [[id_subzone, percentageIn, contactAreaIn],...]
def addContactAreaTo(item, placedItems):
    newItem = deepcopy(item)
    itemSubzones = deepcopy(item["subzones"].tolist())
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
            totalContactAreaInSubzone = sum(list(map(lambda x: getIntersectionArea(x, item), sharePlaneItems))) * i[1]
        # For each subzone the item is in we also have the contact area which is not the same as the percentage within the subzone.
        i.append(totalContactAreaInSubzone)
    newItem["subzones"] = np.asarray(itemSubzones)
    return newItem


# This function returns a ndarray with the item and True if the item has at least 80% of supported area, False otherwise.
def isStable(item, placedItems, stage):
    threshold = 0.8 if stage == 1 else 0.75
    itemWithContactArea = addContactAreaTo(item, placedItems)
    totalItemContactArea = sum(list(map(lambda x: x[2], itemWithContactArea["subzones"])))
    contactAreaPercentage = totalItemContactArea / getBottomPlaneArea(item)
    if contactAreaPercentage >= threshold:
        return np.array([[1, itemWithContactArea]])
    return np.array([[0, itemWithContactArea]])


# ------------------ Physical constrains - Truck-related ----------------------------------------
# This function returns True if the packet inserted in a potentialPoint does not exceed the length of the truck, False otherwise.
def isWithinTruckLengthAux(item):
    return item["lengthFitting"]


# This function returns True if the packet inserted in a potentialPoint does not exceed the length of the truck, False otherwise.
def isWithinTruckLength(item, truckLength):
    return getBRR(item)[2] <= truckLength


# This function returns True if the packet inserted in a potentialPoint does not exceed the width of the truck, False otherwise.
def isWithinTruckWidth(item, truckWidth):
    return getBRR(item)[0] <= truckWidth


# This function returns True if the packet inserted in a potentialPoint does not exceed the height of the truck, False otherwise.
def isWithinTruckHeight(item, truckHeight):
    return getTopPlaneHeight(item) <= truckHeight


# This function returns True if dimension constrains are met, False otherwise.
def isWithinTruckDimensionsConstrains(item, truckDimensions):
    return isWithinTruckLength(item, truckDimensions["length"]) \
           and isWithinTruckWidth(item, truckDimensions["width"]) \
           and isWithinTruckHeight(item, truckDimensions["height"])


# ------------------ Physical constrains - Items-related ----------------------------------------
def overlapper(p1all, p2all):
    """
    This function checks whether an item overlaps other or not.

    :param p1all: tuple of 3 planes,
    :param p2all:
    :return: True if the item overlaps the polyItem, False otherwise.
    """
    for i, j in zip(p1all, p2all):
        if generalIntersectionArea(i, j):
            continue
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
        ndxDistances = distance.cdist(massCenter.reshape((1, 3)), itemsMCs, 'euclidean').argsort()[0]
        # Get the nearest mass centers and its items.
        nearestMCs = itemsMCs[ndxDistances[:min(len(placedItems), amountOfNearItems)]]
        nearItems = list(
            filter(lambda x: any((list(map(lambda y: all(y == x["mass_center"]), nearestMCs)))), placedItems))
        return nearItems
    return []


def isNotOverlapping(item, placedItems):
    """
    This function checks if an item is overlapping others and vice versa.

    :param item: item object.
    :param placedItems: list of placed item objects.
    :return: True if the item does not overlap other items around it, False otherwise.
    """
    if len(placedItems):
        nearItems = getSurroundingItems(item["mass_center"].reshape(1, 3), placedItems, 10)
        # Generate points for item evaluated.
        p1all = getPlanesFor(item)
        # Validate overlapping conditions item vs. placedItems and vice versa.
        itemToNearItemsNotOverlapping = all(list(map(lambda x: overlapper(p1all, getPlanesFor(x)), nearItems)))
        return itemToNearItemsNotOverlapping
    else:
        return True


def physicalConstrains(placedItems, item, truck):
    return not isWeightExceeded(placedItems, item, truck) \
           and isWithinTruckDimensionsConstrains(item, {"width": truck["width"], "height": truck["height"],
                                                        "length": truck["length"]}) \
           and isADRSuitable(item, getTruckBRR(truck)[2]) \
           and isNotOverlapping(item, placedItems)


# --------------------- Helpers to the main module function -----------------------------------
# This function checks if a potential point is feasible for placing the item, meaning it satisfies all the conditions.
# Returns the state of feasibility condition and the item after processing it for all the constrains.
def isFeasible(potentialPoint, placedItems, newItem, minDim, truck, stage):
    item = setItemMassCenter(newItem, potentialPoint, truck["width"], minDim)

    # Conditions to be checked sequentially to improve performance.
    if physicalConstrains(placedItems, item, truck):
        truckSubzones = getContainerSubzones(truck)
        itemWithSubzones = setItemSubzones(truckSubzones, item)
        # This item is [condition, itemWithContactAreaForEachSubzone]
        i3WithCondition = isStable(itemWithSubzones, placedItems, stage)
        # Checks if it is stable and stackable.
        if i3WithCondition[0][0] and isStackable(item, placedItems):
            # Way of keeping the modified object and if the condition state.
            i4WithCondition = itemContributionExceedsSubzonesWeightLimit(i3WithCondition[0][1], truckSubzones)
            if i4WithCondition[0][0]:
                return np.array([[1, i4WithCondition[0][1]]])
            else:
                return np.array([[0, newItem]])
        else:
            return np.array([[0, newItem]])
    else:
        return np.array([[0, newItem]])


def areaConstraint(currentAreas, maxAreas, item):
    return currentAreas[0][item["dst_code"]] + getBottomPlaneArea(item) <= maxAreas[item["dst_code"]]


def feasibleInStage0(potentialPoint, placedItems, newItem, currentAreas, maxAreas, minDim, truck):
    item = setItemMassCenter(newItem, potentialPoint, truck["width"], minDim)

    if areaConstraint(currentAreas, maxAreas, item):
        if physicalConstrains(placedItems, item, truck):
            truckSubzones = getContainerSubzones(truck)
            itemWithSubzones = setItemSubzones(truckSubzones, item)
            # This item is [condition, itemWithContactAreaForEachSubzone]
            i3WithCondition = isStable(itemWithSubzones, placedItems, 0)
            # Checks if it is stable and stackable.
            if i3WithCondition[0][0]:
                # Way of keeping the modified object and if the condition state.
                i4WithCondition = itemContributionExceedsSubzonesWeightLimit(i3WithCondition[0][1], truckSubzones)
                if i4WithCondition[0][0]:
                    return np.array([[1, i4WithCondition[0][1]]])
                else:
                    return np.array([[0, newItem]])
            else:
                return np.array([[0, newItem]])
        return np.array([[0, newItem]])
    return np.array([[0, newItem]])


def areEnoughPlacedItemsOfTheCstCode(dst_code, placedItems, nItems):
    """
    This function checks whether there are enough items with a customer code.
    :param dst_code: The customer code to be checked.
    :param placedItems: Set of items already placed in the container.
    :param nItems: Threshold of items.
    :return: True if there are more items placed than the threshold for the same customer.
    """
    return len(list(filter(lambda x: dst_code == x["dst_code"], placedItems))) >= nItems


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
            filter(lambda x: x["dst_code"] == item["dst_code"], nearItems))
        if not areEnoughPlacedItemsOfTheCstCode(item["dst_code"], placedItems, nItems):
            surroundingCondition = 1 - item["dst_code"] / (nDst - 1)
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
        itemBehindCondition = int(itemBehind["dst_code"] == item["dst_code"])

        if stage == 3:
            surroundingCondition = -stageFW[3] if item["dst_code"] < itemBehind["dst_code"] else surroundingCondition
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


def fitnessForStage0(PP, item, truck, nDst, placedItems, maxWeight):
    fitWeights = [0.3, 0.3, 0.4] if nDst > 1 else [0.5, 0.5, 0]
    if nDst > 1:
        # For the surrounding customer code objects.
        nItems = 5
        nearItems = getSurroundingItems(item["mass_center"], placedItems, nItems)
        # Consider valid dst code the same or the previous.
        nearItemsWithValidDstCode = list(
            filter(lambda x: x["dst_code"] == item["dst_code"] or x["dst_code"] == item["dst_code"] + 1,
                   nearItems)) if nDst > 2 else list(
            filter(lambda x: x["dst_code"] == item["dst_code"], nearItems))
        if not areEnoughPlacedItemsOfTheCstCode(item["dst_code"], placedItems, nItems):
            surroundingCondition = 1 - item["dst_code"] / (nDst - 1)
        elif len(nearItemsWithValidDstCode) <= 1:
            surroundingCondition = -0.30
        else:
            surroundingCondition = len(nearItemsWithValidDstCode) / max(len(nearItems), 1)
    else:
        surroundingCondition = 0
    fitnessValue = (1 - PP[2] / truck["length"]) * fitWeights[0] \
                   + (item["weight"] / maxWeight) * fitWeights[1] + surroundingCondition * fitWeights[2]
    return np.concatenate((PP, np.array([fitnessValue])))


def isBetterPP(newPP, currentBest):
    """
    This function decide which potential point is better. Criteria is:
    - Give same fitness, randomly choose one.
    - Choose the one with the best fitness value.
    :param newPP: potential point being evaluated.
    :param currentBest: current potential point for an item.
    :return: True if the newPP is better than the current best, False otherwise.
    """
    if newPP[3] == currentBest[3]:
        return random.getrandbits(1)
    return newPP[3] > currentBest[3]


def projectPPOverlapped(item, potentialPoints, placedItems):
    potentialPointsOverlapped = list(filter(lambda x: pointInPlane(x, getBLF(item), getBRR(item)), potentialPoints.tolist()))
    newPotentialPoints = list(filter(lambda x: x not in potentialPointsOverlapped, deepcopy(potentialPoints.tolist())))
    for p in potentialPointsOverlapped:
        ppOut = list(map(lambda x: list(filter(lambda y: all(y == p), x["pp_out"])), placedItems))
        p[1] = getTopPlaneHeight(item) + 0.0015
        ppOut[1] = p[1]
        newPotentialPoints.append(p)
    return newPotentialPoints


# This function creates a list of potential points generated after inserting an item.
# Output format: [[TLF],[BLR],[BxF]]
def generateNewPPs(item, placedItems, truckHeight, truckWidth, minDim, stage):
    # Add margin to z-coordinate.
    BLR = getBLR(item) + np.array([0, 0, 0.0015])
    # BRR if x >= truckWidth - minDim aprox, BRF otherwise
    BRF = getBRF(item) + np.array([0.0015, 0, 0])
    BRx = getBRR(item) + np.array([0, 0, 0.0015]) if BRF[0] >= truckWidth - minDim else BRF
    TLF = getTLF(item) + np.array([0, 0.0015, 0])
    TRF = getTRF(item) + np.array([0, 0.0015, 0])
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


def fillListStage0(candidateList, potentialPoints, truck, nDst, minDim, placedItems):
    # Fill number of items per destination.
    nItemDst = []
    for n in range(nDst):
        nItemDst.append(len(list(filter(lambda x: x["dst_code"] == n, candidateList))))
    # Average weight of candidateList.
    avgGeneral = getAverageWeight(candidateList)
    # Filter the candidates for each destination that satisfy a condition.
    filteredCandidates = []
    for d in list(range(nDst)):
        filteredCandidates = filteredCandidates + list(
            filter(lambda x: x["dst_code"] == d and x["weight"] >= avgGeneral*0.5, candidateList))
    # Count amount of filtered for each destination.
    nFilteredDst = list(
        map(lambda x: len(list(filter(lambda y: y["dst_code"] == x, filteredCandidates))), list(range(nDst))))
    # Group items that did not pass the filter.
    discardList = list(filter(lambda x: x not in filteredCandidates, candidateList))
    # Update list with the items that passed the filter.
    candidateList = filteredCandidates
    # Create max area items of a destination can occupy within the container.
    maxAreas = generateMaxArea(nItemDst, nFilteredDst, truck, nDst)
    # Initialize current areas.
    currentAreas = np.zeros((1, nDst))
    # Obtain the maximum weight of the candidatelist.
    maxWeight = getMaxWeight(candidateList)
    # Create new list for discarded PP.
    discardedPP = []
    # Auxiliary list to group PP that are not important in this stage(those that are not in the floor).
    notInFloorPP = []
    # Check the best item for each Potential Point in order of destination.
    for d in range(nDst):
        # Select corresponding variables to destination.
        currentArea = currentAreas[0][d]
        maxArea = maxAreas[d]
        # The intention is to fill the max area of the container assigned to a destination,
        # so it checks this condition for each potential point, each item and each item orientation.
        while (currentArea <= maxArea) and len(potentialPoints):
            # Check if there is no item that satisfies full filling without exceeding max allowed area.
            if not any(list(map(lambda x: getBottomPlaneArea(x) + currentArea <= maxArea, candidateList))):
                break
            # Initialization of best point as the worst, in this context the TRR of the truck. And worse fitness value.
            ppBest = np.array([truck["width"], truck["height"], truck["length"], 0])
            # Get the potential point with lower z-coordinate (closest to the front of the container).
            pp = sorted(potentialPoints, key=lambda x: x[2])[0]
            # Only proceed with the search if the item is in the floor.
            if not pp[1]:
                for i in candidateList:
                    # Pick one random orientation apart from the current.
                    orientations = [i["orientation"], random.choice([o for o in i["f_orient"] if o != i["orientation"]])]
                    for o in orientations:
                        if o != i["orientation"]:
                            i = changeItemOrientation(i, [o])
                        # Try to get the best PP for an item.
                        # [condition, item]
                        feasibility = feasibleInStage0(pp, placedItems, i, currentAreas, maxAreas, minDim, truck)
                        if feasibility[0][0]:
                            ppWithFitness = fitnessForStage0(pp, feasibility[0][1], truck, nDst, placedItems, maxWeight)
                            if isBetterPP(ppWithFitness, ppBest):
                                ppBest = ppWithFitness
                                feasibleItem = feasibility[0][1]
                        # This condition is only important for the first two items.
                        if ppBest[3] == 1:
                            break
                # If the best is different from the worst there is a PP to insert the item.
                if ppBest[3] != 0:
                    currentAreas[0][feasibleItem["dst_code"]] = currentAreas[0][
                                                                    feasibleItem["dst_code"]] + getBottomPlaneArea(
                        feasibleItem)
                    # Add pp in which the object is inserted.
                    feasibleItem["pp_in"] = ppBest[0:3]
                    # Remove item from candidate list.
                    candidateList = list(filter(lambda x: feasibleItem["id"] != x["id"], candidateList))
                    # Remove pp_best from potentialPoints list.
                    potentialPoints = np.array(list(filter(lambda x: any(x != ppBest[0:3]), potentialPoints)))
                    # Generate new PPs to add to item and potentialPoints.
                    newPPs = generateNewPPs(feasibleItem, placedItems, truck["height"], truck["width"], minDim, 0)
                    feasibleItem["pp_out"] = newPPs
                    potentialPoints = np.vstack((potentialPoints, newPPs)) if len(newPPs) else potentialPoints
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
    discardList = discardList + candidateList
    # Keep the potential points that are not in the floor(which should be full).
    potentialPoints = np.asarray(notInFloorPP)
    return {"placed": placedItems, "discard": discardList,
            "truck": truck, "potentialPoints": potentialPoints}


# This function creates a solution from a list of packets and a given potential points
def fillList(candidateList, potentialPoints, truck, retry, stage, nDst, minDim, placedItems):
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
            if feasibility[0][0]:
                ppWithFitness = fitnessFor(pp, feasibility[0][1], placedItems, notPlacedMaxWeight, truck["height"],
                                           truck["length"], stage, nDst)
                if isBetterPP(ppWithFitness, ppBest):
                    ppBest = ppWithFitness
                    feasibleItem = feasibility[0][1]
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


# This function is the main function of the module M2_2
def main_cp(truck, candidateList, nDst):
    potentialPoints = truck["pp"]
    minDim = getMinDim(candidateList)
    stage = 0
#    startTime0 = time.time()
    filling0 = fillListStage0(candidateList, potentialPoints, truck, nDst, minDim, [])
#    print("Time stage " + str(time.time() - startTime0))
#    print(len(filling0["placed"]))

    stage = stage + 1
#    startTime1 = time.time()
    filling1 = fillList(sortingRefillingPhase(filling0["discard"], nDst),
                        np.unique(filling0["potentialPoints"], axis=0), truck, 0, stage,
                        nDst, getMinDim(filling0["discard"]), filling0["placed"])
#    print("Time stage " + str(time.time() - startTime1))
    newPPs = createAndProjectNewPPs(filling1["placed"], filling1["potentialPoints"])
    stage = stage + 1
#    startTime2 = time.time()
#    print(len(filling1["placed"]))
    filling = fillList(filling1["discard"],
                        np.unique(newPPs, axis=0),
                        filling1["truck"], 1, stage, nDst,
                        getMinDim(filling1["discard"]), filling1["placed"])
#    print("Time stage " + str(time.time() - startTime2))
    stage = stage + 1
#    startTime3 = time.time()
#    print(len(filling["placed"]))
    if len(candidateList) < 300:
        filling = fillList(filling["discard"],
                            np.unique(filling["potentialPoints"], axis=0),
                            filling["truck"], 1, stage, nDst,
                            getMinDim(filling["discard"]), filling["placed"])
#    print(len(filling["placed"]))
#    print("Time stage " + str(time.time() - startTime3))
    return filling
