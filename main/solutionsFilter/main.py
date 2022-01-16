"""
This module is in charge of processing the array of solutions reducing it to the best.
"""
import numpy as np
from scipy.spatial import distance
from main.packetOptimization.constructivePhase.mainCP import getSurroundingItems


def filterSolutions(solutions, solutionsStatistics):
    """
    This function filters a set of solutions and its statistics by this constrains:
    - Not horizontal stability in the truck.
    - Left priority items unloaded.
    
    :param solutions: set of solutions in this format [{"solution":'', "iteration":'', "time":''}, ...]
    :param solutionsStatistics: set of statistics.
    :return: one set of filtered solutions and another set with its stats.
    """
    # Keep those that satisfies conditions.
    solutionsStatistics = list(filter(lambda x: x["p_cond"] and x["hs_cond"] and x["sub_cond"], solutionsStatistics))
    feasibleIterations = list(map(lambda x: x["iteration"], solutionsStatistics))
    solutions = list(filter(lambda x: x["iteration"] in feasibleIterations, solutions))
    solutions = addLoadingOrderTo(solutions)
    return solutions, solutionsStatistics


def addLoadingOrderTo(sols):
    for sol in sols:
        # Extract the mass center of all placed items.
        itemsIDs = np.asarray(list(map(lambda x: x["in_id"], sol["placed"])))
        itemsMCs = np.asarray(list(map(lambda x: x["mass_center"], sol["placed"])))
        # Compute and sort the distances between the new item mass center and the rest.
        ndxDistances = distance.cdist(np.array([[0, 0, 0]]), itemsMCs, 'euclidean').argsort()[0]
        # Get the nearest mass centers and its items.
        nearestIds = itemsIDs[ndxDistances].tolist()
        for i in nearestIds:
            item = list(filter(lambda x: x["in_id"] == i, sol["placed"]))[0]
            item["id_or"] = nearestIds.index(i)
    return sols


def getUpdatedStatsWithConditions(solutions, solutionsStatistics):
    """
    This function overwrites stats to denote if the conditions have been satisfied.

    :param solutions: set of solutions in this format [{"solution":'', "iteration":'', "time":''}, ...]
    :param solutionsStatistics: set of statistics.
    :return: set of stats with conditions updated.
    """
    return list(map(lambda x: updateStatsWithConditions(x, solutionsStatistics[x["iteration"]]), solutions))


def updateStatsWithConditions(solution, stats):
    stats["unload_obs"] = determineUnloadingObstacles(solution)
    stats["hs_cond"] = int(isHorizontallyStable(solution["placed"], solution["truck"]["width"]))
    stats["p_cond"] = checkPriorityCondition(solution["discard"])
    stats["sub_cond"] = checkSubgroupingCondition(solution)
    return stats


def determineUnloadingObstacles(solution):
    """
    This function estimates the number of obstacles in the unloading of cargo in a packing solution.

    :param solution: dataset with all the items and their corresponding positions.
    :return: number of unloading obstacles.
    """
    obstacles = 0
    for i in solution["placed"]:
        nearItems = getSurroundingItems(np.array(i["mass_center"]),
                                        [e for e in solution["placed"] if e["id"] != i["id"]], 5)
        if i["dstCode"] > 0:
            # Consider an obstacle if a packet is surrounded by 5 items of different dst code.
            condition = 1 if len(list(filter(lambda x: i["dstCode"] != x["dstCode"], nearItems))) > 4 else 0
            obstacles = obstacles + condition
    return obstacles


def getBest(solutions, solutionsStatistics, nSol):
    """
    This function gets the best solutions by different criteria.
    
    :param nSol: number of solutions.
    :param solutions: set of solutions in this format [{"solution":'', "iteration":'', "time":''}, ...]
    :param solutionsStatistics: set of statistics.
    :return: dictionary with all the criteria and tuples containing best solutions and their stats.
    """
    return {"volume": getBestBy(convertCriteria("volume"), solutions, solutionsStatistics, nSol),
            "weight": getBestBy(convertCriteria("weight"), solutions, solutionsStatistics, nSol),
            "taxability": getBestBy(convertCriteria("taxability"), solutions, solutionsStatistics, nSol)}


# ----------------- Helpers -----------------------------
# TODO, add obstacles.
def convertCriteria(criteria):
    """
    This function gets attribute for the object following a criteria.
    
    :param criteria: Human readable criteria, i.e, taxability.
    :return: string attribute of an object.
    """
    data = ["used_volume", "used_weight",
            "p_total_taxability"]
    return list(filter(lambda x: criteria in x, data))[0]


def getBestBy(criteria, solutions, solutionStatistics, nSol):
    """
    This function gets nSol best solutions by criteria.
    
    :param criteria: String with the criteria.
    :param solutions: list of solutions.
    :param solutionStatistics: list of statistics.
    :param nSol: number of the best solutions.
    :return: tuple of list of nSol solutions and its stats.
    """
    bestStats = sorted(solutionStatistics, key=lambda x: x[criteria], reverse=True)[:nSol]
    nIterFromBestStats = list(map(lambda x: x["iteration"], bestStats))
    bestSolutions = list(map(lambda x: list(filter(lambda y: y["iteration"] == x, solutions))[0], nIterFromBestStats))
    return bestSolutions, bestStats


# ------------ Constrains -------------------------------------
def isHorizontallyStable(solutionPlacedItems, truckWidth):
    """
    This function evaluates horizontal stability constrain.
    
    :param solutionPlacedItems: set of placed items from a solution.
    :param truckWidth: truck's width.
    :return: True if satisfies condition, False otherwise.
    """
    massCenterWithWeight = np.vstack(
        list(map(lambda x:
                 np.append(x["mass_center"], x["weight"]), solutionPlacedItems)))
    containerMC = np.average(massCenterWithWeight[:, :3], axis=0, weights=massCenterWithWeight[:, 3])
    return truckWidth * 0.3 < containerMC[0] < truckWidth * 0.7


def checkSubgroupingCondition(solution):
    """
    This function checks if there are no items unpacked with a certain subgroup that has been partially packed.

    :param solution:
    :return: True if condition satisfied, false otherwise.
    """
    placedSubgroups = list(map(lambda x: x["subgroupId"], solution["placed"]))
    return int(len(list(filter(lambda x: x["subgroupId"] not in placedSubgroups, solution["discard"]))) == 0)


def checkPriorityCondition(solutionDiscarded, priorityLevelThreshold=1):
    """
    This function checks if a certain solution has packed all its priority items.

    :param priorityLevelThreshold: numeric priority item level, from which a solution is not feasible.
    :param solutionDiscarded: set of discarded items from a solution.
    :return: True if condition satisfied, False otherwise.
    """
    return int(len(list(filter(lambda x: x["priority"] >= priorityLevelThreshold, solutionDiscarded))) == 0)
