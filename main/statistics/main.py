import pandas as pd


def solutionStatistics(solution):
    """
    This function returns main statistics for a solution.

    :param solution: solution object.
    :return: Object of stats.
    """
    placed = pd.DataFrame(solution["placed"])
    discard = pd.DataFrame(solution["discard"]) if len(solution["discard"]) else placed.iloc[0:1].apply(lambda x: 0, axis=0)
    return {"iteration": solution["iteration"], "time": solution["time"],
            "n_placed": len(solution["placed"]), "n_discard": len(solution["discard"]),
            "p_mean_weight": float(placed.weight.mean()), "d_mean_weight": float(discard.weight.mean()),
            "p_median_weight": float(placed.weight.median()), "d_median_weight": float(discard.weight.median()),
            "p_std_weight": float(placed.weight.std()), "d_std_weight": float(discard.weight.std()),
            "p_total_weight": float(placed.weight.sum()), "d_total_weight": float(discard.weight.sum()),
            "p_mean_taxability": float(placed.taxability.mean()), "d_mean_taxability": float(discard.taxability.mean()),
            "p_total_taxability": float(placed.taxability.sum()), "d_total_taxability": float(discard.taxability.sum()),
            "p_mean_volume": float(placed.volume.mean()), "d_mean_volume": float(discard.volume.mean()),
            "p_median_volume": float(placed.volume.median()), "d_median_volume": float(discard.volume.median()),
            "p_std_volume": float(placed.volume.std()), "d_std_volume": float(discard.volume.std()),
            "p_total_volume": float(placed.volume.sum()), "d_total_volume": float(discard.volume.sum()),
            "d_max_priority": int(discard.priority.max()),
            "used_volume": float(placed.volume.sum() / solution["truck"]["volume"]),
            "used_weight": float(placed.weight.sum() / solution["truck"]["tonnage"])
            }