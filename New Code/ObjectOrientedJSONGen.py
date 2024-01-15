import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
import json
import os

cwd = os.getcwd()

class Node:
    def __init__(self, utility, substation, adminIP, ipaddress, label, vlan):
        self.utility = utility
        self.adminIP = adminIP
        self.ipAddress = ipaddress
        if vlan == 'Corporate':
            self.subnetMask = '255.255.255.224'
        elif vlan == 'OT':
            self.subnetMask = '255.255.255.192'
        self.vlan = vlan
        self.substation = substation
        self.label = label
        self.compromised = False
class Firewall(Node):
    def __init__(self, acls, interfaces, Latitude, Longitude, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.acls = acls
        self.interfaces = interfaces
        self.Latitude = Latitude
        self.Longitude = Longitude
class Router(Node):
    def __init__(self, interfaces, routingTable, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.interfaces = interfaces
        self.routingTable = routingTable
class Switch(Node):
    def __init__(self, arpTable, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.arpTable = arpTable
class RelayController(Node):
    def __init__(self, relayIPlist, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.relayIPlist = relayIPlist
class Host(Node):
    def __init__(self, openPorts, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.openPorts = openPorts
class Relay(Node):
    def __init__(self, busNumber, breakers, relayType, relaysubtype, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.breakers = breakers
        self.busNumber = busNumber
        self.relayType = relayType
        self.relaySubType = relaysubtype
class Link:
    def __init__(self, source, destination, link_type, bandwidth, distance, protocol):
        self.source = source
        self.destination = destination
        self.link_type = link_type
        self.bandwidth = bandwidth
        self.distance = distance
        self.protocol = protocol
        self.compromised = False

class Substation:
    def __init__(self, relaynum, label, networklan, utility, substation_name, substation_num, latitude, longitude, utl_id):
        self.relayCounter = relaynum
        self.label = label
        self.networkLan = networklan
        self.supernetMask = "255.255.255.128"
        self.utility = utility
        self.substation = substation_name
        self.substationNumber = substation_num
        self.OTAddress = networklan
        self.OTSubnetMask = "255.255.255.192"
        self.OTHosts = [f"10.{utl_id}.{substation_num}.{i}" for i in range(1, 63)]
        self.routeAddress = networklan[:-1] + "64"
        self.routeSubnetMask ="255.255.255.224"
        self.routingHosts = [f"10.{utl_id}.{substation_num}.{i}" for i in range(65, 95)]
        self.corporateAddress = networklan[:-1] + "96"
        self.corporateSubnetMask = "255.255.255.224"
        self.corporateHosts = [f"10.{utl_id}.{substation_num}.{i}" for i in range(97, 126)]
        self.latitude = latitude
        self.longitude = longitude
        self.nodes = []
        self.links = []
        self.switches = []
        self.rcs = []
        self.substationFirewall = []
        self.substationRouter = []
        self.substationSwitch = []
        self.substationrelayController = []
        self.compromised = False

    def add_node(self, node):
        self.nodes.append(node)

    def add_link(self, source_id, destination_id, link_type, bandwidth, distance, protocol):
        link = Link(source=source_id, destination=destination_id, link_type=link_type, bandwidth=bandwidth, distance=distance, protocol=protocol)
        self.links.append(link)

    def add_switch(self, switch):
        #switch = Switch(arpTable=arptab)
        self.switches.append(switch)

    def add_rcs(self, rc):
        #rc = RelayController(relayIPlist=relayIP)
        self.rcs.append(rc)

    def add_subFirewall(self, subFirewall):
        #subFirewall = Firewall(acllist,interfacelist,self.latitude,self.longitude)
        self.substationFirewall.append(subFirewall)

    def add_subRouter(self, subRouter):
        #subRouter = Router(interfacelist,routinglist)
        self.substationRouter.append(subRouter)

    def add_subSwitch(self, subSwitch):
        #subSwitch = Switch(self,arptab)
        self.substationSwitch.append(subSwitch)

    def add_subRC(self, subRC):
        #subRC = RelayController(relayIP)
        self.substationrelayController.append(subRC)

# class Utility:
#     def __init__(self, networkLan, subnetMask, utility_id, utility_name, substations, latitude, longitude):
#         #self.region = region
#         #self.utility = utility
#         self.networkLan = networkLan
#         self.subnetMask = subnetMask
#         self.label = utility_id
#         self.utility = utility_name
#         self.substations = substations
#         self.useableHost = []
#         self.substationFirewalls = substationFirewalls
#         self.latitude = latitude
#         self.longitude = longitude
#         self.nodes = []
#         self.links = []
#         self.utilityFirewall = utilFirewall
#         self.utilityRouter = utilRouter
#         self.utilitySwitch = utilswitch
#         self.utilityEMS = utilEMS
#         self.substationsRouter = subsRouter
#         self.substationsFirewall = subsFirewall
#         self.DMZFirewall = DMZfirewall
#         self.linkUtlFirewalltoUtlRouter = linkUtlFirewalltoUtlRouter
#         self.linkUtlRoutertoEMS = linkUtlRoutertoEMS
#         self.linkSubEMStoSubsRouter = linkSubEMStoSubsRouter
#         self.linkSubsRoutertoSubsFirewall = linkSubsRoutertoSubsFirewall
#         self.compromised = False
#
#
#         # Initialize utility components
#         self.initialize_components()
#
#     def initialize_components(self):
#         base_id = f"{self.region}.{self.utility}.{self.utility_id}.VLAN1."
#
#         # Create utility components
#         self.firewall1 = Firewall("ACL1", self.latitude, self.longitude, self.region, self.utility, self.utility_id, "192.168.100.1", "Firewall01", "VLAN1", base_id + "Firewall1")
#         self.router1 = Router({}, {}, self.region, self.utility, self.utility_id, "192.168.100.2", "Router01", "VLAN1", base_id + "Router1")
#         self.switch = Switch("MAC_Table", self.region, self.utility, self.utility_id, "192.168.100.3", "Switch01", "VLAN1", base_id + "Switch")
#         self.ems = CyberNode("EMS_Protocol", self.region, self.utility, self.utility_id, "192.168.100.4", "EMS01", "VLAN1", base_id + "EMS")
#         self.router2 = Router({}, {}, self.region, self.utility, self.utility_id, "192.168.100.5", "Router02", "VLAN1", base_id + "Router2")
#         self.firewall2 = Firewall("ACL2", self.latitude, self.longitude, self.region, self.utility, self.utility_id, "192.168.100.6", "Firewall02", "VLAN1", base_id + "Firewall2")
#         self.dmz = CyberNode("DMZ_Protocol", self.region, self.utility, self.utility_id, "192.168.100.7", "DMZ01", "VLAN1", base_id + "DMZ")
#
#         # Add nodes to utility
#         self.nodes.extend([self.firewall1, self.router1, self.switch, self.ems, self.router2, self.firewall2, self.dmz])
#
#         # Create links between nodes
#         self.add_link(self.firewall1.id, self.router1.id, "Ethernet", 1000, 10, "IP")
#         self.add_link(self.router1.id, self.switch.id, "Ethernet", 1000, 10, "IP")
#         self.add_link(self.ems.id, self.switch.id, "Ethernet", 1000, 10, "IP")
#         self.add_link(self.switch.id, self.router2.id, "Ethernet", 1000, 10, "IP")
#         self.add_link(self.router2.id, self.firewall2.id, "Ethernet", 1000, 10, "IP")
#         self.add_link(self.firewall2.id, self.dmz.id, "Ethernet", 1000, 10, "IP")
#
#     def add_link(self, source_id, destination_id, link_type, bandwidth, distance, protocol):
#         link = Link(source=source_id, destination=destination_id, link_type=link_type, bandwidth=bandwidth, distance=distance, protocol=protocol)
#         self.links.append(link)
#
# class Regulatory:
#     def __init__(self, region, utilities):
#         self.region = region
#         self.utilities = utilities
#         self.regulatory_id = "{}".format(region)
#         self.firewall = Firewall("ACL", "0.0", "0.0", region, None, self.regulatory_id, "192.168.100.1", "RegFirewall", "VLAN1", "RegFirewall1")
#         self.router = Router({}, {}, region, None, self.regulatory_id, "192.168.100.2", "RegRouter", "VLAN1", "RegRouter1")
#         self.iccp_server = CyberNode("ICCP", region, None, self.regulatory_id, "192.168.100.3", "ICCP_Server", "VLAN1", "ICCP1")
#         self.links = [
#             Link(self.iccp_server.id, self.router.id, "Ethernet", 1000, 10, "ICCP"),
#             Link(self.router.id, self.firewall.id, "Ethernet", 1000, 10, "IP")
#         ]
#
#     def add_utility_links(self):
#         for utility in self.utilities:
#             for substation in utility.substations:
#                 for node in substation.nodes:
#                     if isinstance(node, Firewall):
#                         self.links.append(Link(self.firewall.id, node.id, "Ethernet", 1000, 10, "IP"))
#


class CyberPhysicalSystem:
    def load_substations_from_csv(self, csv_file):
        df = pd.read_csv(csv_file, skiprows=1)
        # Selecting the columns for clustering
        X = df[['Latitude', 'Longitude']]
        # Number of clusters - This can be adjusted based on specific needs
        n_clusters = 2
        # Performing K-Means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=0).fit(X)

        # Adding the cluster labels (utility names) to the original DataFrame
        df['Utility Name'] = 'Utility ' + pd.Series(kmeans.labels_).astype(str)
        unique_values = df['Utility Name'].unique()
        # Create a dictionary with keys as the unique values and values as a sequence starting from 52
        starting_utl_number = 52
        unique_dict = {value: starting_utl_number + i for i, value in enumerate(unique_values)}

        #setting starting number for switches and hosts
        starting_switch_num = 59
        starting_host_num = 60

        substations = []
        relay_num=100
        for _, row in df.iterrows():
            # Constructing the base part of the ID
            sub_label = f"Region.{row['Utility Name']}.{row['Sub Name']}"
            utl_ID = unique_dict.get(row["Utility Name"])

            # Create substation instance
            sub = Substation(
                relaynum=row['# of Buses'],
                label=sub_label,
                networklan=f"10.{utl_ID}.{row['Sub Name']}.0",
                utility=row["Utility Name"],
                substation_name=row["Sub Name"],
                substation_num=row["Sub Num"],
                latitude=row['Latitude'],
                longitude=row['Longitude'],
                utl_id=utl_ID
            )

            firewall = Firewall([], [], row['Latitude'], row['Longitude'],
                                utility=row["Utility Name"], substation=row["Sub Name"],
                                adminIP=f"10.{utl_ID}.{row['Sub Num']}.97",
                                ipaddress=f"10.{utl_ID}.{row['Sub Num']}.96",
                                label=f"{row['Utility Name']}.{row['Sub Name']}..Firewall {row['Sub Num']}",
                                vlan='Corporate')
            router = Router([], [], utility=row["Utility Name"], substation=row["Sub Name"],
                                adminIP=f"10.{utl_ID}.{row['Sub Num']}.98",
                                ipaddress=f"10.{utl_ID}.{row['Sub Num']}.96",
                                label=f"{row['Utility Name']}.{row['Sub Name']}..Router {row['Sub Num']}",
                                vlan='Corporate')
            switch=Switch([], utility=row["Utility Name"], substation=row["Sub Name"],
                                adminIP=f"10.{utl_ID}.{row['Sub Num']}.1",
                                ipaddress=f"10.{utl_ID}.{row['Sub Num']}.0",
                                label=f"{row['Utility Name']}.{row['Sub Name']}.OT.Switch {(2*int(row['Sub Num'])-1)}",
                                vlan='OT')
            corp_switch=Switch([], utility=row["Utility Name"], substation=row["Sub Name"],
                                adminIP=f"10.{utl_ID}.{row['Sub Num']}.99",
                                ipaddress=f"10.{utl_ID}.{row['Sub Num']}.96",
                                label=f"{row['Utility Name']}.{row['Sub Name']}.Corporate.Switch {(2*int(row['Sub Num']))}",
                                vlan='Corporate')
            host1 = Host([], utility=row["Utility Name"], substation=row["Sub Name"],
                                adminIP=f"10.{utl_ID}.{row['Sub Num']}.100",
                                ipaddress=f"10.{utl_ID}.{row['Sub Num']}.96",
                                label=f"{row['Utility Name']}.{row['Sub Name']}..Host {(2*int(row['Sub Num'])-1)}",
                                vlan='Corporate')
            host2 = Host([], utility=row["Utility Name"], substation=row["Sub Name"],
                                adminIP=f"10.{utl_ID}.{row['Sub Num']}.100",
                                ipaddress=f"10.{utl_ID}.{row['Sub Num']}.96",
                                label=f"{row['Utility Name']}.{row['Sub Name']}..Host {(2*int(row['Sub Num']))}",
                                vlan='Corporate')
            RC = RelayController([], utility=row["Utility Name"], substation=row["Sub Name"],
                                 adminIP=f"10.{utl_ID}.{row['Sub Num']}.2",
                                 ipaddress=f"10.{utl_ID}.{row['Sub Num']}.0",
                                 label=f"{row['Utility Name']}.{row['Sub Name']}..RC {row['Sub Num']}",
                                 vlan='OT')

            #Add above nodes to substation
            sub.add_node(firewall)
            sub.add_node(router)
            sub.add_node(switch)
            sub.add_node(corp_switch)
            sub.add_node(host1)
            sub.add_node(host2)
            # Create relay and relay controller nodes
            # Create relays
            starting_relay_id = 2
            relayiplist = []
            for i in range(int(row['# of Buses'])):
                ip = f"10.{utl_ID}.{row['Sub Num']}.{starting_relay_id+1}"
                relayiplist.append(ip)
                relay = Relay("", [], 'Line', 'OC',
                              utility=row['Utility Name'], substation=row['Sub Name'],
                              adminIP=ip,
                              ipaddress=f"10.{utl_ID}.{row['Sub Num']}.0",
                              vlan='OT',
                              label=f"{row['Utility Name']}.{row['Sub Name']}..Relay {relay_num+1}")
                sub.add_node(relay)
                # RC --> relays
                sub.add_link(RC.label, relay.label, "Ethernet", 10.0, 10.0, "DNP3")

            RC.relayIPlist = relayiplist
            sub.add_node(RC)

            #Add the non-nodes objects to the substations
            sub.add_switch(switch)
            sub.add_rcs(RC)
            sub.add_subFirewall(firewall)
            sub.add_subRouter(router)
            sub.add_subSwitch(switch)
            sub.add_subRC(RC)

            # Create links between nodes
            # firewall --> router
            sub.add_link(firewall.label, router.label, "Ethernet", 10.0, 10.0, "DNP3")
            # firewall --> switch.OT
            sub.add_link(firewall.label, switch.label, "Ethernet", 10.0, 10.0, "DNP3")
            # switch.OT --> RC
            sub.add_link(switch.label, RC.label, "Ethernet", 10.0, 10.0, "DNP3")
            # router --> switch.Corp
            sub.add_link(router.label, corp_switch.label, "Ethernet", 10.0, 10.0, "DNP3")
            # switch.corp --> host1
            sub.add_link(corp_switch.label, host1.label, "Ethernet", 10.0, 10.0, "DNP3")
            # switch.corp --> host2
            sub.add_link(corp_switch.label, host2.label, "Ethernet", 10.0, 10.0, "DNP3")
            # RC --> relay
            sub.add_link(corp_switch.label, host1.label, "Ethernet", 10.0, 10.0, "DNP3")

            substations.append(sub)
            name_json = f"Region.{row['Utility Name']}.{row['Sub Name']}.json"
            output_to_json_file(sub, filename=os.path.join(cwd,"Output",name_json))
        return substations

def to_json(obj):
    """Converts objects to a JSON-friendly format."""
    if isinstance(obj, Node) or isinstance(obj, Link) or isinstance(obj, Substation) or isinstance(obj, Utility) or isinstance(obj, Regulatory):
        return obj.__dict__
    elif isinstance(obj, list):
        return [to_json(item) for item in obj]
    else:
        return obj

def output_to_json_file(substation, filename):
    """Outputs the regulatory structure to a JSON file."""
    with open(filename, "w") as file:
        json.dump(substation, file, default=to_json, indent=4)

def generate_system_from_csv(csv_file):
    cps = CyberPhysicalSystem()
    substations = cps.load_substations_from_csv(csv_file)
    #utilities = cps.cluster_substations(substations)
    #regulatory = Regulatory(region="Region1", utilities=utilities)
    #regulatory.add_utility_links()  # Add links from regulatory firewall to utility firewalls



# Example usage
generate_system_from_csv("Substation_14bus.csv")

