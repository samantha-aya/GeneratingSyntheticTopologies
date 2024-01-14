import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
import json

class Node:
    def __init__(self, region, utility, substation, adminIP, label, vlan, node_id):
        self.region = region
        self.utility = utility
        self.substation = substation
        self.adminIP = adminIP
        self.label = label
        self.vlan = vlan
        self.id = node_id

class CyberNode(Node):
    def __init__(self, protocol, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.protocol = protocol

class Switch(Node):
    def __init__(self, macTable, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.macTable = macTable

class Router(Node):
    def __init__(self, interfaces, routingTable, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.interfaces = interfaces
        self.routingTable = routingTable

class Relay(Node):
    def __init__(self, busNumber, relayType, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.busNumber = busNumber
        self.relayType = relayType

class RTU(Node):
    def __init__(self, substation_id, breaker_list, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.substation_id = substation_id
        self.breaker_list = breaker_list

class Firewall(Node):
    def __init__(self, acl, Latitude, Longitude, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.acl = acl
        self.Latitude = Latitude
        self.Longitude = Longitude

class RelayController(Node):
    def __init__(self, substation_id, relayIPlist, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.substation_id = substation_id
        self.relayIPlist = relayIPlist

class Link:
    def __init__(self, source, destination, link_type, bandwidth, distance, protocol):
        self.source = source
        self.destination = destination
        self.link_type = link_type
        self.bandwidth = bandwidth
        self.distance = distance
        self.protocol = protocol

class Substation:
    def __init__(self, region, utility, substation, substation_id, latitude, longitude):
        self.region = region
        self.utility = utility
        self.substation = substation
        self.substation_id = substation_id
        self.latitude = latitude
        self.longitude = longitude
        self.nodes = []
        self.links = []

    def add_node(self, node):
        self.nodes.append(node)

    def add_link(self, source_id, destination_id, link_type, bandwidth, distance, protocol):
        link = Link(source=source_id, destination=destination_id, link_type=link_type, bandwidth=bandwidth, distance=distance, protocol=protocol)
        self.links.append(link)

class Utility:
    def __init__(self, region, utility, substations, utility_id, latitude, longitude):
        self.region = region
        self.utility = utility
        self.substations = substations
        self.utility_id = utility_id
        self.latitude = latitude
        self.longitude = longitude
        self.nodes = []
        self.links = []

        # Initialize utility components
        self.initialize_components()

    def initialize_components(self):
        base_id = f"{self.region}.{self.utility}.{self.utility_id}.VLAN1."

        # Create utility components
        self.firewall1 = Firewall("ACL1", self.latitude, self.longitude, self.region, self.utility, self.utility_id, "192.168.100.1", "Firewall01", "VLAN1", base_id + "Firewall1")
        self.router1 = Router({}, {}, self.region, self.utility, self.utility_id, "192.168.100.2", "Router01", "VLAN1", base_id + "Router1")
        self.switch = Switch("MAC_Table", self.region, self.utility, self.utility_id, "192.168.100.3", "Switch01", "VLAN1", base_id + "Switch")
        self.ems = CyberNode("EMS_Protocol", self.region, self.utility, self.utility_id, "192.168.100.4", "EMS01", "VLAN1", base_id + "EMS")
        self.router2 = Router({}, {}, self.region, self.utility, self.utility_id, "192.168.100.5", "Router02", "VLAN1", base_id + "Router2")
        self.firewall2 = Firewall("ACL2", self.latitude, self.longitude, self.region, self.utility, self.utility_id, "192.168.100.6", "Firewall02", "VLAN1", base_id + "Firewall2")
        self.dmz = CyberNode("DMZ_Protocol", self.region, self.utility, self.utility_id, "192.168.100.7", "DMZ01", "VLAN1", base_id + "DMZ")

        # Add nodes to utility
        self.nodes.extend([self.firewall1, self.router1, self.switch, self.ems, self.router2, self.firewall2, self.dmz])

        # Create links between nodes
        self.add_link(self.firewall1.id, self.router1.id, "Ethernet", 1000, 10, "IP")
        self.add_link(self.router1.id, self.switch.id, "Ethernet", 1000, 10, "IP")
        self.add_link(self.ems.id, self.switch.id, "Ethernet", 1000, 10, "IP")
        self.add_link(self.switch.id, self.router2.id, "Ethernet", 1000, 10, "IP")
        self.add_link(self.router2.id, self.firewall2.id, "Ethernet", 1000, 10, "IP")
        self.add_link(self.firewall2.id, self.dmz.id, "Ethernet", 1000, 10, "IP")

    def add_link(self, source_id, destination_id, link_type, bandwidth, distance, protocol):
        link = Link(source=source_id, destination=destination_id, link_type=link_type, bandwidth=bandwidth, distance=distance, protocol=protocol)
        self.links.append(link)

class Regulatory:
    def __init__(self, region, utilities):
        self.region = region
        self.utilities = utilities
        self.regulatory_id = "{}".format(region)
        self.firewall = Firewall("ACL", "0.0", "0.0", region, None, self.regulatory_id, "192.168.100.1", "RegFirewall", "VLAN1", "RegFirewall1")
        self.router = Router({}, {}, region, None, self.regulatory_id, "192.168.100.2", "RegRouter", "VLAN1", "RegRouter1")
        self.iccp_server = CyberNode("ICCP", region, None, self.regulatory_id, "192.168.100.3", "ICCP_Server", "VLAN1", "ICCP1")
        self.links = [
            Link(self.iccp_server.id, self.router.id, "Ethernet", 1000, 10, "ICCP"),
            Link(self.router.id, self.firewall.id, "Ethernet", 1000, 10, "IP")
        ]

    def add_utility_links(self):
        for utility in self.utilities:
            for substation in utility.substations:
                for node in substation.nodes:
                    if isinstance(node, Firewall):
                        self.links.append(Link(self.firewall.id, node.id, "Ethernet", 1000, 10, "IP"))



class CyberPhysicalSystem:
    def load_substations_from_csv(self, csv_file):
        df = pd.read_csv(csv_file, skiprows=1)
        substations = []
        unique_node_no = 1  # Starting number for unique node no.

        for _, row in df.iterrows():
            # Constructing the base part of the ID
            base_id = f"{row['Area Name']}.Utility{row['Sub Num']}.{row['Sub Num']}.VLAN1."

            # Create substation instance with custom ID
            substation_id = base_id + str(unique_node_no)
            unique_node_no += 1
            sub = Substation(
                region=row['Area Name'],
                utility=None,
                substation=row['Sub Name'],
                substation_id=substation_id,
                latitude=row['Latitude'],
                longitude=row['Longitude']
            )

            # Create relay and relay controller nodes
            relay_controller_id = base_id + str(unique_node_no)
            unique_node_no += 1
            relay_controller = RelayController("Sub" + str(row['Sub Num']), [], sub.region, None, row['Sub Name'], "192.168.1.100", "Controller01", "VLAN1", relay_controller_id)
            sub.add_node(relay_controller)

            # Create relays and link them to the relay controller
            for i in range(int(row['# of Buses'])):
                relay_id = base_id + str(unique_node_no)
                unique_node_no += 1
                relay = Relay("Bus1", "Type1", row['Area Name'], None, row['Sub Name'], "192.168.1.1", "Relay01",
                              "VLAN1", relay_id)
                sub.add_node(relay)
                sub.add_link(relay.id, relay_controller.id, "Ethernet", 100, 10, "DNP3")

            # Create other nodes (Switch1, Switch2, Router, Desktop, Firewall)
            switch1_id = base_id + str(unique_node_no)
            unique_node_no += 1
            switch2_id = base_id + str(unique_node_no)
            unique_node_no += 1
            router_id = base_id + str(unique_node_no)
            unique_node_no += 1
            desktop_id = base_id + str(unique_node_no)
            unique_node_no += 1
            firewall_id = base_id + str(unique_node_no)
            unique_node_no += 1
            switch1 = Switch("MAC_Table1", sub.region, None, row['Sub Name'], "192.168.2.1", "Switch01", "VLAN1", switch1_id)
            switch2 = Switch("MAC_Table2", sub.region, None, row['Sub Name'], "192.168.2.2", "Switch02", "VLAN1", switch2_id)
            router = Router({}, {}, sub.region, None, row['Sub Name'], "192.168.3.1", "Router01", "VLAN1", router_id)
            desktop = CyberNode("Protocol", sub.region, None, row['Sub Name'], "192.168.4.1", "Desktop01", "VLAN1", desktop_id)
            firewall = Firewall("ACL", sub.latitude, sub.longitude, sub.region, None, row['Sub Name'], "192.168.5.1", "Firewall01", "VLAN1", firewall_id)
            sub.add_node(switch1)
            sub.add_node(switch2)
            sub.add_node(router)
            sub.add_node(desktop)
            sub.add_node(firewall)

            # Create links between nodes
            sub.add_link(relay_controller.id, switch1.id, "Ethernet", 100, 10, "DNP3")
            sub.add_link(switch1.id, router.id, "Ethernet", 1000, 10, "IP")
            sub.add_link(desktop.id, switch2.id, "Ethernet", 100, 10, "IP")
            sub.add_link(switch2.id, router.id, "Ethernet", 1000, 10, "IP")
            sub.add_link(router.id, firewall.id, "Ethernet", 1000, 10, "IP")

            substations.append(sub)
        return substations

    def cluster_substations(self, substations, n_clusters=4):
        # Extract latitudes and longitudes for clustering
        locations = np.array([(sub.latitude, sub.longitude) for sub in substations])
        kmeans = KMeans(n_clusters=n_clusters)
        kmeans.fit(locations)

        # Calculate centroids of each cluster
        centroids = kmeans.cluster_centers_

        # Create Utility instances and set their latitude and longitude to the cluster centroids
        utilities = []
        for i, centroid in enumerate(centroids):
            utility = Utility(region="Region" + str(i+1), utility="Utility" + str(i+1), substations=[], utility_id="Util" + str(i+1), latitude=centroid[0], longitude=centroid[1])
            utilities.append(utility)

        # Assign substations to the closest utility and update their utility attribute
        for sub, label in zip(substations, kmeans.labels_):
            utilities[label].substations.append(sub)
            sub.utility = utilities[label].utility

        return utilities
def to_json(obj):
    """Converts objects to a JSON-friendly format."""
    if isinstance(obj, Node) or isinstance(obj, Link) or isinstance(obj, Substation) or isinstance(obj, Utility) or isinstance(obj, Regulatory):
        return obj.__dict__
    elif isinstance(obj, list):
        return [to_json(item) for item in obj]
    else:
        return obj

def output_to_json_file(regulatory, filename="regulatory.json"):
    """Outputs the regulatory structure to a JSON file."""
    with open(filename, "w") as file:
        json.dump(regulatory, file, default=to_json, indent=4)

def generate_system_from_csv(csv_file):
    cps = CyberPhysicalSystem()
    substations = cps.load_substations_from_csv(csv_file)
    utilities = cps.cluster_substations(substations)
    regulatory = Regulatory(region="Region1", utilities=utilities)
    regulatory.add_utility_links()  # Add links from regulatory firewall to utility firewalls
    output_to_json_file(regulatory)


# Example usage
generate_system_from_csv("Substation_14bus.csv")

