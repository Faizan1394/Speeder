from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

latlngs = [
    [43.90302, -78.94934],
    [43.90391, -78.94969],
    [43.90414, -78.94881],
    [43.9044356, -78.9475582],
    [43.9057112, -78.9426978],
    [43.9059246, -78.9421041],
    [43.906386, -78.9410528],
    [43.9080293, -78.9398131],
    [43.9093174, -78.9388471],
    [43.91161, -78.93448],
    [43.9152308, -78.9360707],
    [43.91612, -78.93375],
    [43.91722, -78.93224],
    [43.91775, -78.92969],
    [43.91894, -78.92914],
    [43.9194318, -78.9271041],
    [43.9206807, -78.9276331],
    [43.9215542, -78.927781],
    [43.92189, -78.92749],
    [43.92214, -78.92655],
    [43.9225035, -78.925025],
    [43.9226064, -78.9244246],
    [43.923342, -78.9212616],
    [43.9239676, -78.9183999],
    [43.9240111, -78.9182057],
    [43.9240328, -78.9181111],
    [43.9245833, -78.9156999],
    [43.9247986, -78.9149332],
    [43.924958, -78.9141492],
    [43.926162, -78.9089493],
    [43.9262651, -78.9083327],
    [43.9262839, -78.9082408],
    [43.9263722, -78.9082515],
    [43.9267508, -78.9083716],
    [43.9430467, -78.9155326],
    [43.9436155, -78.9154965],
    [43.9439194, -78.914629],
    [43.9454576, -78.9076059],
    [43.9457458, -78.9059392],
    [43.9471678, -78.8995985],
    [43.94626, -78.8992],
    [43.94618, -78.89803],
    [43.94607, -78.89592],
    [43.9437411, -78.8949944]
]


@app.route('/')
def index():
    """ Displays the index page accessible at '/'
    """
    return render_template('MapGUI.html')


def get_coordinates(locations, drivers):
    """
    This function should return dictionary as shown below.
    :param locations: list of addresses
    :param drivers: number of drivers
    :return:
    """

    output = {
        "locations": [
            {
                "startingPointName": "Vanier Street",
                "endingPointName": "Durham College",
                "coordinates": latlngs,
                "summary": "Just see the map dude! hahaha! Just Kidding." * 100,
            }
        ]
    }

    return output


@app.route('/getdata', methods=['POST'])
def display_details():
    data = request.get_json()
    print(data)
    output = get_coordinates(data['locations'], data['drivers'])
    return jsonify(output)


if __name__ == '__main__':
    app.run(port=8080, debug=True)
