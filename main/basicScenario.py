import random
import pymongo
import pandas as pd
import numpy as np
import json
from copy import deepcopy
from main.truckAdapter.adapter import adaptTruck
from main.packetAdapter.adapter import adaptPackets
from main.packetOptimization.randomizationAndSorting.randomization import randomization
from main.packetOptimization.randomizationAndSorting.sorting import sorting
from main.packetOptimization.constructivePhase.mainCP import main_m2_2
from main.statistics.main import main_statistics
from main.packetOptimization.constructivePhase.mainCP import isNotOverlapping

# ----------------------- MongoDB extraction ----------------------
myclient = pymongo.MongoClient("mongodb://localhost:27017/",
                               username="mongoadmin",
                               password="admin")

# Creamos la base de datos
db = myclient['SpainVRP']

# Creamos las colecciones dentro de la base de datos
wharehouses_col = db['wharehouses']
trucks_col = db['trucks']
packets_col = db['packets']

# Extract relevant data
truck_var = trucks_col.find_one()
wharehouses_titles = list(map(lambda x: x["name"], wharehouses_col.find({}, {'_id': 0, 'name': 1})))


# --------------- Packet Generator ------------------------------------------

def random_packet_generator(max_dimensions, max_weight, places):
    packet = {"subgroup_id": random.choices([0, 1, 2], [90, 5, 5])[0],
              "length": random.randint(30, max_dimensions[0]) / 100,
              "width": random.randint(30, max_dimensions[1]) / 100,
              "height": random.randint(30, max_dimensions[2]) / 100}
    packet["volume"] = round((packet["length"] * packet["width"] * packet["height"]), 3)
    packet["weight"] = random.randint(10000, max_weight) / 1000
    packet["src"] = places[5]
    packet["src_code"] = 5  # Fixed main wharehouse
    packet["dst"] = random.choice([p for p in places if p != packet["src"]])
    packet["dst_code"] = wharehouses_titles.index(packet["dst"])
    packet["frozen"] = random.choices([0, 1], [100, 0])[0]  # TODO, change this to 85,15
    packet["priority"] = random.randint(1, 10)
    packet["breakability"] = random.choices([0, 1], [85, 15])[0]
    packet["ADR"] = random.choices([0, 1], [85, 15])[0] if packet["frozen"] == 0 else 0

    return packet


max_dimensions_var = [160, 160, 160]
max_weight_var = 50000

packets_var = []
for i in range(100):
    packets_var.append(random_packet_generator(max_dimensions_var, max_weight_var, wharehouses_titles))

packets_dataset = pd.DataFrame(packets_var)
packets_dataset["id"] = packets_dataset.apply(lambda x: x.name, axis=1)

packets_to_db = packets_dataset.to_dict(orient='records')


# -------------------- Main Processes -----------------------------
def main(packets, truck):
    # ------ Packet adaptation------
    packets = adaptPackets(packets, 0.6)
    # ------ Truck adaptation ------
    truck = adaptTruck(truck, 4)
    sort_output = sorting(packets)
    rand_output = randomization(deepcopy(sort_output["solution"]), list(range(1, 7)))
    # ------- Solution builder --------
    return main_m2_2(truck, rand_output)


# ------------------ Translation to Application -------------------
def adaptNdarrayToList(item):
    item["mass_center"] = item["mass_center"].tolist()
    item["subzones"] = item["subzones"].tolist()
    item["pp_in"] = item["pp_in"].tolist()
    item["pp_out"] = item["pp_out"].tolist()
    return item


# ------------------ Solution processing --------------------------
solution = main(deepcopy(packets_to_db), truck_var)
serializableSolutionPlaced = deepcopy(solution["placed"])
serializableSolutionPlaced = list(map(lambda x: adaptNdarrayToList(x), serializableSolutionPlaced))
pandasDataframe = main_statistics(solution)
with open('/Users/yamilmateorodriguez/Developtment/TFG/3DBinPacking-VisualizationTool/web-3dbp-visualization/src/placedpackets.json', 'w') as file:
    json.dump(serializableSolutionPlaced, file)
