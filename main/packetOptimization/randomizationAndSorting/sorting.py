import random
from main.packetAdapter.helpers import *


# ------------- Helpers ----------------------------------------


# -------------- Types -----------------------------------------
# This function will sort by decreasing taxability
def taxSorting(items):
    return {"sort_type": "tax", "solution": sorted(items, key=lambda x: x["taxability"], reverse=True)}


# This function will sort by decreasing priority level
def prioritySorting(items):
    return {"sort_type": "prior", "solution": sorted(items, key=lambda x: x["priority"], reverse=True)}


# This function will sort by decreasing customer code
# TODO, no confundir dst_code con el costumer_code para una ruta dada
def customerSorting(items):
    return {"sort_type": "cust", "solution": sorted(items, key=lambda x: x["dst_code"])}


# This function returns sorted items by a fitness function designed for the main sorting phase
def mainSortByFitness(items, avgWeight, avgTaxability, avgVolume, avgPriority, nDst):
    return sorted(items, key=lambda x: (x["taxability"] / avgTaxability + x["volume"] / avgVolume + x[
        "weight"] / avgWeight + x["priority"] / avgPriority) * (1 - x["dst_code"] * 0.5 / nDst), reverse=True)


# This function returns sorted items by a fitness function designed for the main sorting phase
def mainSortByFitnessPrime(items, maxWeight, maxTax, maxVol, maxPrio, nDst):
    return sorted(items, key=lambda x: (((x["taxability"] / maxTax) * 0.35 + (x["volume"] / maxVol) * 0.1 + (x[
        "weight"] / maxWeight) * 0.35 + (x["priority"] / maxPrio) * 0.2) * (1 - (x["dst_code"] * 0.8 / nDst))), reverse=True)


# This function returns sorted items based on a fitness function.
def refillingSortByFitness(items, maxWeight, maxTaxability, maxPrio, nDst):
    return sorted(items, key=lambda x: ((x["priority"]/maxPrio) * 0.5 + (x["taxability"] / maxTaxability)*0.25
                                        + (x["weight"] / maxWeight)*0.25) * (1 - (x["dst_code"] * 0.8 / nDst)),
                  reverse=True)


# ----------- Main functions ----------------------------------
# This function is in charge of sorting the packets choosing the sorting method randomly.
def sortingPhase(items, nDst):
    return mainSortByFitness(items, getAverageWeight(items),
                             getAverageTaxability(items), getAverageVolume(items),
                             getAveragePriority(items), nDst)


# This function is in charge of sorting the packets choosing the sorting method randomly.
def sortingPhasePrime(items, nDst):
    return mainSortByFitnessPrime(items, getMaxWeight(items),
                                  getMaxTaxability(items), getMaxVolume(items),
                                  getMaxPriority(items), nDst)


# This function returns sorted by a fitness function in resorting process.
def sortingRefillingPhase(items, nDst):
    return refillingSortByFitness(items, getMaxWeight(items),
                                  getMaxTaxability(items),
                                  getMaxPriority(items), nDst)
