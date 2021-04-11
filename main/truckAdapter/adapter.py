import numpy as np
from main.packetOptimization.constructivePhase.geometryHelpers import getTruckBLF
from main.packetOptimization.constructivePhase.geometryHelpers import getTruckBRF


# This function adapts truck container surface to longitudinal zone separation. Creates the subzones in the truck object.
# [Xin, Zin, Xend, Zend] which is the diagonal of a square
def setContainerSubzones(truck, nZones):
    truck["subzones"] = []
    for i in range(nZones):
        subzone = {"id": i + 1, "blf": np.array([0, 0, i * truck["length"] / nZones], dtype=float),
                   "brr": np.array([truck["width"], 0, (i + 1) * truck["length"] / nZones], dtype=float), "weight": 0,
                   # TODO, cannot be hardcoded, this will depend on the opetator introducing packets.
                   "weight_limit": truck["tonnage"] / nZones}
        truck["subzones"].append(subzone)
    return truck


def setContainerPP(truck):
    truck["pp"] = np.array((getTruckBLF(truck), getTruckBRF(truck)))
    return truck


def adaptTruck(truck, nZones):
    return setContainerPP(setContainerSubzones(truck, nZones))
