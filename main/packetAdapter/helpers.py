# This function return the average weight for a list of items.
def getAverageWeight(items):
    return sum(list(map(lambda x: x["weight"], items))) / len(items)


# This function return the average weight for a list of items.
def getAverageVolume(items):
    return sum(list(map(lambda x: x["volume"], items))) / len(items)


# This function return the average priority for a list of items.
def getAveragePriority(items):
    return sum(list(map(lambda x: x["priority"], items))) / len(items)


# This function calculates the average taxability from a group of items
def getAverageTaxability(items):
    return sum(list(map(lambda x: x["taxability"] if "taxability" in x else 0, items))) / len(items)


# This function returns max taxability value in a list of items.
def getMaxTaxability(items):
    return max(item["taxability"] for item in items)


# This function returns max priority value in a list of items.
def getMaxPriority(items):
    return max(item["priority"] for item in items)


# This function returns max volume value in a list of items.
def getMaxVolume(items):
    return max(item["taxability"] for item in items)


# This function returns max weight value in a list of items.
def getMaxWeight(items):
    return max(item["weight"] for item in items)

