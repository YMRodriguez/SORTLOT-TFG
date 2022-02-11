import json
import os
import pathlib


def persistInLocal(bestSolsFiltered, bestStatsFiltered, bestSolsUnfiltered, bestStatsUnfiltered, ID):
    # Pass the data to visualization. This will be made in a flask api not in local.
    # with open(
    #         '/Users/yamilmateorodriguez/Developtment/TFG/3DBinPacking-VisualizationTool/web-3dbp-visualization/src/' + str(ID) + 'bestSolsFiltered.json',
    #         'w') as file:
    #     json.dump(bestSolsFiltered, file, indent=2, ensure_ascii=False)
    #
    # with open(
    #         '/Users/yamilmateorodriguez/Developtment/TFG/3DBinPacking-VisualizationTool/web-3dbp-visualization/src/' + str(ID) + 'bestStatsFiltered.json',
    #         'w') as file:
    #     json.dump(bestStatsFiltered, file, indent=2, ensure_ascii=False)
    #
    # with open(
    #         '/Users/yamilmateorodriguez/Developtment/TFG/3DBinPacking-VisualizationTool/web-3dbp-visualization/src/' + str(ID) + 'bestSolsUnfiltered.json',
    #         'w') as file:
    #     json.dump(bestSolsUnfiltered, file, indent=2, ensure_ascii=False)
    #
    # with open(
    #         '/Users/yamilmateorodriguez/Developtment/TFG/3DBinPacking-VisualizationTool/web-3dbp-visualization/src/' + str(ID) + 'bestStatsUnfiltered.json',
    #         'w') as file:
    #     json.dump(bestStatsUnfiltered, file, indent=2, ensure_ascii=False)
    with open(
            os.path.dirname(__file__) + os.path.sep + 'results' + os.path.sep + 'resultsNew' + os.path.sep + str(
                ID) + 'bestSolsFiltered.json',
            'w+') as file:
        json.dump(bestSolsFiltered, file, indent=2, ensure_ascii=False)

    with open(
            os.path.dirname(__file__) + os.path.sep + 'results' + os.path.sep + 'resultsNew' + os.path.sep + str(
                ID) + 'bestStatsFiltered.json',
            'w+') as file:
        json.dump(bestStatsFiltered, file, indent=2, ensure_ascii=False)

    with open(
            os.path.dirname(__file__) + os.path.sep + 'results' + os.path.sep + 'resultsNew' + os.path.sep + str(
                ID) + 'bestSolsUnfiltered.json',
            'w+') as file:
        json.dump(bestSolsUnfiltered, file, indent=2, ensure_ascii=False)

    with open(
            os.path.dirname(__file__) + os.path.sep + 'results' + os.path.sep + 'resultsNew' + os.path.sep + str(
                ID) + 'bestStatsUnfiltered.json',
            'w+') as file:
        json.dump(bestStatsUnfiltered, file, indent=2, ensure_ascii=False)


def persistStats(stats, ID):
    with open(os.path.dirname(
            __file__) + os.path.sep + 'results' + os.path.sep + 'resultsNew' + os.path.sep + 'simulationNew' + os.path.sep + str(
        ID) + 'simulationStats.json',
              'w+') as file:
        json.dump(stats, file, indent=2, ensure_ascii=False)


def logBestPSOExperiment(expID, bestCost, position, iteration):
    pathlib.Path(os.path.dirname(
        __file__) + os.path.sep + 'results' + os.path.sep + 'resultsNew' + os.path.sep + 'PSOexperiments').mkdir(
        parents=True, exist_ok=True)
    with open(os.path.dirname(
            __file__) + os.path.sep + 'results' + os.path.sep + 'resultsNew' + os.path.sep + 'PSOexperiments' + os.path.sep + str(
        expID) + "BestPSO.json",
              'w+') as file:
        json.dump(
            {"expID": expID, "bestCost": int(bestCost), "bestPosition": position.tolist(), "iteration": iteration},
            file, indent=2, ensure_ascii=False)


def logPSOHistory(expID, history):
    with open(os.path.dirname(
            __file__) + os.path.sep + 'results' + os.path.sep + 'resultsNew' + os.path.sep + 'PSOexperiments' + os.path.sep + str(
        expID) + "BestPSO.json",
              'w+') as file:
        json.dump(history, file, indent=2, ensure_ascii=False)
