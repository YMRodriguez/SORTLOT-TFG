import numpy as np
from main.packetAdapter.helpers import changeItemOrientation


# --------------------------------- Item geometric helpers -----------------------------------
# This function adds the spacial center of mass to a packet solution inserted in a PP
def setItemMassCenter(item, potentialPoint, truckWidth):
    # TODO, limit in which to iterate to determine best solutions.
    if truckWidth * 0.92 <= potentialPoint[0] <= truckWidth:
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


# This function returns the height of the bottom Plane of an item.
def getBottomPlaneHeight(item):
    return item["mass_center"][1] - np.array([item["height"] / 2])[0]


# This function returns the height(y-axis) of the top Plane of an item.
def getTopPlaneHeight(item):
    return item["mass_center"][1] + np.array([item["height"] / 2])[0]


# This function returns the area(m2) of the base face of an item.
def getBottomPlaneArea(item):
    return item["length"] * item["width"]


# This function returns the intersection area(m2) between two items in Plane x(width), z(length).
def getIntersectionArea(i1, i2):
    dx = min(getBRR(i1)[0], getBRR(i2)[0]) - max(getBLF(i1)[0], getBLF(i2)[0])
    dz = min(getBRR(i1)[2], getBRR(i2)[2]) - max(getBLF(i1)[2], getBLF(i2)[2])
    if (dx >= 0) and (dz >= 0):
        return dx * dz
    else:
        return 0


def generalIntersectionArea(p1, p2):
    """
    This function returns intersection area between two planes.

    :param p1: plane with format [cord1, cord2, difAxis1, difAxis2]
    :param p2: plane with format [cord1, cord2, difAxis1, difAxis2]
    :return: intersection area in m2.
    """
    d1 = min(p1[0]+p1[2], p2[0]+p2[2]) - max(p1[0], p2[0])
    d2 = min(p1[1]+p1[3], p2[1]+p2[3]) - max(p1[1], p2[1])
    if (d1 >= 0) and (d2 >= 0):
        return d1 * d2
    else:
        return 0


def getPlanesFor(item):
    """
    This function generates XY, ZY, ZX planes represented in ndarrays.

    :param item: item object.
    :return: tuple of 3 planes.
    """
    blf = getBLF(item)
    return np.array([blf[0], blf[1], item["width"], item["height"]]), \
           np.array([blf[2], blf[1], item["length"], item["height"]]), \
           np.array([blf[2], blf[0], item["length"], item["width"]])


# This function returns True if the point is inside the Plane for the same y-axis value.
# PlaneLF/RR could be both the bottom and top Plane of an item.
def pointInPlane(point, planeLF, planeRR):
    return planeRR[0] >= point[0] >= planeLF[0] and planeRR[2] >= point[2] >= planeLF[2]


# This function returns the projection in y-axis over the nearest item top plane for a point.
def getNearestProjectionPointFor(point, placedItems):
    # Reduce the scope to those items whose top or bottom plane contains the point in (x,z)-axis.
    pointIntoPlaneItems = list(filter(lambda x: pointInPlane(point, getBLF(x), getBRR(x)), placedItems))
    # Sort and get the item with the nearest y-axis value.
    itemWithNearestProj = sorted(pointIntoPlaneItems, key=lambda x: getTopPlaneHeight(x))
    if len(itemWithNearestProj) != 0:
        # Return the same point but with y-axis value projected.
        return np.array([point[0], getTopPlaneHeight(itemWithNearestProj[0]) + 0.003, point[2]])
    # Return the projection to the floor.
    return np.array([point[0], 0, point[2]])


def reorient(item):
    """
    This function randomly reorients a given item.
    :param item: item object.
    :return: reoriented item.
    """
    return changeItemOrientation(item, list(filter(lambda x: x != item["orientation"], [1, 2, 3, 4])))


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
