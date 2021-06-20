import json

data = []


def edit(item):
    item["breakability"] = 0
    item["priority"] = 0
    return item


with open("./0-D10-min35-max120-n200-dst1-ADR0-S0-P0-B0.json", "r+") as f:
    data = json.load(f)
    data = list(map(lambda x: edit(x), data))

with open("./0-D10-min35-max120-n200-dst1-ADR0-S0-P0-B0.json", "w+") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
