from flask import Flask, request, jsonify, render_template
import optimalPath

app = Flask(__name__)



@app.route('/')
def index():
    """ Displays the index page accessible at '/'
    """
    return render_template('MapGUI.html')

# Build the graph - this is Whitby/Oshawa for testing purposes - east, west, south, north
G = optimalPath.build_graph(43.984503, 43.862879, -78.954552, -78.821660)
def get_coordinates(locations, drivers):
    """
    This function should return dictionary as shown below.
    :param locations: list of addresses
    :param drivers: number of drivers
    :return:
    """
    
    #get the starting location and convert it to coordinates
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
        #print('\n\nDriver', driver+1, 'Route:')
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
        summary,visitOrder = optimalPath.print_route_summary(simplified_route, dest_dict, G)
        
        #get coordinates for full path from start to finish
        for node in simplified_route['Start Node']:
            nCord = optimalPath.node_to_coords(G, node)
            coordinates.append([nCord[0],nCord[1]])
        
        
        #print(summary)
        #print(visitOrder)
        
        #dst =[]

       # for i in visited:
         #   dst.append(int(i))
        
        info = {
            "startingPointName": route_df['Street Name'][0],
            "destinations": visitOrder,
            "coordinates": coordinates,
            "summary": summary,
            }
        
        dicts.append(info)
     
  #  for i in range (len(dicts)):
     #   print(i)
      #  print(dicts[i])
        #print("\n\n\n\n")
     
        
    output = {
        "locations": dicts
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
