import pandas as pd


# TODO, in this module will also have the statistics of the container.


# This function will return the main statistics for a solution.
# TODO, we may want to include priority by customer.
def solution_statistics(solution):
    placed = pd.DataFrame(solution["placed"])
    discard = pd.DataFrame(solution["discard"])
    return {"p_mean_weight": placed.weight.mean(), "d_mean_weight": discard.weight.mean(),
            "p_mean_taxability": placed.weight.mean(), "d_mean_taxability": discard.weight.mean(),
            "p_mean_volume": placed.volume.mean(), "d_mean_volume": discard.volume.mean(),
            "p_cumulative_priority:": placed.priority.sum(), "p_mean_priority": placed.priority.mean(),
            "d_max_priority": discard.priority.max(),
            "used_volume": placed.volume.sum()/solution.truck["volume"],
            "used_volume_s1": "" ,
            "used_volume_s2": "",
            "used_volume_s3": "",
            "used_volume_s4": "",
            "used_weight": placed.weight.sum()/solution.truck["tonnage"],
            "used_weight_s1": "",
            "used_weight_s2": "",
            "used_weight_s3": "",
            "used_weight_s4": "",
    }


# This function will return the statistics from a scenario.
# Evaluates the context:
# - Relevant statistics of the population of items: heterogeneity, volume, ...
# - Relevant statistics of the set of solutions.
def scenario_statistics():
    return