import numpy as np


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
def getItemBLF(item):
    blf = item["mass_center"] - np.array([item["width"] / 2, item["height"] / 2, item["length"] / 2])
    return blf


# This function returns the spacial Bottom-Right-Front of the item.
def getItemBRF(item):
    brf = item["mass_center"] - np.array([-item["width"] / 2, item["height"] / 2, item["length"] / 2])
    return brf


# This function returns the spacial Bottom-Right-Rear of the item.
def getItemBRR(item):
    brr = item["mass_center"] + np.array([item["width"] / 2, -item["height"] / 2, item["length"] / 2])
    return brr


# This function returns the spacial Bottom-Left-Rear of the item.
def getItemBLR(item):
    blr = item["mass_center"] + np.array([-item["width"] / 2, -item["height"] / 2, item["length"] / 2])
    return blr


# This function returns the height of the bottom plain of an item.
def getBottomPlainHeight(item):
    h = item["mass_center"][1] - np.array([item["height"] / 2])
    return h


# This function returns the height of the top plain of an item.
def getTopPlainHeight(item):
    h = item["mass_center"][1] + np.array([item["height"] / 2])
    return h


# This function returns the area of the base face of an item.
def getBottomPlainArea(item):
    return (getItemBRF(item)[0] - getItemBLF(item)[0]) * (getItemBLR(item[2]) - getItemBLF(item[2]))


# This function returns the intersection area between two items none in plain x(width), z(length).
def getIntersectionArea(i1, i2):
    dx = min(getItemBRR(i1)[0], getItemBRR(i2)[0]) - max(getItemBLF(i1)[0], getItemBLF(i2)[0])
    dz = min(getItemBRR(i1)[2], getItemBRR(i2)[2]) - max(getItemBLF(i1)[2], getItemBLF(i2)[2])
    return dx * dz


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
