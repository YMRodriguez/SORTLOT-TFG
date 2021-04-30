import numpy as np
from main.packetOptimization.randomizationAndSorting.randomization import changeItemOrientation
import math


# --------------------------------- Item geometric helpers -----------------------------------
# This function adds the spacial center of mass to a packet solution inserted in a PP
def setItemMassCenter(item, potentialPoint, truckWidth):
    # TODO, limit in which to iterate to determine best solutions.
    if truckWidth * 0.85 <= potentialPoint[0] <= truckWidth:
        item["mass_center"] = potentialPoint + np.array([-item["width"] / 2, item["height"] / 2, item["length"] / 2])
    else:
        item["mass_center"] = potentialPoint + np.array([item["width"] / 2, item["height"] / 2, item["length"] / 2])
    return item


# This function returns if an item is in the floor.
def isInFloor(item):
    if item["mass_center"][1] - item["height"] / 2 == 0:
        return True
    return False


# This function returns the spacial Bottom-Left-Front of the item.
def getBLF(item):
    return item["mass_center"] - np.array([item["width"] / 2, item["height"] / 2, item["length"] / 2])


# This function returns the spacial Bottom-Right-Front of the item.
def getBRF(item):
    return item["mass_center"] - np.array([-item["width"] / 2, item["height"] / 2, item["length"] / 2])


# This function returns the spacial Bottom-Right-Rear of the item.
def getBRR(item):
    return item["mass_center"] + np.array([item["width"] / 2, -item["height"] / 2, item["length"] / 2])


# This function returns the spacial Bottom-Left-Rear of the item.
def getBLR(item):
    return item["mass_center"] + np.array([-item["width"] / 2, -item["height"] / 2, item["length"] / 2])


# This function return the spacial Top-Left-Front of the item.
def getTLF(item):
    return item["mass_center"] - np.array([item["width"] / 2, -item["height"] / 2, item["length"] / 2])


# This function returns the spacial Top-Right-Front of the item.
def getTRF(item):
    return item["mass_center"] + np.array([item["width"] / 2, item["height"] / 2, -item["length"] / 2])


# This function return the spacial Top-Right-Rear of the item.
def getTRR(item):
    return item["mass_center"] + np.array([item["width"] / 2, item["height"] / 2, item["length"] / 2])


# This function returns the spacial Top-Left-Rear of the item.
def getTLR(item):
    return item["mass_center"] + np.array([-item["width"] / 2, item["height"] / 2, item["length"] / 2])


# This function gets the mid point in the bottom front intersection of the item.
def getBFMid(item):
    return item["mass_center"] - np.array([0, item["height"] / 2, item["length"] / 2])


# This function gets the mid point in the bottom front intersection of the item plus a differential.
def getBFMidDifferential(item):
    return item["mass_center"] - np.array([0, item["height"] / 2, item["length"] * 0.45])


# This function gets the mid point in the bottom rear intersection of the item.
def getBRMid(item):
    return item["mass_center"] - np.array([0, item["height"] / 2, -item["length"] / 2])


# This function gets the mid point in the top front intersection of the item.
def getTFMid(item):
    return item["mass_center"] + np.array([0, item["height"] / 2, -item["length"] / 2])


# This function gets the mid point in the top rear intersection of the item.
def getTRMid(item):
    return item["mass_center"] + np.array([0, item["height"] / 2, item["length"] / 2])


# This function returns the extended right mass center of an item.
def getMCRight(item):
    return item["mass_center"] + np.array([item["width"] / 4, 0, 0])


# This function returns the extended left mass center of an item.
def getMCLeft(item):
    return item["mass_center"] - np.array([item["width"] / 4, 0, 0])


# This function returns the extended front mass center of an item.
def getMCFront(item):
    return item["mass_center"] - np.array([0, 0, item["length"] / 4])


# This function returns the extended rear mass center of an item.
def getMCRear(item):
    return item["mass_center"] + np.array([0, 0, item["length"] / 4])


# This function returns the extended bottom mass center of an item.
def getMCBottom(item):
    return item["mass_center"] - np.array([0, item["height"] / 4, 0])


# This function returns the extended top mass center of an item.
def getMCTop(item):
    return item["mass_center"] + np.array([0, item["height"] / 4, 0])


# This function returns the mid point of the right bottom part between rear and front.
def getMidBottomRight(item):
    return item["mass_center"] - np.array([item["width"] / 2, item["height"] / 2, 0])


# This function returns the mid point of the right bottom part between rear and front.
def getMidBottomLeft(item):
    return item["mass_center"] - np.array([-item["width"] / 2, item["height"] / 2, 0])


# This function returns the mid point of the right bottom part between rear and front.
def getMidTopRight(item):
    return item["mass_center"] + np.array([-item["width"] / 2, item["height"] / 2, 0])


# This function returns the mid point of the right bottom part between rear and front.
def getMidTopLeft(item):
    return item["mass_center"] + np.array([item["width"] / 2, item["height"] / 2, 0])


# This function returns the height of the bottom Plane of an item.
def getBottomPlaneHeight(item):
    return item["mass_center"][1] - np.array([item["height"] / 2])[0]


# This function returns the height(y-axis) of the top Plane of an item.
def getTopPlaneHeight(item):
    return item["mass_center"][1] + np.array([item["height"] / 2])[0]


# This function returns the area(m2) of the base face of an item.
def getBottomPlaneArea(item):
    return (getBRF(item)[0] - getBLF(item)[0]) * (getBLR(item)[2] - getBLF(item)[2])


# This function returns the intersection area(m2) between two items in Plane x(width), z(length).
def getIntersectionArea(i1, i2):
    return (min(getBRR(i1)[0], getBRR(i2)[0]) - max(getBLF(i1)[0], getBLF(i2)[0])) * \
           (min(getBRR(i1)[2], getBRR(i2)[2]) - max(getBLF(i1)[2], getBLF(i2)[2]))


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


# This function gets the euclidean distance between two given points.
def getEuclideanDistance(a, b):
    return round(math.sqrt(a ** 2 + b ** 2))


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
