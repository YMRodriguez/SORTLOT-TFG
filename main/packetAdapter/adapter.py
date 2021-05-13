# ------------------ Taxability --------------------------------------------
# This function takes the taxability from a given item
def getTaxability(item, alpha):
    return max(item["weight"], alpha * item["volume"])


# This function takes the taxability from a given item
def setTaxability(item, alpha):
    item["taxability"] = getTaxability(item, alpha)
    return item


# This function sets taxability for each item in a group of items
def addTaxToDataset(items, alpha):
    return list(map(lambda x: setTaxability(x, alpha), items))


# This function returns if a group of items are taxed or not
def areTaxed(items):
    return all(list(map(lambda x: "taxability" in x, items)))


# -------------------- Adapter ----------------------------------------
# This function adapts items to be taxed.
def adaptPackets(items, alpha):
    if not areTaxed(items):
        return addTaxToDataset(items, alpha)
    else:
        print("Items are already taxed")


def cleanDestinationAndSource(items):
    """
    This function return set of items without destination and source strings.
    :param items: set of packets.
    :return: cleaned packets.
    """
    for i in items:
        del i["dst"]
        del i["src"]
    return items
