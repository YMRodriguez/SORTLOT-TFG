"""
author: Yamil Mateo Rodríguez
university: Universidad Politécnica de Madrid
"""

from joblib import Parallel, delayed, parallel_backend
import json
import time
import sys
from copy import deepcopy
from main.truckAdapter.adapter import adaptTruck
from main.packetAdapter.adapter import adaptPackets, cleanDestinationAndSource
from main.packetOptimization.randomizationAndSorting.randomization import randomization
from main.packetOptimization.randomizationAndSorting.sorting import sortingPhase
from main.packetOptimization.constructivePhase.mainCP import main_cp
from main.statistics.main import solutionStatistics
from main.solutionsFilter.main import filterSolutions, getBest, getUpdatedStatsWithConditions
from main.scenarios.dataSaver import persistInLocal, persistStats
import glob
import os

# ----------------------- MongoDB extraction ----------------------
truck_var = json.load(open(os.path.dirname(__file__) + os.path.sep + "packetsDatasets" + os.path.sep + "truckvar.json"))


# --------------- Packet Generator ------------------------------------------
def getDataFromJSONWith(filepath):
    """
    This function gets a dataset file by its id.

    :param filepath: the id of the dataset, not the name.
    :return: object mapped from json file and number of destinations.
    """
    nDst = int(filepath.split("round2" + os.path.sep)[1].split("-")[5][0])
    return json.load(open(filepath)), nDst


def getFilepaths():
    return glob.glob(os.path.dirname(
        __file__) + os.path.sep + "packetsDatasets" + os.path.sep + "articleDatasets" + os.path.sep + "round2" + os.path.sep + "*.json")


def getIdFromFilePath(filepath):
    return filepath.split(os.path.sep)[-1].split("-")[0] + "art"


# -------------------- Main Processes -----------------------------
def main_scenario(packets, truck, nDst, nIteration, coeffs, rangeOrientations=None):
    if rangeOrientations is None:
        rangeOrientations = [1, 2, 3, 4, 5, 6]
    # ------ Packet adaptation------
    # Alpha is 333 for terrestrial transport
    packets = adaptPackets(packets, 333)
    # ------ Truck adaptation ------
    truck = adaptTruck(truck, 4)
    sort_output = sortingPhase(packets, nDst, coeffs[:2])
    rand_output = randomization(deepcopy(sort_output), nDst)
    # ------- Solution builder --------
    startTime = time.time()
    iteration = main_cp(truck, rand_output, nDst, coeffs[2:])
    endTime = time.time()
    # It may be relevant to know the sorting method used.
    return {"placed": iteration["placed"],
            "discard": iteration["discard"],
            "truck": iteration["truck"],
            "potentialPoints": iteration["potentialPoints"],
            "sorted": sort_output,
            "rand": rand_output,
            "iteration": nIteration,
            "time": str(endTime - startTime)}


# ------------------ Translation of nested ndarrays -------------------
def serializePlacedItem(item):
    """
    This function adapts nested ndarrays in a object.

    :param item: item object.
    :return: item object with nested numpy arrays jsonified.
    """
    item["mass_center"] = item["mass_center"].tolist()
    item["subzones"] = item["subzones"]
    item["pp_in"] = item["pp_in"].tolist()
    item["pp_out"] = item["pp_out"].tolist()
    return item


def serializeDiscardItem(item):
    """
    This function adapts nested ndarrays in a object.

    :param item: item object.
    :return: item object with nested numpy arrays jsonified.
    """
    item["mass_center"] = item["mass_center"].tolist()
    if "subzones" in item:
        item["subzones"] = item["subzones"]
    return item


def serializeTruck(truck):
    """
    This function serializes ndarrays in object.

    :param truck: truck object.
    :return: serialized object.
    """
    for s in truck["subzones"]:
        s['blf'] = s['blf'].tolist()
        s['brr'] = s['brr'].tolist()
    truck['pp'] = truck['pp'].tolist()
    return truck


def serializeSolutions(sols):
    """
    This function serializes solution.

    :param: sols: list of solutions to be serialized.
    :return: serialized solution.
    """
    for s in sols:
        s["placed"] = list(map(lambda x: serializePlacedItem(x), s["placed"]))
        s["discard"] = list(map(lambda x: serializeDiscardItem(x), s["discard"]))
        s["truck"] = serializeTruck(s["truck"])
    return sols


# ------------------ Solution processing ----------------------------------
# ------ Common variables ----------
if len(sys.argv) > 1:
    try:
        iterations = int(sys.argv[1])
    except ValueError:
        iterations = 1

    try:
        cores = int(sys.argv[2])
    except ValueError:
        cores = 1

    try:
        expP1 = int(sys.argv[3])
    except ValueError:
        expP1 = 1

    try:
        expP2 = int(sys.argv[4])
    except ValueError:
        expP2 = expP1 + 1

else:
    iterations, expP1, expP2, cores = 3, 1, 2, 2


experiments = sorted(getFilepaths())

coefficients = [0.86, 0.53, 0.88, 0.98, 0.93, 0.97, 0.84, 0.67, 0.45, 0.64, 0.86, 0.45, 0.9, 0.96, 0.8, 0.88, 0.69]

for i in range(expP1, expP2):
    # ------ Get packets dataset -------
    items, ndst = getDataFromJSONWith(experiments[i])
    ID = getIdFromFilePath(experiments[i])

    # ------ Iterations ------------
    with parallel_backend(backend="loky", n_jobs=cores):
        parallel = Parallel(verbose=100)
        solutions = parallel(
            [delayed(main_scenario)(deepcopy(items), deepcopy(truck_var), ndst, i, coefficients) for i in range(iterations)])
        solutionsStats = list(map(lambda x: solutionStatistics(x), solutions))

        # ------- Process set of solutions --------
        # Clean solutions
        solutionsCleaned = list(map(lambda x: {"placed": x["placed"],
                                               "discard": x["discard"],
                                               "truck": x["truck"],
                                               "iteration": x["iteration"],
                                               "time": x["time"]}, solutions))
        updatedStats = getUpdatedStatsWithConditions(solutionsCleaned, solutionsStats)
        persistStats(updatedStats, ID)
        # Get best filtered and unfiltered.
        serializedSolutions = serializeSolutions(solutionsCleaned)
        filteredSolutions, filteredStats = filterSolutions(serializedSolutions, solutionsStats)
        bestFiltered = getBest(filteredSolutions, filteredStats, 3)
        bestUnfiltered = getBest(solutionsCleaned, solutionsStats, 3)

        # Make it json serializable
        bestSolsFiltered = {"volume": bestFiltered["volume"][0],
                            "weight": bestFiltered["weight"][0],
                            "taxability": bestFiltered["taxability"][0]}
        bestStatsFiltered = {"volume": bestFiltered["volume"][1],
                             "weight": bestFiltered["weight"][1],
                             "taxability": bestFiltered["taxability"][1]}
        bestSolsUnfiltered = {"volume": bestUnfiltered["volume"][0],
                              "weight": bestUnfiltered["weight"][0],
                              "taxability": bestUnfiltered["taxability"][0]}
        bestStatsUnfiltered = {"volume": bestUnfiltered["volume"][1],
                               "weight": bestUnfiltered["weight"][1],
                               "taxability": bestUnfiltered["taxability"][1]}

        persistInLocal(bestSolsFiltered, bestStatsFiltered, bestSolsUnfiltered, bestStatsUnfiltered, ID)
