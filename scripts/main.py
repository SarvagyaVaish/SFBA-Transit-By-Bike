from scripts.caltrain import CaltrainModel
from scripts.util import create_bike_connections, time_str_to_int, time_int_to_str
from scripts.util import Node, setup_DB, biking_duration_bw_nodes, heuristic_time_to_destination

import logging
logger = logging.getLogger(__name__)


NUMBER_OF_SOLUTIONS = 10


def cmp_solutions(a, b):
    dest_a = a[-1]
    dest_b = b[-1]
    if dest_a["arrival_time"] < dest_b["arrival_time"]:
        return -1
    elif dest_a["arrival_time"] > dest_b["arrival_time"]:
        return 1
    else:
        if dest_a["cost"] < dest_b["cost"]:
            return -1
        elif dest_a["cost"] > dest_b["cost"]:
            return 1
        else:
            return 0

def cmp_to_key(mycmp):
    'Convert a cmp= function into a key= function'
    class K:
        def __init__(self, obj, *args):
            self.obj = obj
        def __lt__(self, other):
            return mycmp(self.obj, other.obj) < 0
        def __gt__(self, other):
            return mycmp(self.obj, other.obj) > 0
        def __eq__(self, other):
            return mycmp(self.obj, other.obj) == 0
        def __le__(self, other):
            return mycmp(self.obj, other.obj) <= 0
        def __ge__(self, other):
            return mycmp(self.obj, other.obj) >= 0
        def __ne__(self, other):
            return mycmp(self.obj, other.obj) != 0
    return K


def find_routes(departure_coordinate, arrival_coordinate, departure_time, schedule):
    """
    :param departure_coordinate:  tuple of (lat, long)
    :param arrival_coordinate: tuple of (lat, long)
    :param departure_time: Departure time string
    :return: Json with directions
    """

    # Load transit models
    caltrain = CaltrainModel(schedule)

    # Create basic nodes
    departure_node = Node(modes=["bike"], id="departure", name="Departure", direction="",
                          lat=departure_coordinate[0],
                          lon=departure_coordinate[1]
                          )

    arrival_node = Node(modes=["bike"], id="arrival", name="Arrival", direction="",
                        lat=arrival_coordinate[0],
                        lon=arrival_coordinate[1]
                        )

    setup_DB(caltrain.nodes + [departure_node] + [arrival_node])

    #
    # Graph search
    #

    # Set initial node
    first_node = Node.find_node_by_id("departure")
    first_node.arrival_time = time_str_to_int(departure_time)
    first_node.cost = 0
    final_node_id = "arrival"

    # Remove connections that are in the past, or too far off in the future
    caltrain.keep_connections_bw(first_node.arrival_time - 1, first_node.arrival_time + 3 * 60)

    open_set = [first_node]

    closed_set = []
    solutions_count = 0
    solutions = []

    while len(open_set) > 0:
        # Get next node to explore
        current_node = Node.cheapest_node(
            open_set,
            h_func=None,
            # h_func=heuristic_time_to_destination(Node.find_node_by_id("arrival"))
        )

        # logger.warn("\n----\n\nCurrent node: " + str(current_node))

        open_set.remove(current_node)
        closed_set.append(current_node)

        # Check for goal
        if current_node.id == final_node_id:
            # logger.warn("\nFound solution:\n" + str(current_node.json_representation()))
            current_solution_json = []
            solution_node = current_node
            wait_at_previous_node = 0

            while solution_node is not None:
                wait_at_current_node = wait_at_previous_node
                wait_at_previous_node = solution_node.time_waiting
                solution_node.departure_time = solution_node.arrival_time + wait_at_current_node
                current_solution_json.append(solution_node.json_representation())

                # Go to next node in solution
                solution_node = solution_node.from_node

            current_solution_json.reverse()
            solutions.append(current_solution_json)

            solutions_count += 1
            if solutions_count < NUMBER_OF_SOLUTIONS:
                continue
            else:
                break

        # Add connections for caltrain
        if "caltrain" in current_node.modes:
            all_connections = caltrain.connections

            # Find connections from current node
            relevant_connections = []
            for connection in all_connections:
                if connection.start_node_id == current_node.id:
                    relevant_connections.append(connection)

            # Find connections that are still possible
            possible_connections = []
            for connection in relevant_connections:
                if connection.start_time >= current_node.arrival_time:
                    possible_connections.append(connection)

            # Set connections
            current_node.connections += possible_connections

        # Add connections for bikes
        if "bike" in current_node.modes:
            bike_connections = create_bike_connections(current_node, compute_end_time=False)

            # Prune bike connections
            pruned_connections = []
            for connection in bike_connections:
                conn_destination_node = Node.find_node_by_id(connection.end_node_id)
                conn_departure_node = Node.find_node_by_id(connection.start_node_id)

                # 1. Ignore biking b/w NB and SB stations
                if conn_departure_node.name == conn_destination_node.name:
                    continue

                # 2. Don't bike between stations of the same provider
                if "caltrain" in conn_departure_node.modes and "caltrain" in conn_destination_node.modes:
                    continue

                # 3. Do not create loops
                keep_connection = True
                prev_node = current_node.from_node
                while prev_node is not None:
                    if prev_node.id == conn_destination_node.id:
                        keep_connection = False
                        break
                    prev_node = prev_node.from_node
                if not keep_connection:
                    continue

                # We want to keep this connection. Calculate end_time.
                connection.end_time = connection.start_time + biking_duration_bw_nodes(conn_departure_node, conn_destination_node)
                pruned_connections.append(connection)

            current_node.connections += pruned_connections

        # logger.warn("\nNew connections: ")
        # for connection in current_node.connections:
        #     logger.warn(str(connection))

        # Iterate over connections and add nodes
        new_nodes = []
        for connection in current_node.connections:
            new_node_id = connection.end_node_id
            new_node = Node.find_node_by_id(new_node_id)
            new_node.arrival_time = connection.end_time
            new_node.from_node = current_node
            new_node.from_mode = connection.mode

            if current_node.id == "departure":  # Mark new node as first "real" node, aka first destination node.
                new_node.first_dest_node = True

            # Cost
            time_waiting = connection.start_time - current_node.arrival_time
            time_moving = connection.end_time - connection.start_time
            bike_penalty = 1.0 if connection.mode == "bike" else 1.0
            waiting_penalty = 0.0 if current_node.first_dest_node else 1.0
            new_node.cost = current_node.cost + time_moving * bike_penalty + time_waiting * waiting_penalty

            new_node.time_waiting = time_waiting
            new_node.time_moving = time_moving

            new_nodes.append(new_node)

        # logger.warn("\nNew nodes")
        # for new_node in new_nodes:
        #     logger.warn(str(new_node))

        # Add new node to open set
        open_set += new_nodes

        # Prune open set for duplicates
        open_set.sort(key=lambda x: x.cost)
        unique_open_set = []
        i = 0
        prev_node = None
        for i in range(len(open_set)):
            curr_node = open_set[i]
            accept = False
            if prev_node is None:
                accept = True
            elif prev_node.name != curr_node.name or prev_node.direction != curr_node.direction or prev_node.arrival_time != curr_node.arrival_time:
                accept = True

            if accept:
                unique_open_set.append(curr_node)
                prev_node = curr_node
        open_set = unique_open_set

        # logger.warn("\nOpen set")
        # for node in open_set:
        #     logger.warn(str(node))

    # Sort solutions based on arrival time
    solutions.sort(key=cmp_to_key(cmp_solutions))

    return solutions
