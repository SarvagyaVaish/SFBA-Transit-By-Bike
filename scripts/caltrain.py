import util
import os
from util import Node, Connection


def create_path(path_rel_to_this_file):
    return os.path.join(os.path.dirname(__file__), path_rel_to_this_file)


def create_nodes():
    """
    Read caltrain stops and create create Node objects.
    :return: list of Nodes
    """
    nodes = []
    with util.create_csv_reader(create_path('data_caltrain/stops.txt')) as stops_reader:
        for stop_row in stops_reader:
            node = Node(
                modes=["caltrain", "bike"],
                id=stop_row['stop_id'],
                name=stop_row['stop_name'].replace(" Caltrain", ""),
                direction=stop_row['platform_code'],
                lat=float(stop_row['stop_lat']),
                lon=float(stop_row['stop_lon'])
            )
            nodes.append(node)

    return nodes


def create_connections(nodes, trip_id):
    # TODO: expand to include all trips.
    """
    Read caltrain trip data and create connections between nodes.
    :return: list of Connections
    """

    connections = []

    with util.create_csv_reader(create_path('data_caltrain/stop_times.txt')) as stop_times_reader:
        trip_sequence = {}
        for row in stop_times_reader:
            if row['trip_id'] == trip_id:
                trip_sequence[int(row['stop_sequence'])] = \
                    {
                        'time':    row['arrival_time'],
                        'stop_id': row['stop_id']
                    }

    number_of_stops = len(trip_sequence.keys())
    for i in range(1, number_of_stops):
        # start node
        start_node = filter(lambda n: n.id == trip_sequence[i]['stop_id'], nodes)[0]
        start_time = trip_sequence[i]['time']

        # end node
        end_node = filter(lambda n: n.id == trip_sequence[i+1]['stop_id'], nodes)[0]
        end_time = trip_sequence[i+1]['time']

        # append
        connection = Connection(start_node.id, start_time, end_node.id, end_time, "caltrain")
        connections.append(connection)

    return connections


def get_service_and_trip_information():
    service_to_trips_dict = {}

    with util.create_csv_reader(create_path('data_caltrain/trips.txt')) as trips_reader:
        for trip in trips_reader:
            if trip["service_id"] not in service_to_trips_dict.keys():
                service_to_trips_dict[trip["service_id"]] = []
            service_to_trips_dict[trip["service_id"]].append(trip["trip_id"])

    return service_to_trips_dict


class CaltrainModel:
    def __init__(self):
        self.nodes = create_nodes()
        self.connections = []

        service_dict = get_service_and_trip_information()
        trip_ids = service_dict['CT-17OCT-Combo-Weekday-01']  # Use weekday schedule

        for trip_id in trip_ids:
            self.connections += create_connections(self.nodes, trip_id)

        # print "[Caltrain] Node: {}, Connections: {}".format(len(self.nodes), len(self.connections))

    def keep_connections_bw(self, start_time, end_time):
        keep_list = []
        for connection in self.connections:
            if connection.start_time >= start_time and connection.end_time <= end_time:
                keep_list.append(connection)

        # print "Pruning from {} to {} connections.".format(len(self.connections), len(keep_list))
        self.connections = keep_list
