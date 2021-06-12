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
def mainSortByFitnessPrime(items, maxWeight, maxVol, maxPrio, nDst):
    fitweights = [0.35, 0.4, 0.25] if maxPrio else [0.5, 0.5, 0]
    print(nDst)
    return sorted(items, key=lambda x: (((x["volume"] / maxVol) * fitweights[0] + (x[
        "weight"] / maxWeight) * fitweights[1] + (x["priority"] / max(maxPrio, 1)) * fitweights[2]) + (nDst - x["dst_code"])), reverse=True)


# This function returns sorted items based on a fitness function.
def refillingSortByFitness(items, maxWeight, maxPrio, maxVol, nDst):
    fitweights = [0.15, 0.15, 0.7] if maxPrio else [0.5, 0.5, 0]
    return sorted(items, key=lambda x: (((x["volume"] / maxVol) + fitweights[0] +
                                        (x["weight"] / maxWeight) * fitweights[1] +
                                        (x["priority"]/max(maxPrio, 1)) * fitweights[2]) * (1 - (x["dst_code"] / (nDst-1)))), reverse=True)


# ----------- Main functions ----------------------------------
# This function is in charge of sorting the packets choosing the sorting method randomly.
def sortingPhasePrime(items, nDst):
    return mainSortByFitnessPrime(items, getMaxWeight(items),
                                  getMaxVolume(items),
                                  getMaxPriority(items), nDst)


# This function returns sorted by a fitness function in resorting process.
def sortingRefillingPhase(items, nDst):
    return refillingSortByFitness(items, getMaxWeight(items),
                                  getMaxPriority(items),
                                  getMaxVolume(items), nDst)
