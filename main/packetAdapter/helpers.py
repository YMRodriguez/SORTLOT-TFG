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
