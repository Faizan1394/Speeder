from flask import Flask, request, jsonify, render_template
import optimalPath

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


# Build the graph - this is Whitby/Oshawa for testing purposes - east, west, south, north
G = optimalPath.build_graph(43.984503, 43.862879, -78.954552, -78.821660)


def get_coordinates(locations, drivers, streetsToAvoid, option):
    """
    This function should return dictionary as shown below.
    :param locations: list of addresses
    :param drivers: number of drivers
    :return:
    """

    # get the starting location and convert it to coordinates
    start = optimalPath.address_to_coord(locations[0])

    # Get the coordinates for each destination
    dest_coords = []

    for i in range(1, len(locations)):
        dest_coords.append(optimalPath.address_to_coord(locations[i]))

    # Store the destination addresses and corresponding graph nodes
    dest_dict = optimalPath.dest_address_and_node(G, locations[1:])

    # Cluster the destinations according to the number of drivers
    clusters = optimalPath.cluster_destinations(dest_coords, int(drivers))

    # Convert locations into nodes
    start_node = optimalPath.coords_to_node(G, start)

    # Get destination nodes
    destination_nodes = []
    for i in range(len(clusters)):
        inodes = []
        for x in clusters[i]:
            inodes.append(optimalPath.coords_to_node(G, x))
        destination_nodes.append(inodes)

    dicts = []
    # For each driver, get their route
    for driver in range(len(clusters)):
        coordinates = []

        # Display the driver number
        # print('\n\nDriver', driver+1, 'Route:')
        # Store their destination nodes
        your_dests = destination_nodes[driver]

        # Create empty list of their visited destinations and their overall route
        visited = []
        route = []

        # Use the a* multi algorithm to build these lists
        optimalPath.aStarMulti(start_node, your_dests, G, 'travel_time', visited, route)

        # Convert the list of lists into a single list
        route_list = []
        route_list.append(route[0][0])
        for i in route:
            for j in i:
                if route_list[-1] != j:
                    route_list.append(j)

        # Check if there is a route
        if len(route_list) == 1:
            print('There is no possible route with these specification.')
            print('Please start over.')
            break

        # Get the full route information
        full_route_df = optimalPath.full_route_info(G, route_list, visited)
        # Add in the turns
        route_df = optimalPath.add_turns(full_route_df, G)

        # Get the breakpoints in this driver's route
        break_points = optimalPath.get_break_points(route_df)
        # Split their route into segments
        segments = []
        optimalPath.get_seg(0, segments, break_points, route_df)
        # Simplify the route
        simplified_route = optimalPath.get_simple_route(route_df, segments)

        # Print the driver's route
        summary, visitOrder = optimalPath.print_route_summary(simplified_route, dest_dict, G)
        summary = summary.replace("\n", "<br>")
        summary = summary.replace("TurnLEFT", "Turn LEFT")
        summary = summary.replace("TurnRIGHT", "Turn RIGHT")

        # get coordinates for full path from start to finish
        for node in route_df['Start Node']:
            nCord = optimalPath.node_to_coords(G, node)
            coordinates.append([nCord[0], nCord[1]])

        # print(summary)
        # print(visitOrder)

        # dst =[]

        # for i in visited:
        #   dst.append(int(i))

        print(route_df['Street Name'])

        info = {
            "startingPointName": route_df['Street Name'][0],
            "endingPointName": list(visitOrder[-1].keys())[0],
            "destinations": visitOrder[:-1],
            "coordinates": coordinates,
            "summary": summary,
        }

        dicts.append(info)

    # for i in range (len(dicts)):
    #   print(i)
    #  print(dicts[i])
    # print("\n\n\n\n")

    output = {
        "locations": dicts
    }

    return output


@app.route('/getdata', methods=['POST'])
def display_details():
    data = request.get_json()
    print(data)
    output = get_coordinates(data['locations'], data['drivers'], data['streetsToAvoid'],data['option'])
    return jsonify(output)


@app.route("/driver")
def driver():
    return render_template("Driver.html")


@app.route('/driver_details', methods=['POST'])
def show_driver_detail():
    """
    This method should return route detail for specific driver.
    Example can be seen below.
    :return:
    """
    locations = {
        "locations": [
            {
                "startingPointName": 'Vanier Street',
                "endingPointName": "Durham College",
                "destinations": [],
                "coordinates": latlngs,
                "summary": "Summary will be here...",
            }
        ]
    }

    return jsonify(locations)


if __name__ == '__main__':
    app.run(port=8080, debug=True)
