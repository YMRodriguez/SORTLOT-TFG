import json


def persistInLocal(bestSolsFiltered, bestStatsFiltered, bestSolsUnfiltered, bestStatsUnfiltered, ID):
    # Pass the data to visualization. This will be made in a flask api not in local.
    with open(
            '/Users/yamilmateorodriguez/Developtment/TFG/3DBinPacking-VisualizationTool/web-3dbp-visualization/src/' + str(ID) + 'bestSolsFiltered.json',
            'w') as file:
        json.dump(bestSolsFiltered, file, indent=2, ensure_ascii=False)

    with open(
            '/Users/yamilmateorodriguez/Developtment/TFG/3DBinPacking-VisualizationTool/web-3dbp-visualization/src/' + str(ID) + 'bestStatsFiltered.json',
            'w') as file:
        json.dump(bestStatsFiltered, file, indent=2, ensure_ascii=False)

    with open(
            '/Users/yamilmateorodriguez/Developtment/TFG/3DBinPacking-VisualizationTool/web-3dbp-visualization/src/' + str(ID) + 'bestSolsUnfiltered.json',
            'w') as file:
        json.dump(bestSolsUnfiltered, file, indent=2, ensure_ascii=False)

    with open(
            '/Users/yamilmateorodriguez/Developtment/TFG/3DBinPacking-VisualizationTool/web-3dbp-visualization/src/' + str(ID) + 'bestStatsUnfiltered.json',
            'w') as file:
        json.dump(bestStatsUnfiltered, file, indent=2, ensure_ascii=False)
    with open(
            '/Users/yamilmateorodriguez/Developtment/TFG/SORTLOT-TFG/main/scenarios/results/' + str(ID) + 'bestSolsFiltered.json',
            'w') as file:
        json.dump(bestSolsFiltered, file, indent=2, ensure_ascii=False)

    with open(
            '/Users/yamilmateorodriguez/Developtment/TFG/SORTLOT-TFG/main/scenarios/results/' + str(ID) + 'bestStatsFiltered.json',
            'w') as file:
        json.dump(bestStatsFiltered, file, indent=2, ensure_ascii=False)

    with open(
            '/Users/yamilmateorodriguez/Developtment/TFG/SORTLOT-TFG/main/scenarios/results/' + str(ID) + 'bestSolsUnfiltered.json',
            'w') as file:
        json.dump(bestSolsUnfiltered, file, indent=2, ensure_ascii=False)

    with open(
            '/Users/yamilmateorodriguez/Developtment/TFG/SORTLOT-TFG/main/scenarios/results/' + str(ID) + 'bestStatsUnfiltered.json',
            'w') as file:
        json.dump(bestStatsUnfiltered, file, indent=2, ensure_ascii=False)