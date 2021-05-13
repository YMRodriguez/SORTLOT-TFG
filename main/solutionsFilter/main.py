"""
This module is in charge of processing the array of solutions reducing it to the best.
"""
import numpy as np


def filterSolutions(solutions, solutionsStatistics):
    """
    This function filters a set of solutions and its statistics by this constrains:
    - Not horizontal stability in the truck.
    - Left priority items unloaded.
    
    :param solutions: set of solutions in this format [{"solution":'', "iteration":'', "time":''}, ...]
    :param solutionsStatistics: set of statistics.
    :return: two set of filtered conditions.
    """
    # Keep those that satisfies horizontal stability.
    solutions = list(filter(lambda x: isHorizontallyStable(x["placed"], x["truck"]["width"]), solutions))
    iterations = list(map(lambda x: x["iteration"], solutions))
    solutionsStatistics = list(filter(lambda x: x["iteration"] in iterations, solutionsStatistics))
    # Filter those which has not been able to place all priority items.
    maxPriority = max(solutions[0]["placed"] + solutions[0]["discard"],
                      key=lambda x: x["priority"])["priority"]
    solStatsWithPrio = list(filter(lambda x: x["d_max_priority"] != maxPriority, solutionsStatistics))
    iterWithPrio = list(map(lambda x: x["iteration"], solStatsWithPrio))
    sols = list(filter(lambda x: x["iteration"] in iterWithPrio, solutions))
    return sols, solStatsWithPrio


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
            "priority": getBestBy(convertCriteria("priority"), solutions, solutionsStatistics, nSol),
            "taxability": getBestBy(convertCriteria("taxability"), solutions, solutionsStatistics, nSol)}


# ----------------- Helpers -----------------------------
# TODO, add obstacles.
def convertCriteria(criteria):
    """
    This function gets attribute for the object following a criteria.
    
    :param criteria: Human readable criteria, i.e, taxability.
    :return: string attribute of an object.
    """
    data = ["used_volume", "used_weight", "p_total_taxability",
            "p_cumulative_priority"]
    return list(filter(lambda x: criteria in x, data))[0]


def getBestBy(criteria, solutions, solutionStatistics, nSol):
    """
    This function gets nSol best solutions by criteria.
    
    :param criteria: String with the criteria.
    :param solutions: list of solutions.
    :param solutionStatistics: list of statistics.
    :param nSol: number of best solutions.
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
