import pandas as pd
import json
import time
import pymongo
from copy import deepcopy
from main.truckAdapter.adapter import adaptTruck
from main.packetAdapter.adapter import adaptPackets
from main.packetOptimization.randomizationAndSorting.randomization import randomization
from main.packetOptimization.randomizationAndSorting.sorting import sortingPhase, sortingPhasePrime
from main.packetOptimization.constructivePhase.mainCP import main_cp
from main.statistics.main import solutionStatistics, scenarioStatistics
from main.solutionsFilter.main import filterSolutions, getBest
import glob

# ----------------------- MongoDB extraction ----------------------
# Connect to database
myclient = pymongo.MongoClient("mongodb://localhost:27017/",
                               username="mongoadmin",
                               password="admin")
db = myclient['SpainVRP']
trucks_col = db['trucks']

# Extract relevant data
truck_var = trucks_col.find_one()


# --------------- Packet Generator ------------------------------------------
def getDataFromJSONWith(Id):
    """
    This function gets a dataset file by its id.
    :param Id: the id of the dataset, not the name.
    :return: object mapped from json file.
    """
    filepath = glob.glob("./scenarios/packetsDatasets/" + str(Id) + "*.json")[0]
    nDst = int(filepath.split("Datasets/")[1].split("-")[4][3])
    return json.load(open(filepath)), nDst


# -------------------- Main Processes -----------------------------
def main_scenario(packets, truck, nDst, prime, nIteration, rangeOrientations=None):
    if rangeOrientations is None:
        rangeOrientations = [1, 2, 3, 4]
    # ------ Packet adaptation------
    # Alpha is 333 for terrestrial transport
    packets = adaptPackets(packets, 333)
    # ------ Truck adaptation ------
    truck = adaptTruck(truck, 4)
    sort_output = sortingPhasePrime(packets, nDst) if prime else sortingPhase(packets, nDst)
    rand_output = randomization(deepcopy(sort_output), rangeOrientations)
    # ------- Solution builder --------
    startTime = time.time()
    iteration = main_cp(truck, rand_output)
    endTime = time.time()
    # It may be relevant to know the sorting method used.
    return {"solution": iteration,
            "sorted": sort_output,
            "rand": rand_output,
            "iteration": nIteration,
            "time": str(endTime - startTime)}


# ------------------ Translation of nested ndarrays -------------------
# TODO, this may go into a process data module which will be needed when implementing flask.
def serializeItem(item):
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


def serializeSolution(sol):
    """
    This function serializes solution.
    :param: sol: list of solutions to be serialized.
    :return: serialized solution.
    """
    return list(map(lambda y: list(map(lambda z: serializeItem(z), y)),
                    list(map(lambda x: x["solution"]["placed"], sol))))


# ------------------ Solution processing ----------------------------------
# ------ Common variables ----------
solutions = []
solutionsStats = []
iterations = 1

# ------ Get packets dataset -------
ID = 1
items, ndst = getDataFromJSONWith(ID)

# ------ Iterations ------------
for i in range(iterations):
    solution = main_scenario(deepcopy(items), truck_var, ndst, False, i)
    solutions.append(solution)
    solutionStats = solutionStatistics(solution["solution"], solution["iteration"], solution["time"])
    solutionsStats.append(solutionStats)

# ------- Process set of solutions --------
# Clean solutions
solutionsCleaned = list(map(lambda x: {"solution": x["solution"],
                                       "iteration": x["iteration"],
                                       "time": x["time"]}, deepcopy(solutions)))

# Get best filtered and unfiltered.
serializedSolutions = list(map(lambda x: serializeSolution(x), solutionsCleaned))
filteredSolutions, filteredStats = filterSolutions(serializedSolutions, solutionsStats)
bestFiltered = getBest(filteredSolutions, filteredStats, 5)
bestUnfiltered = getBest(solutionsCleaned, solutionsStats, 5)

# Make it json serializable
bestSolsFiltered = bestFiltered["volume"][0] + bestFiltered["weight"][0] + \
                   bestFiltered["priority"][0] + bestFiltered["taxability"][0]
bestStatsFiltered = bestFiltered["volume"][1] + bestFiltered["weight"][1] + \
                    bestFiltered["priority"][1] + bestFiltered["taxability"][1]

bestSolsUnfiltered = bestUnfiltered["volume"][0] + bestUnfiltered["weight"][0] + \
                     bestUnfiltered["priority"][0] + bestUnfiltered["taxability"][0]
bestSolsUnfilteredSerialized = serializeSolution(bestSolsUnfiltered)
bestStatsUnfiltered = bestUnfiltered["volume"][0] + bestUnfiltered["weight"][0] + \
                      bestUnfiltered["priority"][0] + bestUnfiltered["taxability"][0]

# # Pass the data to visualization. This will be made in a flask api not in local.
# with open(
#         '/Users/yamilmateorodriguez/Developtment/TFG/3DBinPacking-VisualizationTool/web-3dbp-visualization/src/' + ID + 'bestUnfilteredSols.json',
#         'w') as file:
#     json.dump(
#         list(map(lambda x: list(map(lambda y: serializeSolution(y), x["solution"]["placed"]), bestUnfilteredSolsWO))),
#         file, ensure_ascii=False)
#
# with open(
#         '/Users/yamilmateorodriguez/Developtment/TFG/3DBinPacking-VisualizationTool/web-3dbp-visualization/src/' + ID + 'bestUnFilteredStats.json',
#         'w') as file:
#     json.dump(serializableSolutionPlaced, file, ensure_ascii=False)
#
# with open(
#         '/Users/yamilmateorodriguez/Developtment/TFG/3DBinPacking-VisualizationTool/web-3dbp-visualization/src/' + ID + 'bestFilteredSols.json',
#         'w') as file:
#     json.dump(serializableSolutionPlaced, file, ensure_ascii=False)
#
# with open(
#         '/Users/yamilmateorodriguez/Developtment/TFG/3DBinPacking-VisualizationTool/web-3dbp-visualization/src/' + ID + 'bestUnfilteredStats.json',
#         'w') as file:
#     json.dump(serializableSolutionPlaced, file, ensure_ascii=False)
