import numpy as np
from main.packetOptimization.randomizationAndSorting.randomization import changeItemOrientation


# --------------------------------- Item geometric helpers -----------------------------------
# This function adds the spacial center of mass to a packet solution inserted in a PP
def setItemMassCenter(item, potentialPoint):
    mc = potentialPoint + np.array([item["width"] / 2, item["height"] / 2, item["length"] / 2])
    item["mass_center"] = mc
    return item


# This function returns if an item is in the floor.
def isInFloor(item):
    if item["mass_center"][1] - item["height"] / 2 == 0:
        return True
    return False


# This function returns the spacial Bottom-Left-Front of the item.
def getBLF(item):
    blf = item["mass_center"] - np.array([item["width"] / 2, item["height"] / 2, item["length"] / 2])
    return blf


# This function returns the spacial Bottom-Right-Front of the item.
def getBRF(item):
    brf = item["mass_center"] - np.array([-item["width"] / 2, item["height"] / 2, item["length"] / 2])
    return brf


# This function returns the spacial Bottom-Right-Rear of the item.
def getBRR(item):
    brr = item["mass_center"] + np.array([item["width"] / 2, -item["height"] / 2, item["length"] / 2])
    return brr


# This function returns the spacial Bottom-Left-Rear of the item.
def getBLR(item):
    blr = item["mass_center"] + np.array([-item["width"] / 2, -item["height"] / 2, item["length"] / 2])
    return blr


# This function return the spacial Top-Left-Front of the item.
def getTLF(item):
    tlf = item["mass_center"] - np.array([-item["width"] / 2, -item["height"] / 2, item["length"] / 2])
    return tlf


# This function returns the spacial Top-Right-Front of the item.
def getTRF(item):
    trf = item["mass_center"] + np.array([item["width"] / 2, item["height"] / 2, -item["length"] / 2])
    return trf


# This function return the spacial Top-Right-Rear of the item.
def getTRR(item):
    trr = item["mass_center"] + np.array([item["width"] / 2, item["height"] / 2, item["length"] / 2])
    return trr


# This function returns the spacial Top-Left-Rear of the item.
def getTLR(item):
    tlr = item["mass_center"] + np.array([-item["width"] / 2, item["height"] / 2, item["length"] / 2])
    return tlr


# This function returns the height of the bottom Plane of an item.
def getBottomPlaneHeight(item):
    h = item["mass_center"][1] - np.array([item["height"] / 2])[0]
    return h


# This function returns the height(y-axis) of the top Plane of an item.
def getTopPlaneHeight(item):
    h = item["mass_center"][1] + np.array([item["height"] / 2])[0]
    return h


# This function returns the area(m2) of the base face of an item.
def getBottomPlaneArea(item):
    return (getBRF(item)[0] - getBLF(item)[0]) * (getBLR(item[2]) - getBLF(item[2]))


# This function returns the intersection area(m2) between two items in Plane x(width), z(length).
def getIntersectionArea(i1, i2):
    dx = min(getBRR(i1)[0], getBRR(i2)[0]) - max(getBLF(i1)[0], getBLF(i2)[0])
    dz = min(getBRR(i1)[2], getBRR(i2)[2]) - max(getBLF(i1)[2], getBLF(i2)[2])
    return dx * dz


# This function returns True if the point is inside the Plane for the same y-axis value.
# PlaneLF/RR could be both the bottom and top Plane of an item.
def pointInPlane(point, planeLF, planeRR):
    return planeRR[0] >= point[0] >= planeLF[0] and planeRR[2] >= point[2] >= planeLF[2]


# This function returns the projection in y-axis over the nearest item top plane for a point.
def getNearestProjectionPointFor(point, placedItems):
    # Reduce the scope to those items whose top or bottom plane contains the point in (x,z)-axis.
    pointIntoPlaneItems = list(filter(lambda x: pointInPlane(point, getBLF(x), getBRR(x)), placedItems))
    # Sort and get the item with the nearest y-axis value.
    itemWithNearestProj = sorted(pointIntoPlaneItems, key=lambda x: getTopPlaneHeight(x))[0]
    # Return the same point but with y-axis value projected.
    return np.array([point[0], getTopPlaneHeight(itemWithNearestProj), point[2]])


# This function randomly reorients a given item.
def reorient(item):
    return changeItemOrientation(item, list(filter(lambda x: x != item["orientation"], list(range(1, 7)))))


# ------------------------------ Truck Geometric Helpers ----------------------------------------
# This function returns the spacial Bottom-Left-Front of the item.
# TODO, if the truck is modified this changes.
def getTruckBLF(truck):
    return np.array([0, 0, 0])


# This function returns the spacial Bottom-Right-Front of the item.
def getTruckBRF(truck):
    return np.array([truck["width"], 0, 0])


# This function returns the spacial Bottom-Right-Rear of the item.
def getTruckBRR(truck):
    return np.array([truck["width"], 0, truck["length"]])


# This function returns the spacial Bottom-Left-Rear of the item.
def getTruckBLR(truck):
    return np.array([0, 0, truck["length"]])
