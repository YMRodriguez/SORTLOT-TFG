import random
import pymongo
import pandas as pd
import numpy as np
import json
from copy import deepcopy
from main.truckAdapter.adapter import adaptTruck
from main.packetAdapter.adapter import adaptPackets
from main.packetOptimization.randomizationAndSorting.randomization import randomization
from main.packetOptimization.randomizationAndSorting.sorting import sortingPhase
from main.packetOptimization.constructivePhase.mainCP import main_cp
from main.statistics.main import solution_statistics
import time

# ----------------------- MongoDB extraction ----------------------
# Connect to database
myclient = pymongo.MongoClient("mongodb://localhost:27017/",
                               username="mongoadmin",
                               password="admin")
db = myclient['SpainVRP']
wharehouses_col = db['wharehouses']
trucks_col = db['trucks']

# Extract relevant data
truck_var = trucks_col.find_one()
wharehouses_titles = list(map(lambda x: x["name"], wharehouses_col.find({}, {'_id': 0, 'name': 1})[5:12]))
source = wharehouses_titles[0]


# --------------- Packet Generator ------------------------------------------
# In this modification the experiment will have
def random_packet_generator(max_dimensions, max_weight, destinations, source):
    packet = {"subgroup_id": random.choices([0, 1, 2], [90, 5, 5])[0],
              "length": random.randint(30, max_dimensions[0]) / 100,
              "width": random.randint(30, max_dimensions[1]) / 100,
              "height": random.randint(30, max_dimensions[2]) / 100}
    packet["volume"] = round((packet["length"] * packet["width"] * packet["height"]), 3)
    packet["weight"] = random.randint(10000, max_weight) / 1000
    packet["src"] = source
    packet["src_code"] = 10 # Fixed main wharehouse
    packet["dst"] = random.choice(destinations)
    packet["dst_code"] = destinations.index(packet["dst"])
    # We do not care, if it is frozen it will go in a different truck
    packet["frozen"] = random.choices([0, 1], [100, 0])[0]
    packet["priority"] = random.randint(0, 2)
    packet["breakability"] = random.choices([0, 1], [85, 15])[0]
    packet["ADR"] = random.choices([0, 1], [100, 0])[0] # TODO, consider in experiments

    return packet


max_dimensions_var = [160, 160, 160]
max_weight_var = 50000
destinations =  wharehouses_titles[1:]
packets_var = []
for i in range(100):
    packets_var.append(random_packet_generator(max_dimensions_var, max_weight_var, destinations, source))

packets_dataset = pd.DataFrame(packets_var)
packets_dataset["id"] = packets_dataset.apply(lambda x: x.name, axis=1)

packets_to_db = packets_dataset.to_dict(orient='records')


# -------------------- Main Processes -----------------------------
def main_scenario(packets, truck, nDst, rangeOrientations=[1, 2, 3, 4]):
    # ------ Packet adaptation------
    # Alpha is 333 for terrestrial transport
    packets = adaptPackets(packets, 333)
    # ------ Truck adaptation ------
    truck = adaptTruck(truck, 4)
    sort_output = sortingPhase(packets, nDst)
    rand_output = randomization(deepcopy(sort_output["solution"]), rangeOrientations)
    # ------- Solution builder --------
    startTime = time.time()
    iteration = main_cp(truck, rand_output)
    endTime = time.time()
    # It may be relevant to know the sorting method used.
    return {"solution": iteration,
            "sorting_method": sort_output["sort_type"],
            "time": str(endTime-startTime)}


# ------------------ Translation to Application -------------------
def adaptNdarrayToList(item):
    item["mass_center"] = item["mass_center"].tolist()
    item["subzones"] = item["subzones"].tolist()
    item["pp_in"] = item["pp_in"].tolist()
    item["pp_out"] = item["pp_out"].tolist()
    return item


# ------------------ Solution processing --------------------------
solutions = []

solution = main_scenario(deepcopy(packets_to_db), truck_var, len(destinations))
statistics = solution_statistics(solution["solution"])

serializableSolutionPlaced = deepcopy(solution["solution"]["placed"])
serializableSolutionPlaced = list(map(lambda x: adaptNdarrayToList(x), serializableSolutionPlaced))
with open(
        '/Users/yamilmateorodriguez/Developtment/TFG/3DBinPacking-VisualizationTool/web-3dbp-visualization/src/placedpackets.json',
        'w') as file:
    json.dump(serializableSolutionPlaced, file)
