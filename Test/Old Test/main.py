import json
import numpy as np
import os
import pandas as pd
from sklearn.cluster import KMeans

class Node:
    def __init__(self, region, utility, substation, adminIP, label, vlan):
        self.region = region  # ISO or balancing authority
        self.utility = utility  # Utility provider
        self.substation = substation  # Operating substation
        self.adminIP = adminIP  # Administrator IP address
        self.label = label  # Device label
        self.vlan = vlan  # VLAN for the device

# Other subclasses (Firewall, Switch, etc.) remain the same
class Router(Node):
    def __init__(self, region, utility, substation, adminIP, label, vlan, interface, routing_table):
        super().__init__(region, utility, substation, adminIP, label, vlan)
        self.interface = interface  # Dictionary of interfaces and their assigned IP addresses
        self.routing_table = routing_table  # List or dictionary representing the routing table

    def add_interface(self, interface_name, ip_address):
        self.interface[interface_name] = ip_address

    def add_route(self, destination, next_hop):
        self.routing_table[destination] = next_hop

# Example usage
router = Router(
    region="Region2",
    utility="UtilityB",
    substation="SubstationY",
    adminIP="192.168.2.1",
    label="Router01",
    vlan="VLAN200",
    interface={},
    routing_table={}
)

# Adding interface and route to the router
router.add_interface("eth0", "192.168.2.2")
router.add_route("192.168.3.0/24", "192.168.2.2")

class CyberPhysicalSystem:
    def __init__(self):
        a=1# ... (other initializations)

    def generate_network_model(self, substation_csvpath):
        """
        Generates the network model based on a list of substations and writes the data to JSON files.
        """

        substation_list = self.substation_info_to_list(substation_csvpath)
        # Step 1-8: Process each substation
        for sub in substation_list:
            # Create instance of substation
            substation = self.create_substation_instance(sub)
            # Write substation data to JSON file
            self.write_to_json(f'substation_{sub["Sub Num"]}.json', substation)

        # Step 9: Group substations into utilities using k-means clustering
        utility_list = self.cluster_substations(substation_list, n_clusters=7)

        # Step 12-17: Process each utility
        for utility_area, subs in enumerate(utility_list):
            utility = self.create_utility_instance(subs, utility_area)
            self.write_to_json(f'utility_{utility_area}.json', utility)

        # Step 19-23: Create instance of regulatory authority and write to JSON
        regulatory = self.create_regulatory_instance(utility_list)
        self.write_to_json('regulatory.json', regulatory)

    def substation_info_to_list(self, substation_csvpath):
        # Write code to read substation data from csv and convert it into substation_list
        substation_list = []
        sub_df = pd.read_csv(substation_csvpath,skiprows=1)
        sub_df = sub_df[['Sub Num','Latitude','Longitude']]
        substation_list = sub_df.to_dict(orient='records')

        return substation_list


    def create_substation_instance(self, sub):
        # Create instance with nodes and links (dummy implementation)
        return {
            "id": sub["Sub Num"],
            "nodes": [],
            "links": []
        }

    def write_to_json(self, filename, data):
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)

    def cluster_substations(self, substation_list, n_clusters):
        # Extract latitudes and longitudes
        locations = [(sub["Latitude"], sub["Longitude"]) for sub in substation_list]
        kmeans = KMeans(n_clusters=n_clusters)
        kmeans.fit(locations)

        # Group substations by cluster
        utility_list = [[] for _ in range(n_clusters)]
        for sub, label in zip(substation_list, kmeans.labels_):
            utility_list[label].append(sub)
        return utility_list

    def create_utility_instance(self, subs, utility_area):
        # Create utility instance with nodes and links
        return {
            "area": utility_area,
            "substations": subs
        }

    def create_regulatory_instance(self, utility_list):
        # Create regulatory instance with nodes and links
        return {
            "utilities": utility_list
        }

# Example Usage
if __name__ == "__main__":
    cps = CyberPhysicalSystem()
    substation_csvpath = os.path.join(os.getcwd(),'Substation_14bus.csv')
    cps.generate_network_model(substation_csvpath)
