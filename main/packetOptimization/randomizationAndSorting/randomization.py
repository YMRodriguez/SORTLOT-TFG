import random
from main.packetAdapter.helpers import getAverageTaxability
from copy import deepcopy


# --------------- Helpers -----------------------------------------------------------
# This function randomly chooses a feasible orientation with equal probability
# Orientation equivalences (x, y, z) ---> |o1 -> (w, h, l) |
#                                        |o2 -> (l, h, w) |
#                                        |o3 -> (w, l, h) |
#                                        |o4 -> (h, l, w) |
#                                        |o5 -> (l, w, h) |
#                                        |o6 -> (h, w, l) |
def changeItemOrientation(item, validOrientations):
    orientation = random.choice(validOrientations)
    i = deepcopy(item)
    item["orientation"] = orientation
    if orientation == 2:
        item["width"] = i["length"]
        item["height"] = i["height"]
        item["length"] = i["width"]
    elif orientation == 3:
        item["width"] = i["width"]
        item["height"] = i["length"]
        item["length"] = i["height"]
    elif orientation == 4:
        item["width"] = i["height"]
        item["height"] = i["length"]
        item["length"] = i["width"]
    elif orientation == 5:
        item["width"] = i["length"]
        item["height"] = i["width"]
        item["length"] = i["height"]
    elif orientation == 6:
        item["width"] = i["height"]
        item["height"] = i["width"]
        item["length"] = i["length"]
    else:
        pass
    return item


# ------------------------- Comparators --------------------------------------
# This function compares the volume of two give items, returns true if is in range false otherwise
def volumeComp(i0, i1):
    return 0.8 < (i0["volume"] / i1["volume"]) < 1.2


# This function compares the weight of two give items, returns true if is in range false otherwise
def weightComp(i0, i1):
    return 0.8 < (i0["weight"] / i1["weight"]) < 1.2


# ------------------------------ Swappers --------------------------------------
# This function swaps the values of the given indexes in the list
def genericSwapper(lst, i, j):
    lst[i], lst[j] = lst[j], lst[i]


# This function swaps an item with its consecutive with 50% prob in case vi/vi+1 in [0.7, 1.3]
def swapByVolume(packets):
    for i in range(len(packets) - 1):
        if volumeComp(packets[i], packets[i + 1]) and bool(random.getrandbits(1)):
            genericSwapper(packets, i, i + 1)
    return packets


# This function swaps an item with its consecutive with 50% prob in case wi/wi+1 in [0.7, 1.3]
def swapByWeight(packets):
    for i in range(len(packets) - 1):
        if weightComp(packets[i], packets[i + 1]) and bool(random.getrandbits(1)):
            genericSwapper(packets, i, i + 1)
    return packets


def swapByPriority(packets):
    """
    This function swaps an item with another in the list with 50% prob if they have the
    same priority an destination code.

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
            genericSwapper(packets, i, j)
    return packets


# This function swaps an item with another item in the list with 50% prob if the item has a lower taxability than the
# average
def swapByTaxability(packets):
    for i in range(len(packets)):
        if packets[i]["taxability"] < getAverageTaxability(packets) and bool(random.getrandbits(1)):
            item_j = random.choice(packets[i:])
            j = packets.index(item_j)
            genericSwapper(packets, i, j)
    return packets


# ------------------- Main Function ---------------------------------------------------------------------
# This function is in charge of the randomization of a list of packets
def randomization(packets, validOrientations):
    random_oriented_packets = list(map(lambda x: changeItemOrientation(x, validOrientations), packets))
    swapped_v = swapByVolume(random_oriented_packets)
    swapped_w = swapByWeight(swapped_v)
    swapped_p = swapByPriority(swapped_w)
    # swapped_t = swapByTaxability(swapped_p)
    return swapped_p
