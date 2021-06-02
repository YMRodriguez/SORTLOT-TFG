import json

data = []


def edit(item):
    item["breakability"] = 0
    item["priority"] = 0
    return item


with open("./29-D80-min20-max100-n400-dst4-ADR0-S0-P0-B0.json", "r+") as f:
    data = json.load(f)
    data = list(map(lambda x: edit(x), data))

with open("./29-D80-min20-max100-n400-dst4-ADR0-S0-P0-B0.json", "w+") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
