"""
author: Yamil Mateo Rodríguez
university: Universidad Politécnica de Madrid
"""

from main.packetAdapter.helpers import *


# -------------- Types -----------------------------------------

def mainSortByFitness(items, maxWeight, maxPrio, nDst):
    """
    This function sorts items according to a fitness function.

    :param items: dictionary of objects representing the packets.
    :param maxWeight: maximum weight of the cargo.
    :param maxVol: maximum volume of the cargo.
    :param maxPrio: maximum priority of the cargo.
    :param nDst: number of destinations of the cargo.
    :return: sorted set of packets.
    """
    fitweights = [0.8, 0.2] if maxPrio else [0.5, 0]
    return sorted(items, key=lambda x: (((x["weight"] / maxWeight) *
                                         fitweights[0] + (x["priority"] / max(maxPrio, 1)) * fitweights[1]) + (
                                                nDst - x["dstCode"])), reverse=True)


def refillingSortByFitness(nonPackedItems, maxWeight, maxPrio, packedItems, subgroupingCond, nDst):
    """
    This function sorts in the refilling phase according to a fitness function.

    :param items: dictionary of objects representing the packets.
    :param maxWeight: maximum weight of the cargo.
    :param maxVol: maximum volume of the cargo.
    :param maxPrio: maximum priority of the cargo.
    :param nDst: number of destinations of the cargo.
    :return: sorted set of packets.
    """
    if subgroupingCond:
        subgroups = list(map(lambda x: x["subgroupId"], packedItems))
        fitweights = [0.2, 0.4, 0.4] if maxPrio else [0.5, 0.5, 0]
        return sorted(nonPackedItems, key=lambda x: (int(x["subgroupId"] in subgroups) * fitweights[0]) + (
                ((x["weight"] / maxWeight) * fitweights[1] + (x["priority"] / max(maxPrio, 1)) * fitweights[2]) + (
                nDst - x["dstCode"])),
                      reverse=True)
    else:
        fitweights = [0.55, 0.45] if maxPrio else [1, 0]
        return sorted(nonPackedItems, key=lambda x: (((x["weight"] / maxWeight) * fitweights[0] +
                                                      (x["priority"] / max(maxPrio, 1)) * fitweights[1]) + (
                                                             nDst - x["dstCode"])),
                      reverse=True)


# ----------- Main functions ----------------------------------
def sortingPhase(items, nDst):
    """
    This function handles the sorting phase.

    :param items: dictionary of objects representing the packets.
    :param nDst: number of destinations of the cargo.
    :return: sorted set of packets.
    """
    return mainSortByFitness(items, getMaxWeight(items),
                             getMaxPriority(items), nDst)


def sortingRefillingPhase(nonPackedItems, packedItems, subgroupingCondition, nDst):
    """
    This function handles the second sorting phase.

    :param items: dictionary of objects representing the packets.
    :param nDst: number of destinations of the cargo.
    :return: sorted set of packets.
    """
    return refillingSortByFitness(nonPackedItems, getMaxWeight(nonPackedItems),
                                  getMaxPriority(nonPackedItems), packedItems, subgroupingCondition, nDst)
