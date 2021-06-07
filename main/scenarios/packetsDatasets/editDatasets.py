import json

data = []


def edit(item):
    item["breakability"] = 0
    return item


with open("./2-D15-min35-max100-n275-dst3-ADR0-S0-P1-B0.json", "r+") as f:
    data = json.load(f)
    data = list(map(lambda x: edit(x), data))

with open("./2-D15-min35-max100-n275-dst3-ADR0-S0-P1-B0.json", "w+") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
