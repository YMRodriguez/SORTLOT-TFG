"""
author: Yamil Mateo Rodríguez
university: Universidad Politécnica de Madrid
"""

import numpy as np
from main.packetAdapter.helpers import changeItemOrientation


# --------------------------------- Item geometric helpers -----------------------------------
def setItemMassCenter(item, potentialPoint, truckWidth, minDim):
    """
    This function adds the spatial center of mass to a packet solution inserted in a PP.

    :param item: object representing a packet.
    :param potentialPoint: point in cartesian coordinates in which is inserted the packet.
    :param truckWidth: the width of the truck.
    :param minDim: minimum dimension that there is in the rest of the packets 
    :return:
    """
    if truckWidth - minDim <= potentialPoint[0] <= truckWidth:
        item["mass_center"] = potentialPoint + np.array([-item["width"], item["height"], item["length"]])/2
    else:
        item["mass_center"] = potentialPoint + np.array([item["width"], item["height"], item["length"]])/2
    return item


def isInFloor(item):
    """
    This function checks if an item is in the floor.

    :param item: object representing the item.
    :return: True if the item is in the floor, False otherwise.
    """
    if item["mass_center"][1] - item["height"] / 2 == 0:
        return True
    return False


def getBLF(item):
    """
    This function gets the spatial Bottom-Left-Front corner of the item.

    :param item: object representing the item.
    :return: The cartesian coordinates of the corner.
    """
    return item["mass_center"] - [item["width"]/2, item["height"]/2, item["length"]/2]


def getBRF(item):
    """
    This function gets the spatial Bottom-Right-Front corner of the item.

    :param item: object representing the item.
    :return: The cartesian coordinates of the corner.
    """
    return item["mass_center"] - np.array([-item["width"], item["height"], item["length"]])/2


def getBRR(item):
    """
    This function gets the spatial Bottom-Right-Rear corner of the item.

    :param item: object representing the item.
    :return: The cartesian coordinates of the corner.
    """
    return item["mass_center"] + np.array([item["width"], -item["height"], item["length"]])/2


def getBLR(item):
    """
    This function gets the spatial Bottom-Left-Rear corner of the item.

    :param item: object representing the item.
    :return: The cartesian coordinates of the corner.
    """
    return item["mass_center"] + np.array([-item["width"], -item["height"], item["length"]])/2


def getTLF(item):
    """
    This function gets the spatial Top-Left-Front corner of the item.

    :param item: object representing the item.
    :return: The cartesian coordinates of the corner.
    """
    return item["mass_center"] - np.array([item["width"], -item["height"], item["length"]])/2


def getTRF(item):
    """
    This function gets the spatial Top-Right-Front corner of the item.

    :param item: object representing the item.
    :return: The cartesian coordinates of the corner.
    """
    return item["mass_center"] + np.array([item["width"], item["height"], -item["length"]])/2


def getTRR(item):
    """
    This function gets the spatial Top-Right-Rear corner of the item.

    :param item: object representing the item.
    :return: The cartesian coordinates of the corner.
    """
    return item["mass_center"] + np.array([item["width"], item["height"], item["length"]])/2


def getTLR(item):
    """
    This function gets the spatial Top-Left-Rear corner of the item.

    :param item: object representing the item.
    :return: The cartesian coordinates of the corner.
    """
    return item["mass_center"] + np.array([-item["width"], item["height"], item["length"]])/2


def getBottomPlaneHeight(item):
    """
    This function gets the height of the bottom plane of an item.

    :param item: object representing the item.
    :return: Height in metres.
    """
    return item["mass_center"][1] - item["height"]/2


def getTopPlaneHeight(item):
    """
    This function gets the height of the top planes of an item.

    :param item: object representing the item.
    :return: Height in metres.
    """
    return item["mass_center"][1] + item["height"]/2


def getBottomPlaneArea(item):
    """
    This function gets the bottom plane's item area.

    :param item: object representing the item.
    :return: area in square metres.
    """
    return item["length"] * item["width"]


def generalIntersectionArea(p1, p2):
    """
    This function returns intersection area between two planes.

    :param p1: plane with format [cord1, cord2, difAxis1, difAxis2]
    :param p2: plane with format [cord1, cord2, difAxis1, difAxis2]
    :return: intersection area in m2.
    """
    d1 = min(p1[0] + p1[2], p2[0] + p2[2]) - max(p1[0], p2[0])
    d2 = min(p1[1] + p1[3], p2[1] + p2[3]) - max(p1[1], p2[1])
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


def getZXPlaneFor(item):
    """
    This function generates the ZX plane.

    :param item: item object.
    :return: ndarray representing [z,x,dZ,dX]
    """
    blf = getBLF(item)
    return np.array([blf[2], blf[0], item["length"], item["width"]])


# TODO, change these margins.
def pointInPlane(point, planeLF, planeRR):
    """
    This function checks if a point is inside a plane.

    :param point: cartesian point to be checked.
    :param planeLF: cartesian left front point of the plane.
    :param planeRR: cartesian right rear point of the plane.
    :return: True if the point is into plane, False otherwise.
    """
    return planeRR[0] + 0.001 >= point[0] >= planeLF[0] - 0.001 and planeRR[2] + 0.001 >= point[2] >= planeLF[2] - 0.001


def getNearestProjectionPointFor(point, placedItems):
    """
    This function projects a potential point onto the nearest item top plane along the y-axis.

    :param point: the cartesian point to be projected.
    :param placedItems: dictionary of placed packets.
    :return: cartesian coordinates of the projected points.
    """
    # Reduce the scope to those items whose top or bottom plane contains the point in (x,z)-axis.
    pointIntoPlaneItems = list(filter(lambda x: pointInPlane(point, getBLF(x), getBRR(x)), placedItems))
    # Sort and get the item with the nearest y-axis value.
    itemWithNearestProj = sorted(pointIntoPlaneItems, key=lambda x: getTopPlaneHeight(x))
    if len(itemWithNearestProj) != 0:
        # Return the same point but with y-axis value projected.
        return np.array([point[0], getTopPlaneHeight(itemWithNearestProj[0]) + 0.0015, point[2]])
    # Return the projection to the floor.
    return np.array([point[0], 0, point[2]])


def reorient(item):
    """
    This function randomly reorients a given item.

    :param item: item object.
    :return: reoriented item.
    """
    return changeItemOrientation(item, item["feasibleOr"])


def generateMaxAreas(nItemsDst, nFilteredDst, truck, nDst):
    """
    This function calculates the maximum area of the container for each destination.

    :param nDst: number of destinations in the cargo.
    :param truck: data object of the container/truck.
    :param nFilteredDst: number of items filtered (by weight) for each destination.
    :param nItemsDst: number of items for each destination.
    :return: ndarray with max area for each destination.
    """
    nItemsDst = np.asarray(nItemsDst)
    nFilteredDSt = np.asarray(nFilteredDst)
    if nDst > 3:
        # List of factors related to each destination, decimal values in [0, 1].
        factor = []
        for i in range(nDst):
            if i != nDst - 1:
                # Just cut percentage of the destinations previous to the first out.
                factor.append(1 - (nDst - i + 2) / 100)
            else:
                factor.append(1)
        factor = np.asarray(factor)
    else:
        factor = np.ones((1, nDst))[0]
    return (nItemsDst / np.sum(nItemsDst) + nFilteredDSt / np.sum(nFilteredDSt)) * factor * 0.5 * (
            truck["length"] * truck["width"])


# ------------------------------ Truck Geometric Helpers ----------------------------------------
# This function returns the spacial Bottom-Left-Front of the item.
# TODO, if the truck is modified this changes.
def getTruckBLF(truck):
    return np.array([0, 0, 0])


def getTruckBRF(truck):
    """
    This function gets the spatial coordinates of the Bottom Right Front of a truck.

    :param truck: truck object.
    :return: ndarray representing the spatial coordinates of truck's BRF.
    """
    return np.array([truck["width"], 0, 0])


def getTruckBRR(truck):
    """
    This function gets the spatial coordinates of the Bottom Right Rear of a truck.

    :param truck: truck object.
    :return: ndarray representing the spatial coordinates of truck's BRR.
    """
    return np.array([truck["width"], 0, truck["length"]])


def getTruckBLR(truck):
    """
    This function gets the spatial coordinates of the Bottom Left Rear of a truck.

    :param truck: truck object.
    :return: ndarray representing the spatial coordinates of truck's BLR.
    """
    return np.array([0, 0, truck["length"]])
