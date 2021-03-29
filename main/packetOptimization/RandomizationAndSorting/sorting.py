import random


# -------------- Types -----------------------------------------
# This function will sort by decreasing taxability
def taxSorting(packets):
    return {"sort_type": "tax", "solution": sorted(packets, key=lambda x: x["taxability"], reverse=True)}


# This function will sort by decreasing priority level
def prioritySorting(packets):
    return {"sort_type": "prior", "solution": sorted(packets, key=lambda x: x["priority"], reverse=True)}


# This function will sort by decreasing customer code
# TODO, no confundir dst_code con el costumer_code para una ruta dada
def customerSorting(packets):
    return {"sort_type": "cust", "solution": sorted(packets, key=lambda x: x["dst_code"], reverse=True)}


# ----------- Main function ----------------------------------
# This function is in charge of sorting the packets choosing the sorting method randomly.
def sorting(packets):
    sorting_methods = [taxSorting, prioritySorting, customerSorting]
    return random.choice(sorting_methods)(packets)