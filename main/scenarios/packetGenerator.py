import random
import pymongo
import json
import pandas as pd

# ----------------------- General variables -----------------------
ID = 2
difDim = 25
noPackets = 80
maxDim = [100, 100, 100]
minD = 30
nDestinations = 6
ADRc = 0
subgrouping = 0
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
wharehouses_titles = list(
    map(lambda x: x["name"], wharehouses_col.find({}, {'_id': 0, 'name': 1})[5:(6 + nDestinations)]))
# Adapt data to input in generator
src = wharehouses_titles[0]
dests = wharehouses_titles[1:]


# --------------- Packet Generator ------------------------------------------
def randomPacketGenerator(dimensions, destinations, source, ADR, subgroups):
    """Generates a item with specified conditions."""
    packet = {"subgroup_id": random.choices([0, 1, 2], [90, 5, 5])[0] if subgroups else 0,
              "length": dimensions[0],
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
    packet["priority"] = random.choices([0, 1, 2], [70, 20, 10])[0]
    packet["breakability"] = random.choices([0, 1], [85, 15])[0]
    packet["ADR"] = random.choices([0, 1], [95, 5])[0] if ADR else random.choices([0, 1], [100, 0])[0]
    return packet


def addSubgroups(items):
    """This function generate logic aggregations by subgroup."""
    for i in items:
        if i["dst_code"] == 0:
            i["subgroup_id"] = random.choices([0, 1], [95, 5])[0]
    return items


def addIDs(items):
    """This function adds each id to a set of items."""
    itemsDF = pd.DataFrame(items)
    itemsDF["id"] = itemsDF.apply(lambda x: x.name, axis=1)
    return itemsDF.to_dict(orient="records")


def generatePacketsDataset(difDimensions, nPackets, minDim, maxDimensions, destinations, source, ADR, subgroups):
    """This function generates a dataset of packets."""
    packets = []
    dimensions = []
    for i in range(difDimensions):
        dimensions.append([random.randint(minDim, maxDimensions[0]) / 100,
                           random.randint(minDim, maxDimensions[1]) / 100,
                           random.randint(minDim, maxDimensions[2]) / 100])
        # With this we generate most realistic items.
        dimensions[i].append(round(random.uniform(25, 50) * (dimensions[i][0] * dimensions[i][1] * dimensions[i][2]), 3))
    for i in range(nPackets):
        packets.append(randomPacketGenerator(random.choice(dimensions), destinations, source, ADR, subgroups))
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
