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
from flask import Flask, request, jsonify

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
    if iteration is None:
        return iteration
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

def run_optimizer(container, items, destinations, iterations=1, cores=1):
    coefficients = [0.23, 0.01, 0.7, 0.86, 0.17, 0.8, 0.76, 0.55, 0.3, 0.92, 0.92, 0.33, 0.34, 0.75, 0.37, 0.6, 0.79]
    # ------ Iterations ------------
    with parallel_backend(backend="loky", n_jobs=cores):
        parallel = Parallel(verbose=100)
        solutions = parallel(
            [delayed(main_scenario)(deepcopy(items), deepcopy(container), destinations, i, coefficients) for i in range(iterations)])
        notNoneSolutions = list(filter(lambda x: x is not None, solutions))
        if len(notNoneSolutions):
            solutionsStats = list(map(lambda x: solutionStatistics(x), notNoneSolutions))

            # ------- Process set of solutions --------
            # Clean solutions
            solutionsCleaned = list(map(lambda x: {"placed": x["placed"],
                                                   "discard": x["discard"],
                                                   "truck": x["truck"],
                                                   "iteration": x["iteration"],
                                                   "time": x["time"]}, notNoneSolutions))

            updatedStats = getUpdatedStatsWithConditions(solutionsCleaned, solutionsStats)
            # Get best filtered and unfiltered.
            serializedSolutions = serializeSolutions(solutionsCleaned)
            filteredSolutions, filteredStats = filterSolutions(serializedSolutions, solutionsStats)
            bestFiltered = getBest(filteredSolutions, filteredStats, 3)
            bestUnfiltered = getBest(solutionsCleaned, solutionsStats, 3)

            # Make it json serializable
            bestSolsFiltered = bestFiltered["volume"][0]
            bestStatsFiltered = bestFiltered["volume"][1]
            bestSolsUnfiltered = bestUnfiltered["volume"][0]
            bestStatsUnfiltered = bestUnfiltered["volume"][1]
            return {"solutions": bestSolsFiltered, "stats": bestStatsFiltered,
                    "solutionsUnfiltered": bestSolsUnfiltered, "statsUnfiltered": bestStatsUnfiltered}
        else:
            return {"error": "no solution"}
