import pandas as pd


# TODO, in this module will also have the statistics of the container.
# This function will return the main statistics for a solution.
def main_statistics(solution):
    placed = pd.DataFrame(solution["placed"])
    discard = pd.DataFrame(solution["discard"])
    return {"p_mean_weight": placed.weight.mean(), "d_mean_weight": discard.weight.mean(),
            "p_mean_taxability": placed.weight.mean(), "d_mean_taxability": discard.weight.mean()}
