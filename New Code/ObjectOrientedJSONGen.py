import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from scipy.spatial import cKDTree
import json
import os
import configparser

config = configparser.ConfigParser()
config.read('settings.ini')

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
        #self.protocol = protocol
class Host(Node):
    #this class of node is used for ICCPServer (Reg), EMS (Utilities)
    #and ofcourse for hosts anywhere (Reg, Uils, Subtations)
    def __init__(self, openPorts, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.openPorts = openPorts
        #self.protocol = protocol
class Relay(Node):
    def __init__(self, busNumber, breakers, relayType, relaysubtype, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.breakers = breakers
        self.busNumber = busNumber
        self.relayType = relayType
        self.relaySubType = relaysubtype

#added RTU
class RTU(Node):
    def __init__(self, substationNumber, breakerList, protocol, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.substationNumber = substationNumber
        self.breakerList = breakerList
        self.protocol = protocol

class Link:
    def __init__(self, source, destination, link_type, bandwidth, distance):
        self.source = source
        self.destination = destination
        self.link_type = link_type
        self.bandwidth = bandwidth
        self.distance = distance
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

    def add_link(self, source_id, destination_id, link_type, bandwidth, distance):
        link = Link(source=source_id, destination=destination_id, link_type=link_type, bandwidth=bandwidth, distance=distance)
        self.links.append(link)

    def add_switch(self, switch):
        self.switches.append(switch)

    def add_rcs(self, rc):
        self.rcs.append(rc)

    def add_subFirewall(self, subFirewall):
        self.substationFirewall.append(subFirewall)

    def add_subRouter(self, subRouter):
        self.substationRouter.append(subRouter)

    def add_subSwitch(self, subSwitch):
        self.substationSwitch.append(subSwitch)

    def add_subRC(self, subRC):
        self.substationrelayController.append(subRC)

class GenSubstation(Substation):
    def __init__(self, genmw, genmvar, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.genmw = genmw
        self.genmvar = genmvar

class Utility:
    def __init__(self, networkLan, utl_id, utility_name, substations, subFirewalls, latitude, longitude):
        self.networkLan = networkLan
        self.subnetMask = "255.255.255.0"
        self.label = utility_name
        self.utility = utility_name
        self.substations = substations
        self.useableHost = [f"10.{utl_id}.0.{i}" for i in range(1, 254)]
        self.substationFirewalls = subFirewalls #this should have a list of substation firewalls inside the utility
        self.latitude = latitude
        self.longitude = longitude
        self.nodes = []
        self.links = []
        self.utilityFirewall = []
        self.utilityRouter = []
        self.utilitySwitch = []
        self.utilityEMS = []
        self.substationsRouter = []
        self.substationsFirewall = []
        self.DMZFirewall = []
        self.linkUtlFirewalltoUtlRouter = []
        self.linkUtlRoutertoEMS = []
        self.linkSubEMStoSubsRouter = []
        self.linkSubsRoutertoSubsFirewall = []
        self.compromised = False

    def add_node(self, node):
        self.nodes.append(node)
    def add_utilityFirewall(self, utilFirewall):
        self.utilityFirewall.append(utilFirewall)
    def add_utilityRouter(self, utilRouter):
        self.utilityRouter.append(utilRouter)
    def add_utilitySwitch(self, utilSwitch):
        self.utilitySwitch.append(utilSwitch)
    def add_utilityEMS(self, utilEMS):
        self.utilityEMS.append(utilEMS)
    def add_substationsRouter(self, substationsRouter):
        self.substationsRouter.append(substationsRouter)
    def add_substationsFirewall(self, substationsFirewall):
        self.substationsFirewall.append(substationsFirewall)
    def add_DMZFirewall(self, DMZFirewall):
        self.DMZFirewall.append(DMZFirewall)

    def add_link(self, source_id, destination_id, link_type, bandwidth, distance):
        link = Link(source=source_id, destination=destination_id, link_type=link_type, bandwidth=bandwidth, distance=distance)
        self.links.append(link)
    def add_linkUtlFirewalltoUtlRouter(self, source_id, destination_id, link_type, bandwidth, distance):
        link = Link(source=source_id, destination=destination_id, link_type=link_type, bandwidth=bandwidth, distance=distance)
        self.linkUtlFirewalltoUtlRouter.append(link)
    def add_linkUtlRoutertoEMS(self, source_id, destination_id, link_type, bandwidth, distance):
        link = Link(source=source_id, destination=destination_id, link_type=link_type, bandwidth=bandwidth, distance=distance)
        self.linkUtlRoutertoEMS.append(link)
    def add_linkSubEMStoSubsRouter(self, source_id, destination_id, link_type, bandwidth, distance):
        link = Link(source=source_id, destination=destination_id, link_type=link_type, bandwidth=bandwidth, distance=distance)
        self.linkSubEMStoSubsRouter.append(link)
    def add_linkSubsRoutertoSubsFirewall(self, source_id, destination_id, link_type, bandwidth, distance):
        link = Link(source=source_id, destination=destination_id, link_type=link_type, bandwidth=bandwidth, distance=distance)
        self.linkSubsRoutertoSubsFirewall.append(link)

class Regulatory:
    def __init__(self, label, networklan, utils, utilFirewalls, latitude, longitude):
        self.label = label
        self.networkLan = networklan
        self.subnetMask = "255.255.255.0"
        self.utilities = utils
        self.latitude = latitude
        self.longitude = longitude
        self.useableHost = [f"172.30.0.{i}" for i in range(1, 254)]
        self.utilityFirewalls = utilFirewalls
        self.iccpServer = []
        self.regulatoryRouter = []
        self.regulatoryFirewall = []
        self.nodes = []
        self.links = []
        self.compromised = False

    def add_node(self, node):
        self.nodes.append(node)

    def add_link(self, source_id, destination_id, link_type, bandwidth, distance):
        link = Link(source=source_id, destination=destination_id, link_type=link_type, bandwidth=bandwidth, distance=distance)
        self.links.append(link)

    def add_iccpserver(self, server):
        self.iccpServer.append(server)

    def add_regRouter(self, router):
        self.regulatoryRouter.append(router)

    def add_regFirewall(self, firewall):
        self.regulatoryFirewall.append(firewall)


class CyberPhysicalSystem:
    def load_substations_from_csv(self, csv_file):
        df = pd.read_csv(csv_file, skiprows=1)
        df["Gen MW"].fillna(99999, inplace=True)
        # Selecting the columns for clustering
        X = df[['Latitude', 'Longitude']]
        # Number of clusters - This can be adjusted based on specific needs
        n_clusters = int(config['DEFAULT']['n_clusters'])
        # Performing K-Means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=0).fit(X)
        # Extracting the centroids
        centroids = kmeans.cluster_centers_

        # Adding the cluster labels (utility names) to the original DataFrame
        df['Utility Name'] = 'Utility ' + pd.Series(kmeans.labels_).astype(str)
        unique_values = df['Utility Name'].unique()
        utility_centroids = {name: centroids[int(name.split(' ')[1])] for name in unique_values}
        # Create a dictionary with keys as the unique values and values as a sequence starting from 52
        starting_utl_number = 52
        unique_dict = {
            name: {
                'id': starting_utl_number + i,
                'latitude': utility_centroids[name][0],
                'longitude': utility_centroids[name][1]
            }
            for i, name in enumerate(unique_values)
        }

        substations = []
        relay_num=100
        for _, row in df.iterrows():
            # Constructing the base part of the ID
            sub_label = f"Region.{row['Utility Name']}.{row['Sub Name']}"
            utl_ID = unique_dict.get(row["Utility Name"]).get('id')
            
            if row["Gen MW"] == 99999:
                sub = Substation(
                    relaynum=row['# of Buses'],
                    label=sub_label,
                    networklan=f"10.{utl_ID}.{row['Sub Num']}.0",
                    utility=row["Utility Name"],
                    substation_name=row["Sub Name"],
                    substation_num=row["Sub Num"],
                    latitude=row['Latitude'],
                    longitude=row['Longitude'],
                    utl_id=utl_ID)

            else:
                sub = GenSubstation(
                    relaynum=row['# of Buses'],
                    label=sub_label,
                    networklan=f"10.{utl_ID}.{row['Sub Num']}.0",
                    utility=row["Utility Name"],
                    substation_name=row["Sub Name"],
                    substation_num=row["Sub Num"],
                    latitude=row['Latitude'],
                    longitude=row['Longitude'],
                    utl_id=utl_ID,
                    genmw=row["Gen MW"],
                    genmvar=row["Gen Mvar"])
            
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
            starting_relay_id = 3
            relayiplist = []
            for i in range(int(row['# of Buses'])):
                ip = f"10.{utl_ID}.{row['Sub Num']}.{starting_relay_id}"
                relayiplist.append(ip)
                relay = Relay("", [], 'Line', 'OC',
                              utility=row['Utility Name'], substation=row['Sub Name'],
                              adminIP=ip,
                              ipaddress=f"10.{utl_ID}.{row['Sub Num']}.0",
                              vlan='OT',
                              label=f"{row['Utility Name']}.{row['Sub Name']}..Relay {relay_num+1}")
                sub.add_node(relay)
                # RC --> relays
                sub.add_link(RC.label, relay.label, "Ethernet", 10.0, 10.0)
                starting_relay_id=starting_relay_id+1

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
            # router --> firewall
            sub.add_link(router.label, firewall.label, "Ethernet", 10.0, 10.0)
            # firewall --> switch.OT
            sub.add_link(firewall.label, switch.label, "Ethernet", 10.0, 10.0)
            # switch.OT --> RC
            sub.add_link(switch.label, RC.label, "Ethernet", 10.0, 10.0)
            # firewall --> switch.Corp
            sub.add_link(firewall.label, corp_switch.label, "Ethernet", 10.0, 10.0)
            # switch.Corp --> host1
            sub.add_link(corp_switch.label, host1.label, "Ethernet", 10.0, 10.0)
            # switch.Corp --> host2
            sub.add_link(corp_switch.label, host2.label, "Ethernet", 10.0, 10.0)

            substations.append(sub)
            name_json = f"Region.{row['Utility Name']}.{row['Sub Name']}.json"
            output_to_json_file(sub, filename=os.path.join(cwd,"Output/Substations",name_json))
        return substations, unique_dict
    def generate_utilties(self, substations, utility_dict, topology):
        firewall_start = len(substations)+1
        router_start = len(substations)+1
        ems_start = 2501
        utilities = []
        for key, val in utility_dict.items():
            # Constructing the base part of the ID
            util_label = f"Region.{key}"
            print(key)
            utl_ID = val.get('id')

            util = Utility(
                networkLan=f"10.{utl_ID}.0.0",
                utl_id=utl_ID,
                utility_name=key,
                substations=[substation for substation in substations if substation.utility == key],
                subFirewalls=[substation.substationFirewall for substation in substations if substation.utility == key],
                latitude=val.get('latitude'),
                longitude=val.get('longitude')
            )
            utilFirewall=Firewall([], [], val.get('latitude'), val.get('longitude'),
                                utility=key, substation="",
                                adminIP=f"10.{utl_ID}.0.1",
                                ipaddress=f"10.{utl_ID}.0.0",
                                label=f"{key}.{key}..Firewall {firewall_start}",
                                vlan='1')
            utilRouter=Router([], [], utility=key, substation="",
                                adminIP=f"10.{utl_ID}.0.2",
                                ipaddress=f"10.{utl_ID}.0.0",
                                label=f"{key}.{key}..Router {router_start}",
                                vlan='1')
            utilSwitch=Switch([], utility=key, substation="",
                                adminIP=f"10.{utl_ID}.0.8",
                                ipaddress=f"10.{utl_ID}.0.0",
                                label=f"{key}.{key}..Switch {ems_start}",
                                vlan='OT')
            utilEMS=Host([], utility=key, substation="utl",
                                adminIP=f"10.{utl_ID}.0.3",
                                ipaddress=f"10.{utl_ID}.0.0",
                                label=f"{key}.utl..Host {ems_start}",
                                vlan='1')
            router_start = router_start + 1
            substationsRouter=Router([], [], utility=key, substation="",
                                adminIP=f"10.{utl_ID}.0.4",
                                ipaddress=f"10.{utl_ID}.0.0",
                                label=f"{key}.{key}..Router {router_start}",
                                vlan='1')
            firewall_start = firewall_start+1
            substationsFirewall=Firewall([], [], val.get('latitude'), val.get('longitude'),
                                utility=key, substation="",
                                adminIP=f"10.{utl_ID}.0.5",
                                ipaddress=f"10.{utl_ID}.0.0",
                                label=f"{key}.{key}..Firewall {firewall_start}",
                                vlan='1')
            firewall_start = firewall_start + 1
            DMZFirewall=Firewall([], [], val.get('latitude'), val.get('longitude'),
                                utility=key, substation="",
                                adminIP=f"10.{utl_ID}.0.7",
                                ipaddress=f"10.{utl_ID}.0.0",
                                label=f"{key}.{key}..Firewall {firewall_start}",
                                vlan='1')
            firewall_start = firewall_start + 1
            router_start = router_start + 1

            util.add_node(utilFirewall)
            util.add_node(utilRouter)
            util.add_node(utilEMS)
            util.add_node(substationsFirewall)
            util.add_node(substationsRouter)
            for s in substations:
                util.add_node(s)
            util.add_node(DMZFirewall)

            # Add the non-node objects to the Utility
            util.add_utilityFirewall(utilFirewall)
            util.add_utilityRouter(utilRouter)
            util.add_utilitySwitch(utilSwitch)
            util.add_utilityEMS(utilEMS)
            util.add_substationsRouter(substationsRouter)
            util.add_substationsFirewall(substationsFirewall)
            util.add_DMZFirewall(DMZFirewall)

            # router --> firewall
            util.add_link(utilRouter.label, utilFirewall.label, "Ethernet", 10.0, 10.0)
            # utility_firewall --> EMSswitch
            util.add_link(utilFirewall.label, utilSwitch.label, "Ethernet", 10.0, 10.0)
            # EMSswitch --> EMS
            util.add_link(utilSwitch.label, utilEMS.label, "Ethernet", 10.0, 10.0)

            # EMSSwitch --> substationrouter
            util.add_link(utilSwitch.label, substationsFirewall.label, "Ethernet", 10.0, 10.0)
            # substationrouter --> substationFirewall
            util.add_link(substationsFirewall.label, substationsRouter.label, "Ethernet", 10.0, 10.0)
            # substationsRouter --> individual substation routers
            
            if "star" in topology:
                print("star")

                for s in substations:
                    util.add_link(substationsRouter.label, s.substationRouter[0].label, "Ethernet", 10.0, 10.0)
            if "radial" in topology:
                print("radial")
                for s in substations:
                    if row["Gen MW"] != 99999:
                        #For SubNum, grab the substation number from SubNum 1
                        #connectingSub = row["SubNum 1"] #in second CSV file
                        #create connections between those 
                        #util.add_link(substationsRouter.label, s.substationRouter[0].label, "Ethernet", 10.0, 10.0)
                        #look into other excel
                        #in SubNum, look at Substation # in SubNum 1
                        #connect SubNum to SubNum 1
                        util.add_link(substationsRouter.label, s.substationRouter[0].label, "Ethernet", 10.0, 10.0)
                    else:
                        util.add_link(substationsRouter.label, s.substationRouter[0].label, "Ethernet", 10.0, 10.0)

            # utilityRouter --> DMZFirewall
            util.add_link(utilRouter.label, DMZFirewall.label, "Ethernet", 10.0, 10.0)

            utilities.append(util)
            name_json = f"Region.{key}.json"
            output_to_json_file(util, filename=os.path.join(cwd, "Output/Utilities", name_json))
        return utilities

    def generate_BA(self, substations, utilities):
        regulatory = []


        reg = Regulatory(
            label="Regulatory",
            networklan= "172.30.0.0",
            utils=utilities,
            utilFirewalls=[ut.utilityFirewall for ut in utilities],
            latitude=utilities[0].latitude,
            longitude=utilities[0].longitude
        )

        regFirewall = Firewall([], [], reg.latitude, reg.longitude,
                                utility="balancing_authority", substation="ba",
                                adminIP=f"172.30.0.2",
                                ipaddress=f"172.30.0.0",
                                label=f"balancing_authority.ba..Firewall 1701",
                                vlan='1')
        regRouter = Router([], [],
                                utility="balancing_authority", substation="ba",
                                adminIP=f"172.30.0.3",
                                ipaddress=f"172.30.0.0",
                                label=f"balancing_authority.ba..Router 1551",
                                vlan='1')
        iccpserver = Host([],
                                utility="balancing_authority", substation="ba",
                                adminIP=f"172.30.0.1",
                                ipaddress=f"172.30.0.0",
                                label=f"balancing_authority.ba..Host 2801",
                                vlan='1')

        # Add node objects
        reg.add_node(regFirewall)
        reg.add_node(regRouter)
        reg.add_node(iccpserver)
        for u in utilities:
            reg.add_node(u.utilityFirewall[0])

        # Add the non-node objects to the Utility
        reg.add_regRouter(regRouter)
        reg.add_regFirewall(regFirewall)
        reg.add_iccpserver(iccpserver)

        # Add links
        reg.add_link(iccpserver.label, regFirewall.label, "Ethernet", 10.0, 10.0)
        reg.add_link(regFirewall.label, regRouter.label, "Ethernet", 10.0, 10.0)
        for u in utilities:
            reg.add_link(regRouter.label, u.utilityRouter[0].label, "fiber", 10.0, 100.0)

        regulatory.append(reg)
        name_json = "Regulatory.json"
        output_to_json_file(reg, filename=os.path.join(cwd, "Output/Regulatory", name_json))

        return regulatory

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
    topology = config['DEFAULT']['topology_configuration']
    print(topology)
    substations, utility_dict = cps.load_substations_from_csv(csv_file)
    utilities = cps.generate_utilties(substations, utility_dict, topology)
    regulatory = cps.generate_BA(substations, utilities)


generate_system_from_csv("Substation_500bus.csv")

