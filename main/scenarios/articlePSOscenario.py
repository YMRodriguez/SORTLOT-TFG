"""
author: Yamil Mateo Rodríguez
university: Universidad Politécnica de Madrid
"""

from joblib import Parallel, delayed, parallel_backend
import json
import time
import sys
from copy import deepcopy
import numpy as np
from main.truckAdapter.adapter import adaptTruck
from main.packetAdapter.adapter import adaptPackets
from main.packetOptimization.randomizationAndSorting.randomization import randomization
from main.packetOptimization.randomizationAndSorting.sorting import sortingPhase
from main.packetOptimization.constructivePhase.mainCP import main_cp
from main.statistics.main import solutionStatistics
from main.solutionsFilter.main import filterSolutions, getBest, getUpdatedStatsWithConditions
from main.scenarios.dataSaver import persistInLocal, persistStats
import glob
import os
from pyswarms.backend.topology import Star
from pyswarms.backend.handlers import OptionsHandler
import pyswarms.backend as P


# ----------------------- MongoDB extraction ----------------------
truck_var = json.load(open(os.path.dirname(__file__) + os.path.sep + "packetsDatasets" + os.path.sep + "truckvar.json"))


# --------------- Packet Generator ------------------------------------------
def getDataFromJSONWith(filepath):
    """
    This function gets a dataset file by its id.

    :return: object mapped from json file and number of destinations.
    """
    nDst = int(filepath.split(os.path.sep)[-1].split("-")[5])
    return json.load(open(filepath)), nDst


def getFilepaths():
    return glob.glob(os.path.dirname(
        __file__) + os.path.sep + "packetsDatasets" + os.path.sep + "articleDatasets" + os.path.sep + "*.json")


def getIdFromFilePath(filepath):
    return filepath.split(os.path.sep)[-1].split("-")[0]


# -------------------- Main Processes -----------------------------
def main_scenario(packets, coefficients, truck, nDst, nIteration, rangeOrientations=None):
    if rangeOrientations is None:
        rangeOrientations = [1, 2, 3, 4, 5, 6]
    # ------ Packet adaptation------
    # Alpha is 333 for terrestrial transport
    packets = adaptPackets(packets, 333)
    # ------ Truck adaptation ------
    truck = adaptTruck(truck, 4)
    sort_output = sortingPhase(packets, nDst, coefficients[:2])
    rand_output = randomization(deepcopy(sort_output))
    # ------- Solution builder --------
    startTime = time.time()
    iteration = main_cp(truck, rand_output, nDst, coefficients[2:])
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
        exp = int(sys.argv[1])
    except ValueError:
        exp = 1
    try:
        iterations = int(sys.argv[2])
    except ValueError:
        iterations = 1
    try:
        cores = int(sys.argv[3])
    except ValueError:
        cores = 1
    try:
        psoIterations = int(sys.argv[4])
    except ValueError:
        psoIterations = 50
    try:
        particles = int(sys.argv[5])
    except ValueError:
        particles = 15
else:
    iterations, exp, cores, psoIterations, particles = 1, 0, 3, 50, 15


def objectiveFunction(coefficients, nParticles, expID, packets, nDst, truck, nCores=1):
    # Base list to put the cost function of each of the particles.
    costFunction = []
    for i in range(nParticles):
        # Repeat operation in case the cost is max due to no feasible solutions.
        costFunctionForParticle = computeAlgorithm(coefficients[i], expID, packets, nDst, truck, multIter=nCores, nCores=nCores)
        if costFunctionForParticle == 1:
            print("No feasible solution found for:" + str(coefficients))
            costFunctionForParticle = computeAlgorithm(coefficients[i], expID, packets, nDst, truck, multIter=nCores*2, nCores=nCores)
            print("Computed another 3 solutions for particle and the cost was " + str(costFunctionForParticle))
        costFunction.append(costFunctionForParticle)
    return costFunction


def computeAlgorithm(coefficients, expID, packets, nDst, truck, multIter=1, nCores=1):
    # ------ Iterations ------------
    with parallel_backend(backend="loky", n_jobs=nCores):
        parallel = Parallel(verbose=100)
        solutions = parallel(
            [delayed(main_scenario)(deepcopy(packets), coefficients, deepcopy(truck), nDst, i) for i in range(multIter)])
        solutionsStats = list(map(lambda x: solutionStatistics(x), solutions))

        # ------- Process set of solutions --------
        # Clean solutions
        solutionsCleaned = list(map(lambda x: {"placed": x["placed"],
                                               "discard": x["discard"],
                                               "truck": x["truck"],
                                               "iteration": x["iteration"],
                                               "time": x["time"]}, solutions))
        # ------------- Iterations data -------------------------
        updatedStats = getUpdatedStatsWithConditions(solutionsCleaned, solutionsStats)
        # Keep stats of all iterations, useful for graphics.
        persistStats(updatedStats, ID)
        # -------------------------------------------------------
        # Get best filtered and unfiltered.
        serializedSolutions = serializeSolutions(solutionsCleaned)
        filteredSolutions, filteredStats = filterSolutions(serializedSolutions, solutionsStats)
        bestFiltered = getBest(filteredSolutions, filteredStats, 5)
        bestUnfiltered = getBest(solutionsCleaned, solutionsStats, 5)

        # Get the average volume of the iterations.
        averageVolume = sum([j["used_volume"] for j in solutionsStats]) / multIter
        # Let's check if there is any feasible solution.
        feasibleSols = len(filteredSolutions)
        # Opposite to volume occupation.
        costFunction = 1 - averageVolume if feasibleSols else 1

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

        persistInLocal(bestSolsFiltered, bestStatsFiltered, bestSolsUnfiltered, bestStatsUnfiltered, expID)
    return costFunction


def performPSO(expID, packets, nDst, truck, nParticles, nPSOiters, nCores):
    # ---------- Swarm structure creation ------------------------
    topology = Star()
    initPositionsList = [0.8, 0.2, 0.55, 0.45, 0.35, 0.25, 0.4, 0.45, 0.45, 0.05, 0.05, 0.3, 0.5, 0.1, 0.1]
    initPositions = np.tile(initPositionsList, (particles, 1))
    bounds = (np.zeros(15), np.ones(15))
    opHandler = OptionsHandler(strategy={"w": "lin_variation"})
    options = {"w": 0.9, "c1": 0.5, "c2": 0.3}

    mySwarm = P.create_swarm(n_particles=nParticles, dimensions=15, options=options, bounds=bounds, init_pos=initPositions)
    for p in range(nPSOiters):
        # Part 1: Update personal best
        mySwarm.current_cost = objectiveFunction(mySwarm.position, particles, expID, packets, nDst, truck, nCores)  # Compute current cost
        mySwarm.pbest_cost = objectiveFunction(mySwarm.pbest_pos, particles, expID, packets, nDst, truck, nCores)  # Compute personal best pos
        mySwarm.pbest_pos, mySwarm.pbest_cost = P.compute_pbest(mySwarm)  # Update and store

        # Part 2: Update global best
        # Note that gbest computation is dependent on your topology
        if np.min(mySwarm.pbest_cost) < mySwarm.best_cost:
            mySwarm.best_pos, mySwarm.best_cost = topology.compute_gbest(mySwarm)

        # Let's print our output
        if p % 20 == 0:
            print('Iteration: {} | my_swarm.best_cost: {:.4f}'.format(p + 1, mySwarm.best_cost))

        # Part 3: Update position and velocity matrices
        # Note that position and velocity updates are dependent on your topology
        mySwarm.velocity = topology.compute_velocity(mySwarm)
        mySwarm.position = topology.compute_position(mySwarm)
        mySwarm.options = opHandler(options, iternow=p, itermax=nPSOiters)
        print("-----------------")
        print("Iteration " + str(p) + " of the PSO completed")
        print("Current cost is: " + mySwarm.best_cost)
        print("Best cost is: " + mySwarm.best_cost)
        print("-----------------")

    print('The best cost found by our swarm is: {:.4f}'.format(mySwarm.best_cost))
    print('The best position found by our swarm is: {}'.format(mySwarm.best_pos))


# ---------- Experiments ------------------------------------
experiments = getFilepaths()
IDs = []
itemsByExp = []
nDstByExp = []

# ------ Get packets dataset -------
for j in experiments:
    ID = getIdFromFilePath(j)
    IDs.append(ID)
    items, ndst = getDataFromJSONWith(j)
    itemsByExp.append(items)
    nDstByExp.append(ndst)

for a, b, c in zip(IDs, itemsByExp, nDstByExp):
    performPSO(a, b, c, truck_var, particles, psoIterations, cores)
