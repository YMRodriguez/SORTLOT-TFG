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


# This functions returns sorted items by a fitness function designed for the main sorting phase
def mainSortByFitness(items, avgWeight, avgTaxability, avgVolume, avgPriority, nDst):
    return sorted(items, key=lambda x:
    (x["taxability"] / avgTaxability + x["volume"] / avgVolume +
     x["weight"] / avgWeight + x["priority"] / avgPriority) *
     (1 - x["dst_code"] * 0.5 / nDst))


# ----------- Main function ----------------------------------
# This function is in charge of sorting the packets choosing the sorting method randomly.
def sortingPhase(items, nDst):
    avgWeight = getAverageWeight(items)
    avgVolume = getAverageVolume(items)
    avgTaxability = getAverageTaxability(items)
    avgPriority = getAveragePriority(items)
    return mainSortByFitness(items, avgWeight, avgTaxability, avgVolume, avgPriority, nDst)

    sorting_methods = [taxSorting, prioritySorting, customerSorting]
    return random.choice(sorting_methods)(items)
