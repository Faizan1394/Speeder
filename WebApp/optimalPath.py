import osmnx as ox
import networkx as nx
import numpy as np
import pandas as pd
from geopy.geocoders import Nominatim
import geopy.distance
from math import atan2, pi
from sklearn.cluster import KMeans


def build_graph(east, west, south, north):
    """
    Define the limits of the map by specifying the boundary longitudes
    and latitudes.

    Create the graph object.

    Return the graph.
    """
    G = ox.graph_from_bbox(east, west, south, north, network_type='drive')
    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)
    return G


def address_to_coord(address):
    """
    Take address information and use Geopy to get its coordinates.
    """
    locator = Nominatim(user_agent='capstone2_project')
    location = locator.geocode(address)

    if location:
        return (location.latitude, location.longitude)
    else:
        print('Address Not Found')


def cluster_destinations(destinations, drivers):
    """
    Use the list of destination coordinates and the number of drivers.
    Perform K-Means to cluster the destinations.
    Returns the list of destination tuples separated as sublists according
    to their cluster.
    """
    kmeans = KMeans(n_clusters=drivers)
    kmeans.fit(destinations)
    clusters = []
    for i in range(drivers):
        group = []
        for j in range(len(destinations)):
            if kmeans.labels_[j] == i:
                group.append(destinations[j])
        clusters.append(group)
    return clusters


def coords_to_node(graph, coords):
    """
    Take coordinates and returns the closest node in the graph.
    """
    return ox.get_nearest_node(graph, coords)


def node_to_coords(graph, node):
    """
    Gets the latitude and logitude of a graph node.
    """
    return (graph.nodes[node]['y'], graph.nodes[node]['x'])


def dest_address_and_node(graph, dest_addresses):
    """
    To go back and forth between the actual address and the graph node.
    This will be used in the route display sections.
    """
    dest_dict = dict()
    for address in dest_addresses:
        coords = address_to_coord(address)
        node = coords_to_node(graph, coords)
        dest_dict[address] = node
    return dest_dict


def dist(source_node, destination_node):
    """
    Takes two nodes, gets their coordinates and uses Geopy to calculate
    the distance between them in metres.
    """
    return geopy.distance.distance(node_to_coords(G, source_node),
                                   node_to_coords(G, destination_node)).m


# We now work within a cluster
# We want to keep track of the destinations visited within that cluster
# and the optimal path from to visit each destination within the cluster.
visited = []
route = []


def aStarMulti(start_node, destinations_nodes, graph, weight, visited, route):
    """
    This algorithm will determine the order in which to visit each destination in each cluster,
    and the optimal path from the start location, through all destinations.
    We take the starting location, the list of destinations, the graph, the chosen weight -
    'travel_time' or 'length' - and the two previous lists.
    This is a recursive function.  While there are destinations still to visit, the reached
    destination becomes the starting point for the next function call.
    """

    if not destinations_nodes:
        return 'Done'
        # For each destination, calculate the distance to the starting point
    distances = []
    for d in destinations_nodes:
        distances.append(dist(start_node, d))
    # Get the index of the closest destination
    minIndex = distances.index(min(distances))
    # Get the corresponding destination node
    minNode = destinations_nodes[minIndex]
    # Add this to the list of visited destinations
    visited.append(minNode)
    # Get the optimal path to this destination
    path = nx.astar_path(graph, start_node, minNode, weight=weight, heuristic=dist)
    # Add this to the current route
    route.append(path)
    # Remove this destination from the list
    destinations_nodes.pop(minIndex)
    # If there are still destinations to visit, call the function again with the
    # current location as the new starting point
    if destinations_nodes:
        aStarMulti(minNode, destinations_nodes, graph, weight, visited, route)


def direction_between_points(pt1, pt2):
    """
    Takes two tuples of latitudes and longitudes.
    Returns the compass direction from point 1 to point 2.
    """
    delta_x = pt2[1] - pt1[1]
    delta_y = pt2[0] - pt1[0]

    degrees = atan2(delta_x, delta_y) / pi * 180

    if degrees < 0:
        degrees = 360 + degrees

    compass = ['north', 'northeast', 'east', 'southeast',
               'south', 'southwest', 'west', 'northwest', 'north']

    compass_dir = round(degrees / 45)
    return compass[compass_dir]


def full_route_info(graph, route, dests_list):
    """
    Creates a DataFrame containing the starting node, street name,
    length, direction of travel, speed, and ending node, for each edge in the graph.
    We will also label which nodes represent the user's destinations.
    """
    route_info = list()
    num_steps = len(route)
    i = 0
    j = 1
    # We want to get the information for every step in the route
    # We handle if any information is unlisted or unknown
    while j < num_steps:
        step_info = list()
        step_info.append(route[i])
        try:
            name = graph[route[i]][route[j]][0]['name']
            # Sometimes a street may change names within a segment - for example, switching
            # from west to east.  In these cases we will just take the first name.
            if type(name) == list:
                name = name[0]
        except KeyError:
            # Sometimes street names are labeled as "links"
            # In these cases I will relabel them with the previous street
            try:
                name = graph[route[i - 1]][route[j - 1]][0]['name']
            except KeyError:
                name = 'Unnamed'
        step_info.append(name)
        try:
            seg_len = graph[route[i]][route[j]][0]['length']
        except KeyError:
            seg_len = 0
        step_info.append(seg_len)
        # We want to calculate the direction the edge is travelling in
        start = node_to_coords(graph, route[i])
        end = node_to_coords(graph, route[j])
        # Use above function to calculate the direction from the start of the
        # edge to its end
        step_info.append(direction_between_points(start, end))

        seg_speed = graph[route[i]][route[j]][0]['speed_kph']
        step_info.append(seg_speed)
        step_info.append(route[j])
        # Identify if the end node of the edge is a destination
        if route[j] in dests_list:
            step_info.append('Yes')
        else:
            step_info.append('No')

        route_info.append(step_info)
        i += 1
        j += 1

    # Create a data frame of this information
    columns = ['Start Node', 'Street Name', 'Length', 'Direction', 'Speed', 'End Node', 'Destination?']
    return pd.DataFrame(route_info, columns=columns)


def get_turn_dir(graph, node1, node2, node3):
    """
    node1 is starting node for first segment,
    node2 is the shared node between segments,
    node3 is the end node of second segment.
    """
    # First, get coordinates for each of the nodes
    p1 = [graph.nodes[node1]['x'], graph.nodes[node1]['y']]
    p2 = [graph.nodes[node2]['x'], graph.nodes[node2]['y']]
    p3 = [graph.nodes[node3]['x'], graph.nodes[node3]['y']]

    # Next, define the line segments as vectors
    p1top2 = [m - n for m, n in zip(p2, p1)]
    p2top3 = [m - n for m, n in zip(p3, p2)]
    p1top3 = [m - n for m, n in zip(p3, p1)]

    # Next, compute the cross product of the vectors
    crossprod = np.cross(p1top3, p1top2)

    if crossprod > 0:
        return 'Right'
    elif crossprod < 0:
        return 'Left'
    else:
        return 'No turn'


def add_turns(route_df, graph):
    """
    Locate all the rows where the street name changes in the following row.
    Create a dictionary with these as keys - the values will calculate the direction
    of the turn using the previous function.
    Adds a new column in the df showing the turn direction.
    """
    # Get the rows where the street changes in the following row
    # These will be the turns
    turn_indexes = []
    for ind in route_df.index:
        if ind == route_df.index[-1]:
            pass
        elif route_df.iloc[ind]['Street Name'] == route_df.iloc[ind + 1]['Street Name'] and ind != route_df.index[-1]:
            pass
        else:
            turn_indexes.append(ind)
    # Use the above function to get the direction of these turns
    turns_to_make = dict()
    for ind in turn_indexes:
        turn_dir = get_turn_dir(graph, route_df.iloc[ind]['Start Node'], route_df.iloc[ind]['End Node'],
                                route_df.iloc[ind + 1]['End Node'])
        turns_to_make[ind] = turn_dir
    # Create a new column in the dataframe for this information
    turns_list = [None] * len(route_df)
    for i in turns_to_make.keys():
        turns_list[i] = turns_to_make[i]

    route_df['Turn Direction'] = turns_list
    return route_df


def get_break_points(route_df):
    """
    Get the row numbers where there are turns or destinations.
    These rows will be kept in the route summary, and all rows in between each
    break point will be condensed into a single entry with the total length and
    appropriate starting and ending nodes.
    """
    break_points = []
    for row in range(len(route_df)):
        if route_df['Destination?'][row] == 'Yes' or route_df['Turn Direction'][row] != None:
            break_points.append(row)
        row += 1
    return break_points


segments = []


def get_seg(start, segments, break_points, route_df):
    """
    This function will recursively create a list containing lists of the indexes for each leg.
    The identified breakpoints will be the starting points for each sublist.

    """
    seg = []
    for row in range(start, len(route_df)):
        seg.append(row)
        if row in break_points:
            break
    segments.append(seg)
    current = seg[-1] + 1
    if current <= len(route_df) - 1:
        get_seg(current, segments, break_points, route_df)


def get_simple_route(route_df, segments):
    """
    Produce a dataframe with the simplified route information as described above.
    """
    simple_route = []
    for leg in segments:
        # Segments containing a single index are added to the route
        # These are segments that end in destinations or turns
        if len(leg) == 1:
            leg_info = dict()
            leg_info['Start Node'] = route_df.loc[leg[0]]['Start Node']
            leg_info['Street Name'] = route_df.loc[leg[0]]['Street Name']
            leg_info['Length'] = route_df.loc[leg[0]]['Length']
            leg_info['Direction'] = route_df.loc[leg[0]]['Direction']
            leg_info['Speed'] = route_df.loc[leg[0]]['Speed']
            leg_info['End Node'] = route_df.loc[leg[0]]['End Node']
            leg_info['Destination?'] = route_df.loc[leg[0]]['Destination?']
            leg_info['Turn Direction'] = route_df.loc[leg[0]]['Turn Direction']
            simple_route.append(leg_info)
        else:
            # Longer segments will be combined
            # The end of these segments will be turns or destinations
            leg_info = dict()
            leg_info['Start Node'] = route_df.loc[leg[0]]['Start Node']
            leg_info['Street Name'] = route_df.loc[leg[0]]['Street Name']
            length = 0
            # Combine the lenghts into one value
            for row in leg:
                length += route_df.loc[row]['Length']
            leg_info['Length'] = length
            leg_info['Direction'] = route_df.loc[leg[0]]['Direction']
            leg_info['Speed'] = route_df.loc[leg[0]]['Speed']
            # The end node will correspond to the last leg in this segment
            leg_info['End Node'] = route_df.loc[leg[-1]]['End Node']
            leg_info['Destination?'] = route_df.loc[leg[-1]]['Destination?']
            leg_info['Turn Direction'] = route_df.loc[leg[-1]]['Turn Direction']
            simple_route.append(leg_info)
    return pd.DataFrame(simple_route)


def print_route_summary(simplified_route, dest_dict, graph):
    path = ""
    visitOrder = []
    """
    Display a simple summary with all relevant information for the driver.
    """
    # Get the destination nodes
    destinations = simplified_route[simplified_route['Destination?'] == 'Yes']['End Node']
    num_dest = len(destinations)

    path = path + ('You have {} locations to visit:'.format(num_dest))
    # Using the dictionary, print off the destination addresses
    for d in destinations:
        for key, value in dest_dict.items():
            if value == d:
                path = path + "\n" + (key)
                latLong = node_to_coords(graph, value)
                mydict = {key: latLong}
                visitOrder.append(mydict)
    path = path + "\n" + '\nStart!'

    for ind in simplified_route.index:
        # Display information for the leg of the route
        direct = simplified_route['Direction'][ind]
        name = simplified_route['Street Name'][ind]
        length = simplified_route['Length'][ind]
        speed = simplified_route['Speed'][ind]
        path = path + "\n" + ('Head {} on {} for {:.2f} metres at {} km/h.'.format(direct, name, length, speed))
        # At the end of the leg, get the turn
        turn = simplified_route['Turn Direction'][ind]
        # If there is no turn there are two cases - either it is marked "continue" -
        # in cases where a road changes speed or its name changes from west to east, for example -
        # or when we reach the last node on the route
        is_dest = simplified_route['Destination?'][ind]
        if turn == None and is_dest == 'No':
            # If we aren't at a destination, write continue
            if ind != simplified_route.index[-1]:
                path = path + "\n" + ('Continue')
            else:
                # Display no turn information when the route is finished
                pass
        elif turn == None and is_dest == 'Yes':
            # Have arrived at a destination.
            destnode = simplified_route['End Node'][ind]
            # Get the address
            for key, value in dest_dict.items():
                if value == destnode:
                    add = key
            path = path + "\n" + ('\nYou have reached a destination:' + add)
            # This destination is unlikely to be at an actual graph node, so we want to provide some info
            # Get the coordinates of the node and the actual address
            nodecoords = node_to_coords(graph, destnode)
            addcoords = address_to_coord(add)
            # Calculate the distance between these
            dest_dist = geopy.distance.distance(nodecoords, addcoords).m
            # Calculate the direction in which the destination will be
            dest_dir = direction_between_points(nodecoords, addcoords)
            path = path + "\n" + ('It is {:.2f} metres to your {}.\n'.format(dest_dist, dest_dir))
        else:
            # If there is a turn, indicate it
            path = path + "\n" + ('Turn' + turn.upper())

    path = path + "\n" + ('You have visited all of your destinations!')
    return path, visitOrder


def avoid_a_street(graph, street_list):
    """
    Will take a list of street names and return a new graph with these
    edges removed.
    Since the graph is defined at the start and will be used for all uses,
    we first make a copy of the graph before manipulating it.
    Returns a new graph object with appropriate edges removed.
    """
    G2 = nx.Graph.copy(graph)
    edges_to_remove = []
    for edge in G2.edges:
        try:
            # Get the street name for each edge segment
            seg = G2.edges[edge][0]['name']
            # Add to list of edges to be removed
            if seg in street_list:
                edges_to_remove.append(edge)
        except KeyError:
            pass
    # Remove edges
    G2.remove_edges_from(edges_to_remove)
    return G2


def avoid_a_roadtype(graph, street_type_list):
    """
    Will take a road type - 'motorway', 'secondary', 'tertiary', 'residential' -
    and remove this edges from the graph.
    This will allow a user to avoid high speed, or low speed, roads, if possible.

    NOTE:
    This function will always follow avoid_a_street and so will take a copy of a graph.
    Graph copies have their information stored at inside a nested dictionary.
    """
    G2 = nx.Graph.copy(graph)
    edges_to_remove = []
    for edge in G2.edges:
        try:
            # The highway attribute of the edge gives the road type
            seg = G2.edges[edge][0][0]['highway']
            if seg in street_type_list:
                edges_to_remove.append(edge)
        except KeyError:
            pass
    G2.remove_edges_from(edges_to_remove)
    return G2


def get_starting_loc():
    """
    Prompts the user for their starting address.
    """
    print('Enter your starting address and city in full.')
    print('Ex: 23 Vanier Street Whitby')
    start = input()
    return start.title()


def get_destinations():
    """
    Prompts the user for their destinations.
    """
    print('\nEnter your destination addresses and cities in full.')
    print('Press enter after each entry.')
    print('Type "DONE" when you are finished.')
    destinations = []
    while True:
        dest = input()
        if dest.upper() == 'DONE':
            break
        elif dest:
            destinations.append(dest.title())
    return destinations


def get_customizations():
    """
    Asks the user to enter a list of streets they want to avoid,
    one at a time.
    Returns a list of street names.
    """
    print('\nEnter any streets you want to avoid.')
    print('Enter in full. ex: "Brock Street".')
    print('Press enter after each entry.')
    print('Type "DONE" when you are finished.')
    avoid = []
    while True:
        street = input()
        if street.upper() == 'DONE':
            break
        else:
            avoid.append(street.title())
    return avoid


def get_customizations2():
    """
    Gets further user specifications based on road speeds.
    Returns a list of road types to be removed.
    """
    avoid = []
    highways = input('Avoid highways? (Y/N): ')
    if highways.lower().startswith('y'):
        avoid.append('motorway')

    return avoid


def get_customizations3():
    """
    Gets further user specifications on what to optimize on.
    """
    how_opt = input('Do you want to optimize based on travel time (T) or distance traveled (D)? ')
    if how_opt.lower().startswith('T'):
        return 'travel_time'
    else:
        return 'length'


# Build the graph - this is Whitby/Oshawa for testing purposes - east, west, south, north
G = build_graph(43.984503, 43.862879, -78.954552, -78.821660)