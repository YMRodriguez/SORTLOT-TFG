import random
import pymongo
import json
import pandas as pd

# ----------------------- General variables -----------------------
ID = 7
difDim = 30
noPackets = 200
maxDim = [100, 100, 100]
minD = 30
nDestinations = 5
ADRc = 0
subgrouping = 0

# ----------------------- MongoDB extraction ----------------------
# Connect to database
myclient = pymongo.MongoClient("mongodb://localhost:27017/",
                               username="mongoadmin",
                               password="admin")
db = myclient['SpainVRP']
warehouses_col = db['wharehouses']
trucks_col = db['trucks']

# Extract relevant data
truck_var = trucks_col.find_one()
warehouses_titles = list(
    map(lambda x: x["name"], warehouses_col.find({}, {'_id': 0, 'name': 1})[5:(6 + nDestinations)]))

# Adapt data to input in generator
src = warehouses_titles[0]
dests = warehouses_titles[1:]


# --------------- Packet Generator ------------------------------------------
def randomPacketGenerator(dimensions, destinations, source, ADR):
    """
    This function generates a item with specified conditions.
    :param dimensions: list dimensions [Width, Height, Length]
    :param destinations: list of destinations names.
    :param source: name of the source.
    :param ADR: True if dangerous, False otherwise.
    :return: object representing a packet.
    """
    packet = {"length": dimensions[0],
              "width": dimensions[1],
              "height": dimensions[2],
              "volume": round(dimensions[0] * dimensions[1] * dimensions[2], 3),
              "weight": dimensions[3],
              "src": source,
              "src_code": 10,
              "dst": random.choice(destinations)}
    packet["dst_code"] = destinations.index(packet["dst"])
    # We do not care, if it is frozen it will go in a different truck
    packet["frozen"] = random.choices([0, 1], [100, 0])[0]
    packet["priority"] = random.choices([1, 2], [85, 15])[0]
    packet["breakability"] = random.choices([0, 1], [95, 5])[0]
    packet["ADR"] = random.choices([0, 1], [95, 5])[0] if ADR else random.choices([0, 1], [100, 0])[0]
    return packet


def addSubgroups(items):
    """
    This function generate logic aggregations by subgroup.
    :param items: set of items.
    :return: list of items with subgroups.
    """
    for i in items:
        if i["dst_code"] == 0:
            i["subgroup_id"] = random.choices([0, 1], [95, 5])[0]
    return items


def addIDs(items):
    """
    This function adds each id to a set of items.
    :param: items: set of items.
    :return: items with id.
    """
    itemsDF = pd.DataFrame(items)
    itemsDF["id"] = itemsDF.apply(lambda x: x.name, axis=1)
    return itemsDF.to_dict(orient="records")


def generatePacketsDataset(difDimensions, nPackets, minDim, maxDimensions, destinations, source, ADR, subgroups):
    """
    This function generates a dataset of packets.
    :param difDimensions: distinct dimensions.
    :param nPackets: number of packets to be generated.
    :param minDim: minimum W/H/L value in centimetres.
    :param maxDimensions: maximum [W, H, L] in centimetres.
    :param destinations: list of destinations names.
    :param source: name of the source
    :param ADR: True if dangerous in set, False otherwise.
    :param subgroups: True if subgroups in set, False otherwise.
    :return: set of items.
    """
    packets = []
    dimensions = []
    for i in range(difDimensions):
        dimensions.append([random.randint(minDim, maxDimensions[0]) / 100,
                           random.randint(minDim, maxDimensions[1]) / 100,
                           random.randint(minDim, maxDimensions[2]) / 100])
        # Tries to generate more realistic items in terms of volume/weight relations.
        dimensions[i].append(round(random.uniform(25, 50) * (dimensions[i][0] * dimensions[i][1] * dimensions[i][2]), 3))
    for i in range(nPackets):
        packets.append(randomPacketGenerator(random.choice(dimensions), destinations, source, ADR))
    if subgroups:
        packets = addSubgroups(packets)
    return addIDs(packets)


# ------------------------ Generation and saving ----------------------------------------
packets_dataset = generatePacketsDataset(difDim, noPackets, minD, maxDim, dests, src, ADRc, subgrouping)

# File name normalization
filename = str(ID) +"-D" + str(difDim) + "-" + str(minD) + "mx" +\
           str(maxDim[0]) + "x" + str(maxDim[1]) + "x" + \
           str(maxDim[2]) + "-n" + str(noPackets) + "-dst" + str(nDestinations) + \
            "-ADR" + str(ADRc) + "-S" + str(subgrouping)

with open("./packetsDatasets/" + filename + ".json", "x") as f:
    json.dump(packets_dataset, f, indent=2, ensure_ascii=False)
