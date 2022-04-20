"""
author: Yamil Mateo Rodríguez
university: Universidad Politécnica de Madrid
"""

import random
from main.packetAdapter.helpers import getMaxPriority


# ------------------------- Comparators --------------------------------------
def volumeComp(i0, i1):
    """
    This function compares the volume of two give items.

    :param i0: item object 1.
    :param i1: item object 2.
    :return: True if within bounds of similarity, false otherwise.
    """
    return 0.85 < (i0["volume"] / i1["volume"]) < 1.15


def weightComp(i0, i1):
    """
    This function compares the weight of two give items.

    :param i0: item object 1.
    :param i1: item object 2.
    :return: True if within bounds of similarity, false otherwise.
    """
    return 0.85 < (i0["weight"] / i1["weight"]) < 1.15


# ------------------------------ Swappers --------------------------------------
def genericSwapper(lst, i, j):
    """
    This is a generic swapper function which given a list changes two items by their indexes.

    :param lst: list object.
    :param i: index.
    :param j: index.
    """
    lst[i], lst[j] = lst[j], lst[i]


def swapByVolume(packets):
    """
    This function swaps an item with its consecutive in the list with 50% prob if they have the
    a degree of volume similarity [0.85, 1.15] and destination code.

    :param packets: list of packets.
    :return: modified list of packets.
    """
    for i in range(len(packets) - 1):
        if volumeComp(packets[i], packets[i + 1]) \
                and packets[i]["dstCode"] == packets[i+1]["dstCode"]\
                and bool(random.getrandbits(1)):
            genericSwapper(packets, i, i + 1)
    return packets


def swapByWeight(packets):
    """
    This function swaps an item with its consecutive in the list with 50% prob if they have the
    a degree of weight similarity [0.85, 1.15] and destination code.

    :param packets: list of packets.
    :return: modified list of packets.
    """
    for i in range(len(packets) - 1):
        if weightComp(packets[i], packets[i + 1]) \
                and packets[i]["dstCode"] == packets[i+1]["dstCode"]\
                and bool(random.getrandbits(1)):
            genericSwapper(packets, i, i + 1)
    return packets


def swapByPriority(packets, nDst):
    """
    This function swaps an item with another in the list with 50% prob if they have the
    same priority and destination code.

    :param packets: list of packets.
    :return: modified list of packets.
    """
    prioPacketsByDst = list(map(lambda x: list(filter(lambda y: y["dstCode"] == x and y["priority"], packets)), list(range(nDst))))
    for d in range(nDst):
        for i in prioPacketsByDst[d]:
            if bool(random.getrandbits(1)):
                item_j = random.choice(list(filter(lambda x: x != i, prioPacketsByDst[d])))
                index_j = packets.index(item_j)
                index_i = packets.index(i)
                if weightComp(i, item_j) and volumeComp(i, item_j):
                    genericSwapper(packets, index_i, index_j)
    return packets


# ------------------- Main Function ---------------------------------------------------------------------
def randomization(packets, nDst):
    """
    This function randomizes packets based on weight, volume and priority criteria.

    :param packets: list of packets.
    :return: randomized list.
    """
    swapped_v = swapByVolume(packets)
    swapped_w = swapByWeight(swapped_v)
    return swapByPriority(swapped_w, nDst) if getMaxPriority(packets) else swapped_w
