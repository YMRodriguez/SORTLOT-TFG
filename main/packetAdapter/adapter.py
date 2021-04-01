# ------------------ Taxability --------------------------------------------
# This function takes the taxability from a given item
def getTaxability(item, alpha):
    tax = max(item["weight"], alpha * item["volume"])
    return tax


# This function takes the taxability from a given item
def setTaxability(item, alpha):
    item["taxability"] = getTaxability(item, alpha)
    return item


# This function sets taxability for each item in a group of packets
def addTaxToDataset(packets, alpha):
    return list(map(lambda x: setTaxability(x, alpha), packets))


# This function calculates the average taxability from a group of items
def getAverageTaxability(packets):
    average = sum(list(map(lambda x: x["taxability"] if "taxability" in x else 0, packets))) / len(packets)
    return average


# This function returns if a group of packets are taxed or not
def areTaxed(packets):
    return all(list(map(lambda x: "taxability" in x, packets)))


# -------------------- Adapter ----------------------------------------
# This function adapts packets to be taxed.
def adaptPackets(packets, alpha):
    if not areTaxed(packets):
        return addTaxToDataset(packets, alpha)
    else:
        print("Packets are already taxed")