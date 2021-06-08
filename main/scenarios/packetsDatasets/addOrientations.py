import glob
import os
import json
import random


def getDatasetFromJSONWith(ID):
    """
    This function gets a dataset file by its id.

    :param ID: the id of the dataset, not the name.
    :return: list of items from the specified file.
    """
    filepath = glob.glob(os.path.dirname(__file__) + "/../../scenarios/packetsDatasets/" + str(ID) + "-*.json")[0]
    return json.load(open(filepath)), filepath


def updateStatistics(ID):
    data, filepath = getDatasetFromJSONWith(ID)
    for i in range(len(data)):
        if random.getrandbits(1):
            randomOrientation = random.sample([3, 4, 5, 6], k=1)
            # Get next or previous depending on the scheme of rotations.
            randomOrientationRotated = [randomOrientation[0] + 1] if randomOrientation[0] % 2 else [
                randomOrientation[0] - 1]
            feasibleOrientations = [1, 2] + randomOrientation + randomOrientationRotated
            data[i]["f_orient"] = feasibleOrientations
        else:
            data[i]["f_orient"] = [1, 2, 3, 4, 5, 6]
    with open(filepath, 'w+') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

for i in range(30):
    updateStatistics(i)