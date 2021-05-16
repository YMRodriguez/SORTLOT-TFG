from joblib import Parallel, delayed, parallel_backend
import json
import time
from copy import deepcopy
from main.truckAdapter.adapter import adaptTruck
from main.packetAdapter.adapter import adaptPackets, cleanDestinationAndSource
from main.packetOptimization.randomizationAndSorting.randomization import randomization
from main.packetOptimization.randomizationAndSorting.sorting import sortingPhase, sortingPhasePrime
from main.packetOptimization.constructivePhase.mainCP import main_cp
from main.statistics.main import solutionStatistics, scenarioStatistics
from main.solutionsFilter.main import filterSolutions, getBest
from main.scenarios.dataSaver import persistInLocal
import glob
import os

# ----------------------- MongoDB extraction ----------------------
# # Connect to database
# myclient = pymongo.MongoClient("mongodb://localhost:27017/",
#                                username="mongoadmin",
#                                password="admin")
# db = myclient['SpainVRP']
# trucks_col = db['trucks']
#
# # Extract relevant data
# truck_var = trucks_col.find_one()
truck_var = json.load(open(os.path.dirname(__file__) + "/packetsDatasets/truckvar.json"))


# --------------- Packet Generator ------------------------------------------
def getDataFromJSONWith(Id):
    """
    This function gets a dataset file by its id.
    :param Id: the id of the dataset, not the name.
    :return: object mapped from json file.
    """
    filepath = glob.glob(os.path.dirname(__file__) + "/packetsDatasets/" + str(Id) + "*.json")[0]
    nDst = int(filepath.split("Datasets/")[1].split("-")[4][3])
    return json.load(open(filepath)), nDst


# -------------------- Main Processes -----------------------------
def main_scenario(packets, truck, nDst, prime, nIteration, rangeOrientations=None):
    if rangeOrientations is None:
        rangeOrientations = [1, 2, 3, 4]
    # ------ Packet adaptation------
    # Alpha is 333 for terrestrial transport
    packets = adaptPackets(cleanDestinationAndSource(packets), 333)
    # ------ Truck adaptation ------
    truck = adaptTruck(truck, 4)
    sort_output = sortingPhasePrime(packets, nDst) if prime else sortingPhase(packets, nDst)
    rand_output = randomization(deepcopy(sort_output), rangeOrientations)
    # ------- Solution builder --------
    startTime = time.time()
    iteration = main_cp(truck, rand_output, nDst)
    endTime = time.time()
    # It may be relevant to know the sorting method used.
    return {"placed": iteration["placed"],
            "discard": iteration["discard"],
            "truck": iteration["truck"],
            "sorted": sort_output,
            "rand": rand_output,
            "iteration": nIteration,
            "time": str(endTime - startTime)}


# ------------------ Translation of nested ndarrays -------------------
# TODO, this may go into a process data module which will be needed when implementing flask.
def serializePlacedItem(item):
    """
    This function adapts nested ndarrays in a object.
    :param item: item object.
    :return: item object with nested numpy arrays jsonified.
    """
    item["mass_center"] = item["mass_center"].tolist()
    item["subzones"] = item["subzones"].tolist()
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
        item["subzones"] = item["subzones"].tolist()
    return item


def serializeTruck(truck):
    """
    This function serializes ndarrays in object
    :param truck: truck object.
    :return: serialized object.
    """
    for s in truck["subzones"]:
        s['blf'] = s['blf'].tolist()
        s['brr'] = s['brr'].tolist()
    truck['pp'] = truck['pp'].tolist()
    #truck['_id'] = str(truck['_id'])
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
iterations = 64

# ------ Get packets dataset -------
ID = 5
items, ndst = getDataFromJSONWith(ID)

# ------ Iterations ------------
with parallel_backend(backend="loky", n_jobs=8):
    parallel = Parallel(verbose=100)
    solutions = parallel(
        [delayed(main_scenario)(deepcopy(items), deepcopy(truck_var), ndst, True, i) for i in range(iterations)])
    solutionsStats = list(map(lambda x: solutionStatistics(x), solutions))

    # ------- Process set of solutions --------
    # Clean solutions
    solutionsCleaned = list(map(lambda x: {"placed": x["placed"],
                                           "discard": x["discard"],
                                           "truck": x["truck"],
                                           "iteration": x["iteration"],
                                           "time": x["time"]}, solutions))

    # Get best filtered and unfiltered.
    serializedSolutions = serializeSolutions(solutionsCleaned)
    filteredSolutions, filteredStats = filterSolutions(serializedSolutions, solutionsStats)
    bestFiltered = getBest(filteredSolutions, filteredStats, 5)
    bestUnfiltered = getBest(solutionsCleaned, solutionsStats, 5)

    # Make it json serializable
    bestSolsFiltered = {"volume": bestFiltered["volume"][0],
                        "weight": bestFiltered["weight"][0],
                        "priority": bestFiltered["priority"][0],
                        "taxability": bestFiltered["taxability"][0]}
    bestStatsFiltered = {"volume": bestFiltered["volume"][1],
                         "weight": bestFiltered["weight"][1],
                         "priority": bestFiltered["priority"][1],
                         "taxability": bestFiltered["taxability"][1]}

    bestSolsUnfiltered = {"volume": bestUnfiltered["volume"][0],
                          "weight": bestUnfiltered["weight"][0],
                          "priority": bestUnfiltered["priority"][0],
                          "taxability": bestUnfiltered["taxability"][0]}
    bestStatsUnfiltered = {"volume": bestUnfiltered["volume"][1],
                           "weight": bestUnfiltered["weight"][1],
                           "priority": bestUnfiltered["priority"][1],
                           "taxability": bestUnfiltered["taxability"][1]}

    # TODO, determine best by looking at which one is in every characteristic.
    persistInLocal(bestSolsFiltered, bestStatsFiltered, bestSolsUnfiltered, bestStatsUnfiltered, ID)
