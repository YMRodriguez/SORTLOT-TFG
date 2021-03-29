from main.packetOptimization.RandomizationAndSorting.randomization import randomization
from main.packetOptimization.RandomizationAndSorting.sorting import sorting


# Main function for the module of sorting and randomizing
def main_m2_1(packets):
    # TODO, packets should come already adapted.
    # adaptPackets(packets, alpha)
    sort_rand_res = sorting(packets)
    new_sol = randomization(sort_rand_res["solution"])
    sort_rand_res["solution"] = new_sol
    return sort_rand_res