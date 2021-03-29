import random
from main.packetAdapter.adapter import getAverageTaxability


# --------------- Helpers -----------------------------------------------------------
# This function randomly chooses a feasible orientation with equal probability
# Orientation equivalences (x, y, z) ---> |o1 -> (w, h, l) |
#                                        |o2 -> (l, h, w) |
#                                        |o3 -> (w, l, h) |
#                                        |o4 -> (h, l, w) |
#                                        |o5 -> (l, w, h) |
#                                        |o6 -> (h, w, l) |
def changeItemOrientation(item):
    orientation = random.randint(0, 6)
    i = item.copy()
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
    if 0.7 < (i0["volume"] / i1["volume"]) < 1.3:
        return True
    return False


# This function compares the weight of two give items, returns true if is in range false otherwise
def weightComp(i0, i1):
    if 0.7 < (i0["weight"] / i1["weight"]) < 1.3:
        return True
    return False


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


# This function swaps an item with another item in the list with 50% prob if they have the same level of priority
def swapByPriority(packets):
    for i in range(len(packets)):
        same_priority_packets = list(
            filter(lambda x: (x["priority"] == packets[i]["priority"] and x["id"] != packets[i]["id"]), packets))
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
def randomization(packets):
    random_oriented_packets = list(map(lambda x: changeItemOrientation(x), packets))
    swapped_v = swapByVolume(random_oriented_packets)
    swapped_w = swapByWeight(swapped_v)
    swapped_p = swapByPriority(swapped_w)
    swapped_t = swapByTaxability(swapped_p)
    return swapped_t