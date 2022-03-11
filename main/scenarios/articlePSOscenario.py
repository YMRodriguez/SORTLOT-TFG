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
from main.scenarios.dataSaver import persistInLocal, persistStats, logBestPSOExperiment, logPSOHistory
import glob
import os
from pyswarms.backend.topology import Star
from pyswarms.backend.handlers import OptionsHandler, VelocityHandler, BoundaryHandler
import pyswarms.backend as P
import logging
from mlflow.tracking import MlflowClient

logging.basicConfig(filename='pso.log', filemode='w', format='%(levelname)s - %(message)s')

client = MlflowClient(tracking_uri="http://com31.dit.upm.es:8889")
expMlflow = client.get_experiment_by_name("pruebaInicial444")

if not expMlflow:
    expMlflow = client.create_experiment("pruebaInicial444")
else:
    expMlflow = expMlflow.experiment_id
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
if len(sys.argv) > 1:
    try:
        exp = int(sys.argv[0])
    except ValueError:
        exp = 1
    try:
        iterations = int(sys.argv[1])
    except ValueError:
        iterations = 1
    try:
        cores = int(sys.argv[2])
    except ValueError:
        cores = 1
    try:
        psoIterations = int(sys.argv[3])
    except ValueError:
        psoIterations = 50
    try:
        particles = int(sys.argv[4])
    except ValueError:
        particles = 30
else:
    exp, cores, psoIterations, particles = 0, 20, 300, 30


def processParticle(i, coefficients, nParticles, expID, packets, nDst, truck, genRun, bestPositions, current):
    particle_run = None
    if current:
        # Set particle child in generation.
        particle_run = client.create_run(expMlflow)
        client.set_tag(particle_run.info.run_id, "mlflow.parentRunId", genRun.info.run_id)
        client.log_param(particle_run.info.run_id, "particleId", str(i))
        client.log_param(particle_run.info.run_id, "currentPosition", str(coefficients[i]))
        # This will show best position without the current generation taken into account.
        client.log_param(particle_run.info.run_id, "bestPositionPrev", str(bestPositions[i]))

    logging.info("Started execution of particle " + str(i + 1) + " out of " + str(nParticles))
    # Max. resources by doing as many iterations as cores being used.
    costFunctionForParticle = computeAlgorithm(coefficients[i], expID, packets, nDst, truck, particle_run)
    # Repeat operation in case the cost is max. caused by no feasible solutions provided.
    if costFunctionForParticle == 1:
        logging.warning("No feasible solution found for: " + str(coefficients) + " in particle " + str(i))
        costFunctionForParticle = computeAlgorithm(coefficients[i], expID, packets, nDst, truck, particle_run)
        logging.info("Computed new set of solutions and the cost was " + str(costFunctionForParticle))
    logging.info("CURRENTC " if current else "BESTC " + "Finished execution of particle " + str(i + 1) + " out of " + str(nParticles))
    if particle_run is not None:
        client.set_terminated(particle_run.info.run_id)
    return costFunctionForParticle


def objectiveFunction(coefficients, nParticles, expID, packets, nDst, truck, genRun, nCores, bestPositions, current):
    with parallel_backend(backend="loky", n_jobs=nCores):
        parallel = Parallel(verbose=100)
        # Computation for each particle.
        costFunction = parallel(
            [delayed(processParticle)(i, coefficients, nParticles, expID, packets, nDst, truck, genRun, bestPositions, current) for i in
             range(nParticles)])
    return np.array(costFunction)


def computeAlgorithm(coefficients, expID, packets, nDst, truck, particleRun, saveStats=False):
    def logMetrics(noFair):
        if noFair and particleRun is not None:
            client.log_metric(particleRun.info.run_id, "cost", 1)
            client.log_metric(particleRun.info.run_id, "avgVolume", 0)
            client.log_metric(particleRun.info.run_id, "feasibleSols", 0)
        if not noFair and particleRun is not None:
            client.log_metric(particleRun.info.run_id, "cost", costFunction)
            client.log_metric(particleRun.info.run_id, "avgVolume", averageVolume)
            client.log_metric(particleRun.info.run_id, "feasibleSols", feasibleSols)
    # ------ Iterations ------------
    solutions = [main_scenario(deepcopy(packets), coefficients, deepcopy(truck), nDst, 0)]

    # The has been no fair distribution.
    if solutions[0] is None:
        logMetrics(True)
        return 1

    solutionsStats = list(map(lambda x: solutionStatistics(x), solutions))
    # ------- Process set of solutions
    # Clean solutions
    solutionsCleaned = list(map(lambda x: {"placed": x["placed"],
                                           "discard": x["discard"],
                                           "truck": x["truck"],
                                           "iteration": x["iteration"],
                                           "time": x["time"]}, solutions))
    # ------------- Iterations data -------------------------
    updatedStats = getUpdatedStatsWithConditions(solutionsCleaned, solutionsStats)

    if saveStats:
        # Keep stats of all iterations, useful for graphics. TODO, not needed now
        persistStats(updatedStats, expID)
    # -------------------------------------------------------
    # Get best filtered and unfiltered.
    serializedSolutions = serializeSolutions(solutionsCleaned)
    filteredSolutions, filteredStats = filterSolutions(serializedSolutions, solutionsStats)
    if saveStats:
        bestFiltered = getBest(filteredSolutions, filteredStats, 5)
        bestUnfiltered = getBest(solutionsCleaned, solutionsStats, 5)

    # Get the average volume of the iterations.
    averageVolume = sum([s["used_volume"] for s in solutionsStats])
    # Let's check if there is any feasible solution.
    feasibleSols = len(filteredSolutions)
    # Opposite to volume occupation.
    costFunction = 1 - averageVolume if feasibleSols else 1

    logMetrics(False)

    if saveStats:
        # Make it json serializable. TODO, not needed now.
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
    """
    Perform the PSO in a given experiment.

    :param expID: experiment identification.
    :param packets: packets of that experiment.
    :param nDst: number of destinations of that experiment.
    :param truck: truck variable.
    :param nParticles: number of particles of the swarm.
    :param nPSOiters: number of iterations of the PSO.
    :param nCores: number of cores used in the multiprocessing.
    :return:
    """
    # ---------- Swarm structure creation ------------------------
    topology = Star()
    # initPositionsList = [0.8, 0.2, 0.55, 0.45, 0.35, 0.25, 0.4, 0.45, 0.45, 0.05, 0.05, 0.3, 0.5, 0.1, 0.1]
    initialPositions = []
    for i in range(15):
        reference1 = np.ones(15) * 1 / 2
        reference2 = np.ones(15) * 1 / 2
        reference1[i] = 0
        reference2[i] = 1
        initialPositions.append(reference1)
        initialPositions.append(reference2)
    initialPositions = np.array(initialPositions)
    # initPositions = np.tile(initPositionsList, (particles, 1))
    bounds = (np.zeros(15), np.ones(15))
    opHandler = OptionsHandler(strategy={"w": "lin_variation"})
    options = {"w": 0.9, "c1": 0.5, "c2": 0.3}

    mySwarm = P.create_swarm(n_particles=nParticles, dimensions=15, options=options, bounds=bounds,
                             init_pos=initialPositions)
    bestCostIter = 0
    history = []
    for p in range(nPSOiters):
        gen_run = client.create_run(expMlflow)
        client.log_param(gen_run.info.run_id, "generation", p)
        client.log_param(gen_run.info.run_id, "expID", expID)
        # Part 1: Update personal best
        logging.info("Best position of each particle before computing iteration")
        logging.info(mySwarm.pbest_pos)
        logging.info("Swarm current position")
        logging.info(mySwarm.position)

        mySwarm.current_cost = objectiveFunction(mySwarm.position, nParticles, expID, packets, nDst, truck, gen_run,
                                                 nCores, bestPositions=mySwarm.pbest_pos, current=True)  # Compute current cost
        logging.info("Current position cost finished")
        mySwarm.pbest_cost = objectiveFunction(mySwarm.pbest_pos, nParticles, expID, packets, nDst, truck, gen_run,
                                               nCores, bestPositions=None, current=False)  # Compute personal best pos
        logging.info("Computed best position for each particle")
        logging.info(mySwarm.pbest_cost)
        # Update pbest_pos based on cost of previous bests and current positions
        mySwarm.pbest_pos, mySwarm.pbest_cost = P.compute_pbest(mySwarm)  # Update and store

        # Part 2: Update global best
        # Note that gbest computation is dependent on your topology
        if np.min(mySwarm.pbest_cost) < mySwarm.best_cost:
            bestCostIter = p
            mySwarm.best_pos, mySwarm.best_cost = topology.compute_gbest(mySwarm)

        client.log_metric(gen_run.info.run_id, "bestCost", mySwarm.best_cost)
        client.log_param(gen_run.info.run_id, "bestParticle", str(mySwarm.best_pos))
        client.log_param(gen_run.info.run_id, "bestCostPart", str(mySwarm.pbest_cost))

        history.append(
            {"generation": p, "position": mySwarm.position, "cost": mySwarm.best_cost, "bestPos": mySwarm.pbest_pos,
             "bestCost": mySwarm.pbest_cost})
        client.set_terminated(gen_run.info.run_id)
        # Part 3: Update position and velocity matrices
        myVh = VelocityHandler(strategy="invert")
        myBh = BoundaryHandler(strategy="nearest")
        # clamp = (np.ones(15) * 0.2, np.ones(15) * 0.6)
        # Note that position and velocity updates are dependent on your topology
        mySwarm.velocity = topology.compute_velocity(mySwarm, vh=myVh, clamp=None, bounds=bounds)
        mySwarm.position = topology.compute_position(mySwarm, bounds=bounds, bh=myBh)
        mySwarm.options = opHandler(options, iternow=p, itermax=nPSOiters)
        logging.info("Iteration " + str(p + 1) + " of the PSO completed")
        logging.info('Iteration: {} | my_swarm.best_cost: {:.4f}'.format(p + 1, mySwarm.best_cost))

    logging.info('The best cost found by our swarm is: {:.4f}'.format(mySwarm.best_cost))
    logging.info('The best position found by our swarm is: {}'.format(mySwarm.best_pos))
    logBestPSOExperiment(expID, mySwarm.best_cost, mySwarm.best_pos, bestCostIter)
    logPSOHistory(expID, history)


# ---------- Experiments ------------------------------------
experiments = getFilepaths()
# IDs = []
# itemsByExp = []
# nDstByExp = []

# ------ Get packets dataset -------
# for j in experiments:
#     ID = getIdFromFilePath(j)
#     IDs.append(ID)
items, ndst = getDataFromJSONWith(experiments[exp])
#     itemsByExp.append(items)
#     nDstByExp.append(ndst)

# # Perform the PSO for each experiment provided the ID, the items and the numbers of destinations.
# for a, b, c in zip(IDs, itemsByExp, nDstByExp):
#     performPSO(a, b, c, truck_var, particles, psoIterations, cores)
performPSO(experiments[exp], items, ndst, truck_var, particles, psoIterations, cores)
