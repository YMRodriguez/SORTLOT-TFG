import random
from main.packetAdapter.helpers import *


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
def mainSortByFitnessPrime(items, maxWeight, maxVol, maxPrio, nDst):
    return sorted(items, key=lambda x: (((x["volume"] / maxVol) * 0.35 + (x[
        "weight"] / maxWeight) * 0.35 + (x["priority"] / max(maxPrio, 1)) * 0.3) * (1 - (x["dst_code"] * 0.8 / nDst))), reverse=True)


# This function returns sorted items based on a fitness function.
def refillingSortByFitness(items, maxWeight, maxPrio, maxVol, nDst, stage):
    weights = [[0.35, 0.25, 0.4], [0.3, 0.3, 0.4], [0.25, 0.25, 0.5]]
    weightsByStage = weights[1] #TODO
    return sorted(items, key=lambda x: (((x["volume"] / maxVol) + weightsByStage[0] +
                                        (x["weight"] / maxWeight) * weightsByStage[1] +
                                        (x["priority"]/max(maxPrio, 1)) * weightsByStage[2]) * (1 - (x["dst_code"] * 0.8 / nDst))), reverse=True)


# ----------- Main functions ----------------------------------
# This function is in charge of sorting the packets choosing the sorting method randomly.
def sortingPhase(items, nDst):
    return mainSortByFitness(items, getAverageWeight(items),
                             getAverageTaxability(items), getAverageVolume(items),
                             getAveragePriority(items), nDst)


# This function is in charge of sorting the packets choosing the sorting method randomly.
def sortingPhasePrime(items, nDst):
    return mainSortByFitnessPrime(items, getMaxWeight(items),
                                  getMaxVolume(items),
                                  getMaxPriority(items), nDst)


# This function returns sorted by a fitness function in resorting process.
def sortingRefillingPhase(items, nDst, stage):
    return refillingSortByFitness(items, getMaxWeight(items),
                                  getMaxPriority(items),
                                  getMaxVolume(items), nDst, stage)
