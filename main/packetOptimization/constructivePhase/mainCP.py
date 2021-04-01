import numpy as np
import math
from main.packetOptimization.constructivePhase.geometryHelpers import *
from copy import deepcopy
from scipy.spatial import Delaunay


# --------------------- Weight Limit - C1 -------------------------------------------------------------
# This function returns if adding an item does not satisfy weight limit
def isWeightExceeded(placedItems, newItem, truck):
    if sum(list(map(lambda x: x["weight"], placedItems))) + newItem["weight"] > truck["tonnage"]:
        return True
    return False


# This function gives the amount of weight exceeded
def amountWeightExceeded(placedItems, newItem, truck):
    return sum(list(map(lambda x: x["weight"], placedItems))) + newItem["weight"] - truck["tonnage"]


# ----------------- Weight Distribution and load balancing - C2 --------------------------------------
# This function gets subzone length.
def getSubzoneLength(subzones):
    return subzones[0]["blf"][2]


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
    outzoneItemLength = outSubzone * itemLength
    neededSubzones = outzoneItemLength / subzonesLength
    return neededSubzones


# This function sets in which zones is the item, for those, it returns an array with the id and the percentage of the base in.
# Example 1: item in one zone then [id_zone, percentageIn(1)]
# Example 2: item in two zones then [[id_zone1, p], [id_zone2, (1-p)] ]
def setItemSubzones(subzones, item):
    item_blf_z = getBLF(item)[2]
    item_brr_z = getBRR(item)[2]
    subzonesLength = getSubzoneLength(subzones)
    item["subzones"] = None
    for i in range(len(subzones)):  # TODO, Se puede reformar este for
        # Check if it fits completely in one subzone.
        if subzones[i]["blf"][2] <= item_blf_z and subzones[i]["brr"][2] >= item_brr_z:
            item["subzones"] = np.array([i + 1, 1])
            break
        # Get if the blf of an item is within the subzone, and include needed extra subzones.
        elif subzones[i]["blf"][2] <= item_blf_z < subzones[i]["brr"][2]:
            outSubzone = getPercentageOutSubzone(item_brr_z, subzones[i]["brr"][2], item["length"])
            # Decimal number.
            neededExtraSubzonesForItem = getNeededExtraSubzonesForItem(subzonesLength, item["length"], outSubzone)
            # First subzone the item is in.
            item["subzones"] = np.array([subzones[i]["id"], 1 - outSubzone])
            for s in range(1, math.ceil(neededExtraSubzonesForItem) + 1):
                # Needed to calculate the percentage in the last subzone the item is in.
                if s == (math.ceil(neededExtraSubzonesForItem) + 1):
                    # PercentageIn = subzoneLength*(decimalExtraSubzones - floorRoundedSubzones)/itemLength
                    item["subzones"] = np.vstack((item["subzones"], np.array([subzones[i]["id"] + s, (subzonesLength * (
                            neededExtraSubzonesForItem - math.floor(neededExtraSubzonesForItem))) / item[
                                                                                  "length"]])))
                # In case the item is in more than 2 subzones.
                else:
                    item["subzones"] = np.vstack(
                        (item["subzones"], np.array([subzones[i]["id"] + s, subzonesLength / item["length"]])))
        else:
            break
    return item


# This function calculates the weight contribution of an object which has the contactArea for each subzone.
# Input Item Subzone Format: item["subzones"]=[[id_subzone, percentageIn, contactAreaIn],...]
# Output Item Subzone Format: item["subzones"]=[[id_subzone, percentageIn, contactAreaIn, weightIn],...]
def addWeightContributionTo(item):
    newItem = deepcopy(item)
    newItem["subzones"] = np.array(())
    bottomPlaneArea = getBottomPlaneArea(item)
    for i in range(item["subzones"].shape[0]):
        # WeightContributionInSubzone = (contactAreaIn/totalArea) * weight
        # Is not the same the contactAreaIn than the percentage because not all the percentage may be supported, thus in contact.
        if i == 0:
            newItem["subzones"] = np.append(item["subzones"][i],
                                            np.array([(item["subzones"][i][2] / bottomPlaneArea) * item["weight"]]))
        else:
            newItem["subzones"] = np.vstack((newItem["subzones"], np.append(item["subzones"][i], np.array(
                [(item["subzones"][i][2] / bottomPlaneArea) * item["weight"]]))))
    return newItem


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
            weightNotExceeded = np.append(weightNotExceeded, list(filter(lambda x: x is not None, map(
                lambda x: (i[1] * item["weight"] + x["weight"]) <= x["weight_limit"] if i[0] == x["id"] else None,
                truckSubzones))))
    else:
        for i in itemWithWeightContribution["subzones"]:
            # Check if adding the weight to the subzone current weight exceeds its limit.
            weightNotExceeded = np.append(weightNotExceeded, list(filter(lambda x: x is not None, map(
                lambda x: (i[3] + x["weight"]) <= x["weight_limit"] if i[0] == x["id"] else None, truckSubzones))))
    return np.array([all(weightNotExceeded), itemWithWeightContribution])


# ------------------ Stackability - C5 ---------------------------------------------
# This function return the average weight for a list of items.
def getAverageWeight(items):
    return sum(list(map(lambda x: x["weight"], items))) / len(items)


# This function returns true if a item is stackable, false otherwise.
# An item is stackable if the contributions of weight for every object underneath does not exceed certain conditions.
def isStackable(item, averageWeight, placedItems):
    if isInFloor(item):
        # For a optimum solution it is better to reward the algorithm to put the weightier items on the floor.
        if item["weight"] > (1.15 * averageWeight):
            return True
        else:
            return False
    else:
        # Reduce the scope of items to those sharing their top y Plane with bottom y Plane of the new item.
        sharePlaneItems = list(filter(lambda x: getBottomPlaneHeight(item) == getTopPlaneHeight(x), placedItems))
        # This ndarray will store if the conditions are met for every item the newItem is above.
        stackableForSharePlaneItems = np.array((), dtype=bool)
        for i in sharePlaneItems:
            # % of area between the newItem and the placed items underneath * newItem["weight"]
            itemWeightContribution = (getIntersectionArea(i, item) / getBottomPlaneArea(item)) * item["weight"]
            # Portion of weight above fragile item cannot be more than 50% of the weight of the fragile item.
            if i["breakability"] and itemWeightContribution <= 0.5 * i["weight"]:
                stackableForSharePlaneItems = np.append(stackableForSharePlaneItems, True)
            elif not i["breakabitily"] and itemWeightContribution <= i["weight"]:
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
        # TODO, make tests on this predefined condition.
        if (itemBRR_z >= truckBRR_z - 1) and (itemBRR_z <= truckBRR_z):
            return True
    else:
        return False


# ------------------ Stability - C7 ------------------------------------------------

# This function returns the item modified including the contact area in each subzone for it.
# Input Item Subzone Format: [[id_subzone, percentageIn],...]
# Output Item Subzone Format: [[id_subzone, percentageIn, contactAreaIn],...]
def addContactAreaTo(item, placedItems):
    newItem = deepcopy(item)
    newItem["subzones"] = np.array(())
    # Go over the subzones the item is in.
    for i in range(item["subzones"].shape[0]):
        if isInFloor(item):
            totalContactAreaInSubzone = getBottomPlaneArea(item) * item["subzones"][i][1]
        else:
            # Reduce the scope of items to those in the same subzone
            placedItemsSubzone = list(filter(lambda x: item["subzones"][i][0] in getItemSubzones(x), placedItems))
            # Reduce the scope of items to those sharing their top y-axis Plane with bottom y-axis Plane of the new item.
            sharePlaneItems = list(
                filter(lambda x: getBottomPlaneHeight(item) == getTopPlaneHeight(x), placedItemsSubzone))
            # Calculate the area of intersection between the sharedPlaneItems and the new item.
            totalContactAreaInSubzone = sum(list(map(lambda x: getIntersectionArea(x, item), sharePlaneItems)))
        # For each subzone the item is in we also have the contact area which is not the same as the percentage within the subzone.
        if i == 0:
            newItem["subzones"] = np.append(item["subzones"][i], np.array([totalContactAreaInSubzone]))
        else:
            newItem["subzones"] = np.vstack(
                (newItem["subzones"], np.append(item["subzones"][i], np.array([totalContactAreaInSubzone]))))
    return newItem


# This function returns a ndarray with the item and True if the item has at least 70% of supported area, False otherwise.
def isStable(item, placedItems):
    itemWithContactArea = addContactAreaTo(item, placedItems)
    totalItemContactArea = sum(list(map(lambda x: x[2], itemWithContactArea["subzones"])))
    contactAreaPercentage = totalItemContactArea / getBottomPlaneArea(item)
    if contactAreaPercentage > 0.7:
        return np.array([True, itemWithContactArea])
    return np.array([False, itemWithContactArea])


# ------------------ Physical constrains - Truck-related ----------------------------------------
# This function returns True if the packet inserted in a potentialPoint does not exceed the length of the truck, False otherwise.
def isWithinTruckLengthAux(item):
    return item["lengthFitting"]


# This function returns True if the packet inserted in a potentialPoint does not exceed the length of the truck, False otherwise.
def isWithinTruckLength(item, truckLength):
    if getBRR(item)[2] <= truckLength:
        return True
    return False


# This function returns True if the packet inserted in a potentialPoint does not exceed the width of the truck, False otherwise.
def isWithinTruckWidth(item, truckWidth):
    if getBRR(item)[0] <= truckWidth:
        return True
    return False


# This function returns True if the packet inserted in a potentialPoint does not exceed the height of the truck, False otherwise.
def isWithinTruckHeight(item, truckHeight):
    if getTopPlaneHeight(item) <= truckHeight:
        return True
    return False


# This function returns True if dimension constrains are met, False otherwise.
def isWithinTruckDimensionsConstrains(item, truckDimensions):
    if isWithinTruckLength(item, truckDimensions["length"]) and isWithinTruckWidth(item, truckDimensions[
        "width"]) and isWithinTruckHeight(item, truckDimensions["Height"]):
        return True
    return False


# ------------------ Physical constrains - Items-related ----------------------------------------
# TODO, may be overlapping issues between items for those PP which are the projection of some extreme points which are in a exceeding area.
# This function returns True if the item does not overlap other items around it, False otherwise.
def isNotOverlapping(item, placedItems):
    # Corners of the item evaluated for insertion in PP.
    points = np.array((getBLF(item), getTLF(item), getTRF(item), getBRF(item), getBRR(item), getBLR(item), getTRR(item),
                       getTLR(item)))
    for i in placedItems:
        poly = np.array((getBLF(i), getTLF(i), getTRF(i), getBRF(i), getBRR(i), getBLR(i), getTRR(i), getTLR(i)))
        outsideFromPoly = list(map(lambda x: True if x == -1 else False, Delaunay(poly).find_simplex(points)))
        if all(outsideFromPoly):
            continue
        else:
            return False
    return True


# --------------------- Helpers to the main module function -----------------------------------
# This function checks if a potential point is feasible for placing the item, meaning it satisfies all the conditions.
# Returns the state of feasibility condition and the item after processing it for all the constrains.
def isFeasible(potentialPoint, placedItems, newItem, candidateListAverageWeight, truck):
    item = setItemMassCenter(newItem, potentialPoint)
    # Conditions to be checked sequentially to improve performance.
    if not isWeightExceeded(placedItems, item, truck) and isWithinTruckDimensionsConstrains(item, truck[
        "dimensions"]) and isADRSuitable(item, getTruckBRR(truck)[2]) and isNotOverlapping(item, placedItems):
        truckSubzones = getContainerSubzones(truck)
        itemWithSubzones = setItemSubzones(truckSubzones, item)
        # This item is [condition, itemWithContactAreaForEachSubzone]
        i3WithCondition = isStable(itemWithSubzones, placedItems)
        # Checks if it is stable and stackable.
        if i3WithCondition[0] and isStackable(item, candidateListAverageWeight, placedItems):
            # Way of keeping the modified object and if the condition state. TODO, maybe is not necessary to keep the item.
            i4WithCondition = itemContributionExceedsSubzonesWeightLimit(i3WithCondition[1], truckSubzones)
            if i4WithCondition[0]:
                return np.array([True, i4WithCondition[1]])
            else:
                return np.array([False, newItem])
        else:
            return np.array([False, newItem])
    else:
        return np.array([False, newItem])


# This function determines if a potential point if better than other using the following criteria:
# - PP is better than another PP if it has a lower Z-coordinate.
# - In case of tie, if inserting an item in the best implies more contact surface with the underlying object.
def isBetterPP(newPP, currentBest, item, placedItems):
    # Lower z-coordinate meaning closer to the front of the truck, increases volume.
    if newPP[2] < currentBest[2]:
        return True
    # In case of tie, take the one which implies the object to have more contact area with the object/objects underneath.
    elif newPP[2] == currentBest[2]:
        # If the new potential point is in the floor is better than any other.
        if isInFloor(item):
            return True
        else:
            bottomPlaneArea = getBottomPlaneArea(item)
            newPPItem = list(filter(lambda x: any(list(map(lambda y: all(y == newPP), x["pp_out"]))), placedItems))[0]
            currentBestPPItem = \
            list(filter(lambda x: any(list(map(lambda y: all(y == currentBest), x["pp_out"]))), placedItems))[0]
            bestItem = min([newPPItem, currentBestPPItem],
                           key=lambda x: abs(bottomPlaneArea / getTopPlaneHeight(x) - 1))
            if newPPItem == bestItem:
                return True
            else:
                return False
    else:
        return False


# This function creates a list of potential points generated after inserting an item.
# Output format: [[TLF],[BLR],[BRF]]
def generateNewPPs(item, placedItems):
    BLR = getBLR(item)
    BRF = getBRF(item)
    TLF = getTLF(item)
    result = np.array(TLF)
    if isInFloor(item):
        result = np.vstack((result, BLR, BRF))
    else:
        # Reduce the scope of items to those sharing their top y-axis Plane with bottom y-axis Plane of the new item.
        sharePlaneItems = list(
            filter(lambda x: getBottomPlaneHeight(item) == getTopPlaneHeight(x), placedItems))
        # Check which points are not supported.
        isBLRinPlane = all(list(map(lambda x: pointInPlane(BLR, getBLF(x), getBRR(x)), sharePlaneItems)))
        isBRFinPlane = all(list(map(lambda x: pointInPlane(BRF, getBLF(x), getBRR(x)), sharePlaneItems)))
        # Modify not supported points to its projection.
        if not isBRFinPlane:
            BRF = getNearestProjectionPointFor(BRF, placedItems)
        if not isBLRinPlane:
            BLR = getNearestProjectionPointFor(BLR, placedItems)
        result = np.vstack((result, BLR, BRF))
    return result


# This function creates a solution from a list of packets and a given potential points
# TODO, determine if just one or several trucks
def fillList(candidateList, potentialPoints, truck, retry, placedItems):
    discardList = []
    candidateListAverageWeight = getAverageWeight(candidateList)
    for i in candidateList:
        # Using the method as a retryList fill.
        if retry:
            i = reorient(i)
        # Initialization of best point as be the worst, in this context the TRR of the truck.
        pp_best = np.array([truck["width"], truck["height"], truck["length"]])
        # Try to get the best PP for an item.
        for pp in potentialPoints:
            # [condition, item]
            feasibility = isFeasible(pp, placedItems, i, candidateListAverageWeight, truck)
            if feasibility[0] and isBetterPP(pp, pp_best, feasibility[1], placedItems):
                pp_best = pp
                feasibleItem = feasibility[1]
        # If the best is different from the worst there is a PP to insert the item.
        if all(pp_best != np.array([truck["width"], truck["height"], truck["length"]])):
            # Add pp in which the object is inserted.
            feasibleItem["pp_in"] = pp_best
            # Remove pp_best from potentialPoints list.
            potentialPoints = np.array(list(filter(lambda x: all(x != pp_best), potentialPoints)))
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
    return {"placed": placedItems, "discard": discardList, "truck": truck, "potentialPoints": potentialPoints}


# This function is the main function of the module M2_2
def main_m2_2(truck, candidateList):
    potentialPoints = truck["pp"]
    filling = fillList(candidateList, potentialPoints, truck, 0, [])
    refilling = fillList(filling["discard"], filling["potentialPoints"], filling["truck"], 1, filling["placed"])
    return refilling