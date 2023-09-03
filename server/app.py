import sys
sys.path.insert(0, '/Users/yamilmateorodriguez/Development/TFG/SORTLOT-TFG')
print(sys.path)

from flask import Flask, request, jsonify
from main.scenarios.BE_scenario import run_optimizer
from flask_cors import CORS


app = Flask(__name__)
cors = CORS(app, origins="*", allow_headers="*")

@app.route('/run-optimizer', methods=['POST', 'OPTIONS'])
def handle_post_request():
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    try:
        # Extract data from the POST request
        data = request.json
        packets = data.get('packets', [])
        destinations = len(set(map(lambda x: x['dstCode'], packets)))
        truck = data.get('truck', None)
        print(truck)
    except:
        return {"error": "Invalid data format"}

    result = run_optimizer(container=truck, items=packets, destinations=destinations)
    response = jsonify(result)
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    return response


if __name__ == '__main__':
    app.run(debug=True)