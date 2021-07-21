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
                and packets[i]["dst_code"] == packets[i+1]["dst_code"]\
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
                and packets[i]["dst_code"] == packets[i+1]["dst_code"]\
                and bool(random.getrandbits(1)):
            genericSwapper(packets, i, i + 1)
    return packets


def swapByPriority(packets):
    """
    This function swaps an item with another in the list with 50% prob if they have the
    same priority and destination code.

    :param packets: list of packets.
    :return: modified list of packets.
    """
    for i in range(len(packets)):
        same_priority_packets = list(
            filter(lambda x: (x["priority"] == packets[i]["priority"]
                              and x["id"] != packets[i]["id"]
                              and x["dst_code"] == packets[i]["dst_code"]), packets))
        if bool(random.getrandbits(1)) and (len(same_priority_packets) != 0):
            item_j = random.choice(same_priority_packets)
            j = packets.index(item_j)
            if weightComp(packets[i], packets[j]) and volumeComp(packets[i], packets[j]):
                genericSwapper(packets, i, j)
    return packets


# ------------------- Main Function ---------------------------------------------------------------------
def randomization(packets):
    """
    This function randomizes packets based on weight, volume and priority criteria.

    :param packets: list of packets.
    :return: randomized list.
    """
    swapped_v = swapByVolume(packets)
    swapped_w = swapByWeight(swapped_v)
    return swapByPriority(swapped_w) if getMaxPriority(packets) else swapped_w
