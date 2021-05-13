import pandas as pd


# TODO, may want to include priority by customer.
def solutionStatistics(solution):
    """
    This function returns main statistics for a solution.
    :param solution: solution object.
    :return: Object of stats.
    """
    placed = pd.DataFrame(solution["placed"])
    discard = pd.DataFrame(solution["discard"]) if len(solution["discard"]) else placed.iloc[0:1].apply(lambda x: 0, axis=0)
    return {"iteration": solution["iteration"], "time": solution["time"],
            "p_mean_weight": float(placed.weight.mean()), "d_mean_weight": float(discard.weight.mean()),
            "p_total_weight": float(placed.weight.sum()), "d_total_weight": float(discard.weight.sum()),
            "p_mean_taxability": float(placed.weight.mean()), "d_mean_taxability": float(discard.weight.mean()),
            "p_total_taxability": float(placed.taxability.sum()), "d_total_taxability": float(discard.taxability.sum()),
            "p_mean_volume": float(placed.volume.mean()), "d_mean_volume": float(discard.volume.mean()),
            "p_cumulative_priority": int(placed.priority.sum()), "p_mean_priority": int(placed.priority.mean()),
            "d_max_priority": int(discard.priority.max()),
            "used_volume": float(placed.volume.sum() / solution["truck"]["volume"]),
            "used_weight": float(placed.weight.sum() / solution["truck"]["tonnage"])
            }


def scenarioStatistics(solutionsStatistics):
    """
    This function computes a set of unfiltered solutions statistics and return some
    insights on them.
    :param solutionsStatistics:
    :return: Object with statistics.
    """
    return
