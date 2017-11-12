import csv
import copy
from math import sin, cos, sqrt, atan2, radians
from contextlib import contextmanager
from scripts.maps_client import get_biking_time

BIKE_SPEED_M_PER_MIN = 250.
ALL_NODES_DB = {}


@contextmanager
def create_csv_reader(filename):
    file = open(filename, 'r')
    reader = csv.DictReader(file)
    yield reader
    file.close()


def time_str_to_int(time_str):
    elms = time_str.split(":")
    return 60 * int(elms[0]) + int(elms[1])


def time_int_to_str(time_int):
    elms = []
    elms.append(int(time_int % 60))
    time_int /= 60
    elms.append(int(time_int % 60))
    elms.reverse()

    s = ""
    for e in elms:
        s += str(e).zfill(2) + ":"
    s = s[0:-1]
    return s


def straight_line_dist_bw_nodes(node1, node2):
    """
    Calculate distance between two nodes.
    :param node1:
    :param node2:
    :return: Distance in meters.
    """
    lat1 = radians(abs(node1.lat))
    lon1 = radians(abs(node1.lon))
    lat2 = radians(abs(node2.lat))
    lon2 = radians(abs(node2.lon))

    R = 6373.
    dlon = abs(lon2 - lon1)
    dlat = abs(lat2 - lat1)

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c

    return distance * 1000


def biking_duration_bw_nodes(node1, node2):
    start_point = "{},{}".format(node1.lat, node1.lon)
    end_point = "{},{}".format(node2.lat, node2.lon)
    duration = get_biking_time(start_point, end_point)

    if duration is None:
        # print "WARN: fallback to simple biking duration"
        # Fallback on rough estimate using avg speed
        dist = straight_line_dist_bw_nodes(node1, node2)
        duration = max(5, int(dist / BIKE_SPEED_M_PER_MIN))

    return duration


def get_close_nodes(node, all_nodes, dist_th=8000):
    """
    :param node: the node in question
    :param all_nodes: list of all nodes to check against
    :param dist_th: return all nodes closer than this threshold
    :return: list of nodes
    """
    result_nodes = []
    for n in all_nodes:
        if n.id == node.id:  # ignore self
            continue
        if straight_line_dist_bw_nodes(node, n) < dist_th:
            result_nodes.append(n)

    return result_nodes


def create_bike_connections(from_node, compute_end_time=True):
    all_nodes = Node.get_all_nodes()
    close_nodes = get_close_nodes(from_node, all_nodes)

    bike_connections = []
    for node in close_nodes:
        start_time = from_node.arrival_time
        if compute_end_time:
            end_time = start_time + biking_duration_bw_nodes(from_node, node)
        else:
            end_time = copy.deepcopy(start_time)
        connection = Connection(from_node.id, start_time, node.id, end_time, "bike")

        # if node.direction == "SB":  # Hack for debugging
        #     continue

        bike_connections.append(connection)

    return bike_connections


def setup_DB(all_nodes):
    # Create global lookup
    all_nodes_db = {}
    for n in all_nodes:
        all_nodes_db[n.id] = n

    global ALL_NODES_DB
    ALL_NODES_DB = all_nodes_db


def heuristic_time_to_destination(dest_node):
    return lambda node: straight_line_dist_bw_nodes(node, dest_node) / 2200.  # Travel reasonably fast 80 mph


class Node:
    def __init__(self, modes, id, name, direction, lat=0., lon=0.):
        self.modes = modes
        self.id = id
        self.name = name
        self.direction = direction
        self.lat = lat
        self.lon = lon
        self.connections = []
        self.arrival_time = 0
        self.departure_time = 0

        # for A* search
        self.cost = float("inf")
        self.from_node = None
        self.from_mode = None
        self.time_waiting = 0  # Time spent waiting at the parent node, before starting to move towards this node.
        self.time_moving = 0  # Time spent moving from parent to this node.
        self.first_dest_node = False

    def __repr__(self):
        # return "{} ({})".format(self.name, self.id)
        return "{} {} ({}) {} {}".format(
            self.name,
            self.direction,
            time_int_to_str(self.arrival_time),
            self.cost,
            self.from_mode,
        )

    def json_representation(self):
        return dict(
                id=self.id,
                name=self.name,
                arrival_time=self.arrival_time,
                departure_time=self.departure_time,
                arrival_time_str=time_int_to_str(self.arrival_time),
                departure_time_str=time_int_to_str(self.departure_time),
                waiting_time=self.time_waiting,
                moving_time=self.time_moving,
                arrival_mode=self.from_mode,
                cost=self.cost,
            )

    @classmethod
    def find_node_by_id(cls, id, make_copy=True):
        if make_copy:
            return copy.deepcopy(ALL_NODES_DB[id])
        else:
            return ALL_NODES_DB[id]

    @classmethod
    def get_all_nodes(cls, make_copy=True):
        if make_copy:
            return copy.deepcopy(list(ALL_NODES_DB.values()))
        else:
            return ALL_NODES_DB.values()

    @classmethod
    def cheapest_node(cls, nodes, h_func=None):
        best_cost = float('inf')
        best_node = None
        for node in nodes:
            # Compute and heuristic cost using provided function
            h_cost = 0
            if h_func is not None:
                h_cost = h_func(node)

            # Book keeping to find lowest cost node
            if node.cost + h_cost < best_cost:
                best_cost = node.cost + h_cost
                best_node = node

        return best_node


class Connection:
    def __init__(self, start_node_id, start_time_str, end_node_id, end_time_str, mode):
        self.start_node_id = start_node_id
        self.end_node_id = end_node_id
        if isinstance(start_time_str, str):
            self.start_time = time_str_to_int(start_time_str)
        else:
            self.start_time = start_time_str
        if isinstance(end_time_str, str):
            self.end_time = time_str_to_int(end_time_str)
        else:
            self.end_time = end_time_str
        self.mode = mode

    def __repr__(self):
        # return "Start: {} \t@{} \t\t\t{}\n  End: {} \t@{}".format(
        #     Node.find_node_by_id(self.start_node_id), time_int_to_str(self.start_time),
        #     self.mode,
        #     Node.find_node_by_id(self.end_node_id), time_int_to_str(self.end_time),
        # )

        return "Start: {} \t@{}".format(
            self.start_node_id, time_int_to_str(self.start_time)
        )
