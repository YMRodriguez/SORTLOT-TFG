"""
author: Yamil Mateo Rodríguez
university: Universidad Politécnica de Madrid
"""

from main.packetAdapter.helpers import *


# -------------- Types -----------------------------------------

def sortByFitness(items, maxWeight, maxVolume, maxPrio, nDst, coefficients):
    """
    This function sorts items according to a fitness function.

    :param items: array of objects representing the packets.
    :param maxWeight: maximum weight of the cargo.
    :param maxPrio: maximum priority of the cargo.
    :param nDst: number of destinations of the cargo.
    :return: sorted set of packets.
    """
    fitweights = coefficients if maxPrio else [1, 0]
    return sorted(items, key=lambda x: ((((x["weight"] / maxWeight * 0.5 + x["volume"] / maxVolume * 0.5) *
                                          fitweights[0]) + (x["priority"] / max(maxPrio, 1)) * fitweights[1]) + (
                                                nDst - x["dstCode"])), reverse=True)


def reSortByFitness(nonPackedItems, maxWeight, packedItems, subgroupingCond, nDst, coefficients):
    """
    This function sorts after the base has been loaded. It also reduces subgrouping condition to priority.

    :param subgroupingCond: True if subgrouping considered, False otherwise.
    :param packedItems: array of already packed items.
    :param nonPackedItems: array of objects representing the packets.
    :param maxWeight: maximum weight of the cargo.
    :param nDst: number of destinations of the cargo.
    :return: sorted set of packets.
    """
    if subgroupingCond:
        # Get the subgroups that have been already packed.
        packedSubgroups = list(map(lambda x: x["subgroupId"], packedItems))
        for i in nonPackedItems:
            # Simplification of conditions. From subgrouping to priority.
            if i["subgroupId"] in packedSubgroups:
                # TODO, should be maxPrio but the case of active subgrouping and no priority is a non-working exception.
                i["priority"] = 1
    maxPrio = getMaxPriority(nonPackedItems)
    fitweights = coefficients if maxPrio else [1, 0]
    return sorted(nonPackedItems, key=lambda x: (((x["weight"] / maxWeight) * fitweights[0] +
                                                  (x["priority"] / max(maxPrio, 1)) * fitweights[1]) + (
                                                         nDst - x["dstCode"])),
                  reverse=True)


# ----------- Main functions ----------------------------------
def sortingPhase(items, nDst, coefficients):
    """
    This function handles the sorting phase.

    :param items: dictionary of objects representing the packets.
    :param nDst: number of destinations of the cargo.
    :return: sorted set of packets.
    """
    return sortByFitness(items, getMaxWeight(items), getMaxVolume(items),
                         getMaxPriority(items), nDst, coefficients)


def reSortingPhase(nonPackedItems, packedItems, subgroupingCond, nDst, coefficients):
    """
    This function handles the second sorting phase.

    :param subgroupingCond: True if subgrouping considered, False otherwise.
    :param packedItems: array of already packed items.
    :param nonPackedItems: array of objects representing the packets.
    :param nDst: number of destinations of the cargo.
    :return: sorted set of packets.
    """
    return reSortByFitness(nonPackedItems, getMaxWeight(nonPackedItems), packedItems, subgroupingCond, nDst, coefficients)
