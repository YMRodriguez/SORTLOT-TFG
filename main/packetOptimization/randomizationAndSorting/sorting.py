"""
author: Yamil Mateo Rodríguez
university: Universidad Politécnica de Madrid
"""

from main.packetAdapter.helpers import *


# -------------- Types -----------------------------------------

def mainSortByFitness(items, maxWeight, maxVol, maxPrio, nDst):
    """
    This function sorts items according to a fitness function.

    :param items: dictionary of objects representing the packets.
    :param maxWeight: maximum weight of the cargo.
    :param maxVol: maximum volume of the cargo.
    :param maxPrio: maximum priority of the cargo.
    :param nDst: number of destinations of the cargo.
    :return: sorted set of packets.
    """
    fitweights = [0.35, 0.4, 0.25] if maxPrio else [0.5, 0.5, 0]
    return sorted(items, key=lambda x: (((x["volume"] / maxVol) * fitweights[0] + (x[
                                                                                       "weight"] / maxWeight) *
                                         fitweights[1] + (x["priority"] / max(maxPrio, 1)) * fitweights[2]) + (
                                                    nDst - x["dstCode"])), reverse=True)


# This function returns sorted items based on a fitness function.
def refillingSortByFitness(items, maxWeight, maxPrio, maxVol, nDst):
    """
    This function sorts in the refilling phase according to a fitness function.

    :param items: dictionary of objects representing the packets.
    :param maxWeight: maximum weight of the cargo.
    :param maxVol: maximum volume of the cargo.
    :param maxPrio: maximum priority of the cargo.
    :param nDst: number of destinations of the cargo.
    :return: sorted set of packets.
    """
    fitweights = [0.25, 0.35, 0.4] if maxPrio else [0.5, 0.5, 0]
    return sorted(items, key=lambda x: (((x["volume"] / maxVol) + fitweights[0] +
                                         (x["weight"] / maxWeight) * fitweights[1] +
                                         (x["priority"] / max(maxPrio, 1)) * fitweights[2]) + (nDst - x["dstCode"])),
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
                             getMaxVolume(items),
                             getMaxPriority(items), nDst)


def sortingRefillingPhase(items, nDst):
    """
    This function handles the second sorting phase.

    :param items: dictionary of objects representing the packets.
    :param nDst: number of destinations of the cargo.
    :return: sorted set of packets.
    """
    return refillingSortByFitness(items, getMaxWeight(items),
                                  getMaxPriority(items),
                                  getMaxVolume(items), nDst)
