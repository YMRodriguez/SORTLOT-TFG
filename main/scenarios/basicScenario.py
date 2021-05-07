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
from main.statistics.main import solution_statistics
from main.solutionsFilter.main import filterSolutions
import glob
import os


# ----------------------- MongoDB extraction ----------------------
# Connect to database
myclient = pymongo.MongoClient("mongodb://localhost:27017/",
                               username="mongoadmin",
                               password="admin")
db = myclient['SpainVRP']
wharehouses_col = db['wharehouses']
trucks_col = db['trucks']

# Extract relevant data
truck_var = trucks_col.find_one()
wharehouses_titles = list(map(lambda x: x["name"], wharehouses_col.find({}, {'_id': 0, 'name': 1})[5:12]))
# Adapt data to input in generator
src = wharehouses_titles[0]
destinations = wharehouses_titles[1:]


# --------------- Packet Generator ------------------------------------------
# This function returns an array of json from an ID of a dataset.
def getDataFromJSONWith(Id):
    filepath = glob.glob(".packetsDatasets/" + str(ID) + "*.json")[0]
    nDst = filepath.split("Datasets/")[1].split("-")[4]
    return json.load(open(filepath)), nDst


# -------------------- Main Processes -----------------------------
def main_scenario(packets, truck, nDst, prime, rangeOrientations=None):
    # ------ Packet adaptation------
    # Alpha is 333 for terrestrial transport
    if rangeOrientations is None:
        rangeOrientations = [1, 2, 3, 4]
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
            "time": str(endTime-startTime)}


# ------------------ Translation to Application -------------------
def adaptNdarrayToList(item):
    item["mass_center"] = item["mass_center"].tolist()
    item["subzones"] = item["subzones"].tolist()
    item["pp_in"] = item["pp_in"].tolist()
    item["pp_out"] = item["pp_out"].tolist()
    return item


# ------------------ Solution processing --------------------------
# Common variables
solutions = []
solutionsStatistics = []
iterations = 100

# Get packets dataset
ID = 1
items, nDst = getDataFromJSONWith(ID)

# Iterations
for i in range(iterations):
    solution = main_scenario(deepcopy(items), truck_var, nDst, prime=False)
    solutions.append(solution)
    solutionStatistics = solution_statistics(solution["solution"])
    solutionsStatistics.append(solutionStatistics)

# Clean set of solutions
bestSolutions, bestStatistics = filterSolutions(solutions, solutionsStatistics)
serializableSolutionPlaced = deepcopy(solution["solution"]["placed"])
serializableSolutionPlaced = list(map(lambda x: adaptNdarrayToList(x), serializableSolutionPlaced))
with open(
        '/Users/yamilmateorodriguez/Developtment/TFG/3DBinPacking-VisualizationTool/web-3dbp-visualization/src/placedpackets.json',
        'w') as file:
    json.dump(serializableSolutionPlaced, file, ensure_ascii=False)
