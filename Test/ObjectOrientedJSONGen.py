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

    def add_node(self, node):
        self.nodes.append(node)

    def add_link(self, source_id, destination_id, link_type, bandwidth, distance, protocol):
        link = Link(source=source_id, destination=destination_id, link_type=link_type, bandwidth=bandwidth, distance=distance, protocol=protocol)
        self.links.append(link)

class Regulatory:
    def __init__(self, region, utilities, regulatory_id):
        self.region = region
        self.utilities = utilities
        self.regulatory_id = regulatory_id

class CyberPhysicalSystem:
    # ... existing methods ...

    def load_substations_from_csv(self, csv_file):
        df = pd.read_csv(csv_file, skiprows=1)
        substations = []
        for _, row in df.iterrows():
            # Create substation instance
            sub = Substation(
                region=row['Area Name'],
                utility=None,
                substation=row['Sub Name'],
                substation_id=row['Sub Num'],
                latitude=row['Latitude'],
                longitude=row['Longitude']
            )

            # Create relay and relay controller nodes
            relay_controller = RelayController("Sub" + str(row['Sub Num']), [], "Region1", None, row['Sub Name'], "192.168.1.100", "Controller01", "VLAN1", "Controller1")
            sub.add_node(relay_controller)

            # Create relays and link them to the relay controller
            for i in range(int(row['# of Buses'])):
                relay = Relay("Bus" + str(i+1), "Type1", row['Area Name'], None, row['Sub Name'], "192.168.1." + str(i+1), "Relay" + str(i+1), "VLAN1", "Relay" + str(i+1))
                sub.add_node(relay)
                sub.add_link(relay.id, relay_controller.id, "Ethernet", 100, 10, "DNP3")

            # Create other nodes (Switch1, Switch2, Router, Desktop, Firewall)
            switch1 = Switch("MAC_Table1", "Region1", None, row['Sub Name'], "192.168.2.1", "Switch01", "VLAN1", "Switch1")
            switch2 = Switch("MAC_Table2", "Region1", None, row['Sub Name'], "192.168.2.2", "Switch02", "VLAN1", "Switch2")
            router = Router({}, {}, "Region1", None, row['Sub Name'], "192.168.3.1", "Router01", "VLAN1", "Router1")
            desktop = CyberNode("Protocol", "Region1", None, row['Sub Name'], "192.168.4.1", "Desktop01", "VLAN1", "Desktop1")
            firewall = Firewall("ACL", sub.latitude, sub.longitude, "Region1", None, row['Sub Name'], "192.168.5.1", "Firewall01", "VLAN1", "Firewall1")
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

    def cluster_substations(self, substations, n_clusters=2):
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

# Other class definitions remain the same

def generate_system_from_csv(csv_file):
    cps = CyberPhysicalSystem()
    substations = cps.load_substations_from_csv(csv_file)
    utilities = cps.cluster_substations(substations)
    regulatory = Regulatory(region="Region1", utilities=utilities, regulatory_id="Reg1")
    output_to_json_file(regulatory)


# Example usage
generate_system_from_csv("Substation_14bus.csv")

# substation = Substation("Region1", "UtilityA", "SubstationX", "Sub1")
#
# substations = [substation]#[Substation("Region1", "UtilityA", "SubstationX", "Sub1")]
# utilities = [Utility("Region1", "UtilityA", substations, "Util1")]
# regulatory = Regulatory("Region1", utilities, "Reg1")
#
# # Example usage
# #substation = Substation("Region1", "UtilityA", "SubstationX", "Sub1")
#
# # Example of adding nodes and links to a substation
# relay = Relay("Bus1", "Type1", "Region1", "UtilityA", "SubstationX", "192.168.1.1", "Relay01", "VLAN1", "Relay1")
# relay_controller = RelayController("Sub1", ["192.168.1.1"], "Region1", "UtilityA", "SubstationX", "192.168.1.2", "Controller01", "VLAN1", "Controller1")
# switch = Switch("MAC_Table", "Region1", "UtilityA", "SubstationX", "192.168.1.3", "Switch01", "VLAN1", "Switch1")
# router = Router({}, {}, "Region1", "UtilityA", "SubstationX", "192.168.1.4", "Router01", "VLAN1", "Router1")
# firewall = Firewall("ACL", "0.0", "0.0", "Region1", "UtilityA", "SubstationX", "192.168.1.5", "Firewall01", "VLAN1", "Firewall1")
# desktop = CyberNode("Protocol", "Region1", "UtilityA", "SubstationX", "192.168.1.6", "Desktop01", "VLAN1", "Desktop1")
#
# substation.add_node(relay)
# substation.add_node(relay_controller)
# substation.add_node(switch)
# substation.add_node(router)
# substation.add_node(firewall)
# substation.add_node(desktop)
#
# # Example of adding links between nodes
# substation.add_link(relay.id, relay_controller.id, "Ethernet", 100, 10, "DNP3")
# substation.add_link(relay_controller.id, switch.id, "Ethernet", 100, 10, "DNP3")
# substation.add_link(switch.id, router.id, "Ethernet", 100, 10, "IP")
# substation.add_link(router.id, firewall.id, "Ethernet", 100, 10, "IP")
# substation.add_link(switch.id, desktop.id, "Ethernet", 100, 10, "IP")
# substation.add_link(firewall.id, "UtilityA", "Ethernet", 100, 10, "IP") # Assuming UtilityA is an external node ID
# #print(output_regulatory_json(regulatory))
# output_to_json_file(regulatory)
