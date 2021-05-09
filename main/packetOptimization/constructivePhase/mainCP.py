from main.packetOptimization.constructivePhase.geometryHelpers import *
from main.packetAdapter.helpers import getAverageWeight
from main.packetOptimization.randomizationAndSorting.sorting import sortingRefillingPhase
from copy import deepcopy
from scipy.spatial import Delaunay
import random
import numpy as np
import math
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
    weightNotExceeded = np.array((), dtype=bool)
    # Once known the contribution area(contactAreaIn), supposing an homogeneous density, calculate the weight contribution.
    itemWithWeightContribution = addWeightContributionTo(item)
    if isInFloor(item):
        # Check if for each subzone the weight is exceeded.
        for i in item["subzones"]:
            weightNotExceeded = np.array(np.append(weightNotExceeded, list(filter(lambda x: x is not None, map(
                lambda x: (i[1] * item["weight"] + x["weight"]) <= x["weight_limit"] if i[0] == x["id"] else None,
                truckSubzones)))))
    else:
        for i in itemWithWeightContribution["subzones"]:
            # Check if adding the weight to the subzone current weight exceeds its limit.
            weightNotExceeded = np.array(np.append(weightNotExceeded, list(filter(lambda x: x is not None, map(
                lambda x: (i[3] + x["weight"]) <= x["weight_limit"] if i[0] == x["id"] else None, truckSubzones)))))
    return np.array([[all(weightNotExceeded), itemWithWeightContribution]])


# ------------------ Stackability - C5 ---------------------------------------------
# This function returns true if a item is stackable, false otherwise.
# An item is stackable if the contributions of weight for every object underneath does not exceed certain conditions.
def isStackable(item, averageWeight, placedItems):
    if isInFloor(item):
        # For a optimum solution it is better to reward the algorithm to put the weightier items on the floor.
        # TODO, changed this because it is considered in betterPP
        return item["weight"] > 1.2 * averageWeight
    else:
        # TODO, we may want to change this to take into account accumulated weight(i.e 2 packets above another)
        # Reduce the scope of items to those sharing their top y Plane with bottom y Plane of the new item.
        sharePlaneItems = list(filter(lambda x: 0 <= abs(getBottomPlaneHeight(item) - getTopPlaneHeight(x)) <= 0.003, placedItems))
        # This ndarray will store if the conditions are met for every item the newItem is above.
        stackableForSharePlaneItems = np.array([], dtype=bool)
        for i in sharePlaneItems:
            # % of area between the newItem and the placed items underneath * newItem["weight"]
            itemWeightContribution = (getIntersectionArea(i, item) / getBottomPlaneArea(item)) * item["weight"]
            # Portion of weight above fragile item cannot be more than 50% of the weight of the fragile item.
            if i["breakability"] and itemWeightContribution <= 0.5 * i["weight"]:
                stackableForSharePlaneItems = np.append(stackableForSharePlaneItems, True)
            elif not i["breakability"] and itemWeightContribution <= i["weight"]:
                stackableForSharePlaneItems = np.append(stackableForSharePlaneItems, True)
            else:
                stackableForSharePlaneItems = np.append(stackableForSharePlaneItems, False)
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

# This function returns the item modified including the contact area in each subzone for it.
# Input Item Subzone Format: [[id_subzone, percentageIn],...]
# Output Item Subzone Format: [[id_subzone, percentageIn, contactAreaIn],...]
def addContactAreaTo(item, placedItems):
    newItem = deepcopy(item)
    newItem["subzones"] = np.array([[]])
    # Go over the subzones the item is in.
    for i in range(item["subzones"].shape[0]):
        if isInFloor(item):
            totalContactAreaInSubzone = getBottomPlaneArea(item) * item["subzones"][i][1]
        else:
            # Reduce the scope of items to those in the same subzone
            placedItemsSubzone = list(filter(lambda x: item["subzones"][i][0] in getItemSubzones(x), placedItems))
            # Reduce the scope of items to those sharing their top y-axis Plane with bottom y-axis Plane of the new item.
            sharePlaneItems = list(
                filter(lambda x: 0 <= abs(getBottomPlaneHeight(item) - getTopPlaneHeight(x)) <= 0.003,
                       placedItemsSubzone))
            # Calculate the area of intersection between the sharedPlaneItems and the new item in a subzone.
            totalContactAreaInSubzone = sum(list(map(lambda x: getIntersectionArea(x, item), sharePlaneItems))) * item["subzones"][i][1]
        # For each subzone the item is in we also have the contact area which is not the same as the percentage within the subzone.
        if i == 0:
            newItem["subzones"] = np.array([np.append(item["subzones"][i], np.array([[totalContactAreaInSubzone]]))])
        else:
            newItem["subzones"] = np.vstack(
                (newItem["subzones"], np.append(item["subzones"][i], np.array([[totalContactAreaInSubzone]]))))
    return newItem


# This function returns a ndarray with the item and True if the item has at least 80% of supported area, False otherwise.
def isStable(item, placedItems):
    itemWithContactArea = addContactAreaTo(item, placedItems)
    totalItemContactArea = sum(list(map(lambda x: x[2], itemWithContactArea["subzones"])))
    contactAreaPercentage = totalItemContactArea / getBottomPlaneArea(item)
    if contactAreaPercentage > 0.8:
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
# This function returns a ndarray with all the vertices of an item.
def generatePointsFrom(item):
    return np.array([getBLF(item), getTLF(item), getTRF(item), getBRF(item),
                     getBRR(item), getBLR(item), getTRR(item), getTLR(item),
                     getMCFront(item), getMCFront(item), item["mass_center"]])


# This function returns True if none of the vertices of pointsItem is inside of a polyItem.
def overlapper(itemPoints, polyItemPoints):
    return all(list(map(lambda x: x == -1,
                        Delaunay(polyItemPoints).find_simplex(itemPoints))))


# This function returns a list with specified length around the massCenter.
def getSurroundingItems(massCenter, placedItems, amountOfNearItems):
    if placedItems:
        # Extract the mass center of all placed items.
        itemsMCs = np.array(list(map(lambda x: x["mass_center"], placedItems)))
        # Compute and sort the distances between the new item mass center and the rest.
        distances = ((itemsMCs - massCenter) ** 2).sum(axis=1)
        ndx = distances.argsort()
        # Get the nearest mass centers and its items.
        nearestMCs = itemsMCs[ndx[:min(len(placedItems), amountOfNearItems)]]
        nearItems = list(filter(lambda x: any((list(map(lambda y: all(y == x["mass_center"]), nearestMCs)))), placedItems))
        return nearItems
    return []


# TODO, may be overlapping issues between items for those PP which are the projection of some extreme points which are in a exceeding area.
# This function returns True if the item does not overlap other items around it, False otherwise.
def isNotOverlapping(item, placedItems):
    if len(placedItems):
        nearItems = getSurroundingItems(item["mass_center"], placedItems, 8)
        # Generate points for item evaluated.
        itemAsPoints = generatePointsFrom(item)
        # Validate overlapping conditions item vs. placedItems and vice versa.
        itemToNearItemsOverlapping = all(list(map(lambda x: overlapper(itemAsPoints, generatePointsFrom(x)), nearItems)))
        nearItemsOverlappingItem = all(list(map(lambda x: overlapper(generatePointsFrom(x), itemAsPoints), nearItems)))
        return itemToNearItemsOverlapping and nearItemsOverlappingItem
    else:
        return True


# --------------------- Helpers to the main module function -----------------------------------
# This function checks if a potential point is feasible for placing the item, meaning it satisfies all the conditions.
# Returns the state of feasibility condition and the item after processing it for all the constrains.
def isFeasible(potentialPoint, placedItems, newItem, candidateListAverageWeight, truck):
    item = setItemMassCenter(newItem, potentialPoint, truck["width"])
    # Conditions to be checked sequentially to improve performance.
    if not isWeightExceeded(placedItems, item, truck) \
            and isWithinTruckDimensionsConstrains(item, truck["dimensions"]) \
            and isADRSuitable(item, getTruckBRR(truck)[2]) \
            and isNotOverlapping(item, placedItems):
        truckSubzones = getContainerSubzones(truck)
        itemWithSubzones = setItemSubzones(truckSubzones, item)
        # This item is [condition, itemWithContactAreaForEachSubzone]
        i3WithCondition = isStable(itemWithSubzones, placedItems)
        # Checks if it is stable and stackable.
        if i3WithCondition[0][0] and isStackable(item, candidateListAverageWeight, placedItems):
            # Way of keeping the modified object and if the condition state. TODO, maybe is not necessary to keep the item.
            i4WithCondition = itemContributionExceedsSubzonesWeightLimit(i3WithCondition[0][1], truckSubzones)
            if i4WithCondition[0][0]:
                return np.array([[1, i4WithCondition[0][1]]])
            else:
                return np.array([[0, newItem]])
        else:
            return np.array([[0, newItem]])
    else:
        return np.array([[0, newItem]])


# This function computes the fitness value for a potential point.
# PP format [x, y, z, fitnessValue]
def fitnessFor(PP, item, placedItems, avgWeight, maxHeight, maxLength):
    # Common conditions in the fitness function.
    lengthCondition = 1 - (PP[2] / maxLength)
    # For the surrounding customer code objects.
    nearItems = getSurroundingItems(item["mass_center"], placedItems, 5)
    nearItemsWithSameDstCode = list(filter(lambda x: x["dst_code"] == item["dst_code"], nearItems))
    surroundingCondition = len(nearItemsWithSameDstCode) / max(len(nearItems), 1)
    heightWeightRelation = (1 - (item["height"] / maxHeight) / item["weight"] / avgWeight)

    # Item not in floor.
    if PP[1]:
        itemBehind = list(filter(lambda x: any(list(map(lambda y: all(y == PP), x["pp_out"]))), placedItems))[0]
        areaCondition = abs(getBottomPlaneArea(item)/getBottomPlaneArea(itemBehind) - 1)
        return np.concatenate((PP,
                               np.array([lengthCondition*0.4 + surroundingCondition*0.3 + areaCondition*0.1 + heightWeightRelation*0.2])))
    else:
        return np.concatenate((PP,
                               np.array([lengthCondition*0.4 + surroundingCondition*0.3 + 0.1 + heightWeightRelation*0.2])))


# This function returns if the new potential point is better than the former based on a fitness function value.
def isBetterPP(newPP, currentBest):
    if newPP[3] == currentBest[3]:
        return random.getrandbits(1)
    return newPP[3] > currentBest[3]


# This function creates a list of potential points generated after inserting an item.
# Output format: [[TLF],[BLR],[BRF]]
def generateNewPPs(item, placedItems):
    # Add margin to the point of the surface.
    BLR = getBLR(item) + np.array([0, 0, 0.003])
    BRF = getBRF(item) + np.array([0.003, 0, 0])
    TLF = getTLF(item) + np.array([0, 0.003, 0])
    result = np.array([TLF])
    if isInFloor(item):
        result = np.vstack((result, BLR, BRF))
    else:
        # Reduce the scope of items to those sharing their top y-axis Plane with bottom y-axis Plane of the new item.
        sharePlaneItems = list(
            filter(lambda x: 0 <= abs(getBottomPlaneHeight(item) - getTopPlaneHeight(x)) <= 0.003, placedItems))
        # Check which points are not supported.
        isBLRinPlane = any(list(map(lambda x: pointInPlane(BLR, getBLF(x), getBRR(x)), sharePlaneItems)))
        isBRFinPlane = any(list(map(lambda x: pointInPlane(BRF, getBLF(x), getBRR(x)), sharePlaneItems)))
        # Modify not supported points to its projection.
        if not isBRFinPlane:
            BRF = getNearestProjectionPointFor(BRF, placedItems)
        if not isBLRinPlane:
            BLR = getNearestProjectionPointFor(BLR, placedItems)
        result = np.vstack((result, BLR, BRF))
    return result


# This function creates a solution from a list of packets and a given potential points
def fillList(candidateList, potentialPoints, truck, retry, placedItems):
    discardList = []
    for i in candidateList:
        # Update average list excluding those items which have been already placed.
        notPlacedAvgWeight = getAverageWeight(list(filter(lambda x: x not in placedItems, candidateList)))
        # Using the method as a retryList fill.
        if retry:
            i = reorient(i)
        # Initialization of best point as be the worst, in this context the TRR of the truck. And worse fitness value.
        ppBest = np.array([truck["width"], truck["height"], truck["length"], 0])
        # Try to get the best PP for an item.
        for pp in potentialPoints:
            # [condition, item]
            feasibility = isFeasible(pp, placedItems, i, notPlacedAvgWeight, truck)
            if feasibility[0][0]:
                ppWithFitness = fitnessFor(pp, feasibility[0][1], placedItems, notPlacedAvgWeight, truck["height"], truck["length"])
                if isBetterPP(ppWithFitness, ppBest):
                    ppBest = ppWithFitness
                    feasibleItem = feasibility[0][1]
        # If the best is different from the worst there is a PP to insert the item.
        if ppBest[3] != 0:
            # Add pp in which the object is inserted.
            feasibleItem["pp_in"] = ppBest
            # Remove pp_best from potentialPoints list.
            potentialPoints = np.array(list(filter(lambda x: any(x != ppBest[0:3]), potentialPoints)))
            # Generate new PPs to add to item and potentialPoints.
            newPPs = generateNewPPs(feasibleItem, placedItems)
            feasibleItem["pp_out"] = newPPs
            potentialPoints = np.vstack((potentialPoints, newPPs))
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


# This function is the main function of the module M2_2
def main_cp(truck, candidateList):
    potentialPoints = truck["pp"]
    filling = fillList(candidateList, potentialPoints, truck, 0, [])
    discardedResorted = sortingRefillingPhase(filling["discard"])
    refilling = fillList(discardedResorted, filling["potentialPoints"],
                         filling["truck"], 1, filling["placed"])
    return refilling
