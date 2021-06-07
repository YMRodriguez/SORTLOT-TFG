import random
from main.packetAdapter.helpers import getAverageTaxability, getMaxPriority


# ------------------------- Comparators --------------------------------------
# This function compares the volume of two give items, returns true if is in range false otherwise
def volumeComp(i0, i1):
    return 0.85 < (i0["volume"] / i1["volume"]) < 1.15


# This function compares the weight of two give items, returns true if is in range false otherwise
def weightComp(i0, i1):
    return 0.85 < (i0["weight"] / i1["weight"]) < 1.15


# ------------------------------ Swappers --------------------------------------
# This function swaps the values of the given indexes in the list
def genericSwapper(lst, i, j):
    lst[i], lst[j] = lst[j], lst[i]


# This function swaps an item with its consecutive with 50% prob in case vi/vi+1 in [0.85, 1.15]
def swapByVolume(packets):
    for i in range(len(packets) - 1):
        if volumeComp(packets[i], packets[i + 1]) \
                and packets[i]["dst_code"] == packets[i+1]["dst_code"]\
                and bool(random.getrandbits(1)):
            genericSwapper(packets, i, i + 1)
    return packets


# This function swaps an item with its consecutive with 50% prob in case wi/wi+1 in [0.85, 1.15]
def swapByWeight(packets):
    for i in range(len(packets) - 1):
        if weightComp(packets[i], packets[i + 1]) \
                and packets[i]["dst_code"] == packets[i+1]["dst_code"]\
                and bool(random.getrandbits(1)):
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
            if weightComp(packets[i], packets[j]) and volumeComp(packets[i], packets[j]):
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
def randomization(packets):
    swapped_v = swapByVolume(packets)
    swapped_w = swapByWeight(swapped_v)
    return swapByPriority(swapped_w) if getMaxPriority(packets) else swapped_w
