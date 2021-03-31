from main.packetOptimization.randomizationAndSorting.randomization import randomization
from main.packetOptimization.randomizationAndSorting.sorting import sorting


# Main function for the module of sorting and randomizing
def main_m2_1(packets, validOrientations):
    # TODO, packets should come already adapted.
    sort_rand_res = sorting(packets)
    new_sol = randomization(sort_rand_res["solution"], validOrientations)
    sort_rand_res["solution"] = new_sol
    return sort_rand_res
