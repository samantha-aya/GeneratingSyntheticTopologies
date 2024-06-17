import haversine
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
import json
import os
import configparser
from statistics_based import generate_nwk#import zeyu's function
from esa import SAW
from match import main

import logging

# Configure logging
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.basicConfig(filename='D:/Github/ECEN689Project/New Code/progress.log', filemode='w', level=logging.INFO)
#logging.basicConfig(filename='C:/ECEN689Project/New Code/progress.log', filemode='w', level=logging.INFO)
logger = logging.getLogger()

config = configparser.ConfigParser()
config.read('settings.ini')
topology = config['DEFAULT']['topology_configuration']

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
        self.acls = {}
        self.interfaces = interfaces
        self.Latitude = Latitude
        self.Longitude = Longitude

    def add_acl_rule(self, acl_name, description, source, destination, port, transportLayer, action):
        #this allows for an acl to be added
        #multiple acls can be added 
        rule = {
            "description": description,
            "source": source,
            "destination": destination,
            "port": port,
            "transportLayer": transportLayer,
            "action": action #allow or deny
        }
        if acl_name in self.acls:
            self.acls[acl_name].append(rule)
        else:
            self.acls[acl_name] = [rule]

##    def remove_acl_rule(self, acl_name, rule):
##        #remove specific acl
##        if acl_name in self.acls and rule in self.acls[acl_name]:
##            self.acls[acl_name].remove(rule)
##            if not self.acls[acl_name]:
##                del self.acls[acl_name]
class Router(Node):
    def __init__(self, interfaces, routingTable, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.interfaces = interfaces
        self.routingTable = {}
        
class Switch(Node):
    def __init__(self, arpTable, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.arpTable = arpTable
class RelayController(Node):
    def __init__(self, relayIPlist, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.relayIPlist = relayIPlist
        self.protocol = {}

    def set_protocol(self, protocolLabel, port, transportLayer):
        #this functions lets us set the protocol for the relay controller
        protocol = {
            "port": port,
            "transportLayer": transportLayer #tcp or udp
        }
        if protocolLabel in self.protocol:
            self.protocol[protocolLabel].append(protocol)
        else:
            self.protocol[protocolLabel] = [protocol]
        
class Host(Node):
    #this class of node is used for ICCPServer (Reg), EMS (Utilities)
    #and of course for hosts anywhere (Reg, Uils, Subtations)
    def __init__(self, openPorts, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.protocol = {}

    def set_protocol(self, protocolLabel, port, transportLayer):
        #this functions lets us set the protocol for the cyber node/host
        protocol = {
            "port": port,
            "transportLayer": transportLayer #tcp or udp
        }
        if protocolLabel in self.protocol:
            self.protocol[protocolLabel].append(protocol)
        else:
            self.protocol[protocolLabel] = [protocol]
        
class Relay(Node):
    def __init__(self, busNumber, breakers, relayType, relaysubtype, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.breakers = breakers
        self.busNumber = busNumber
        self.relayType = relayType
        self.relaySubType = relaysubtype
        self.protocol = {}


    def set_protocol(self, protocolLabel, port, transportLayer):
        #this functions lets us set the protocol for the relay
        protocol = {
            "port": port,
            "transportLayer": transportLayer #tcp or udp
        }
        if protocolLabel in self.protocol:
            self.protocol[protocolLabel].append(protocol)
        else:
            self.protocol[protocolLabel] = [protocol]
            
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
        self.utility_id = utl_id
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
        self.type= "transmission"

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
    def __init__(self, genmw, genmvar, connecting_TS_num, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.genmw = genmw
        self.genmvar = genmvar
        self.connecting_TS_num=connecting_TS_num
        self.type = "generation"
        
class Utility:
    def __init__(self, networkLan, utl_id, utility_name, substations, subFirewalls, latitude, longitude):
        self.networkLan = networkLan
        self.subnetMask = "255.255.255.0"
        self.label = utility_name
        self.utility = utility_name
        self.id = utl_id
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
        self.iccpserver=[]
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
    def add_iccpserver(self, iccpServer):
        self.iccpserver.append(iccpServer)
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
        self.iccpclient = []
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

    def add_iccpClient(self, server):
        self.iccpclient.append(server)

    def add_regRouter(self, router):
        self.regulatoryRouter.append(router)

    def add_regFirewall(self, firewall):
        self.regulatoryFirewall.append(firewall)

class CyberPhysicalSystem:
    def load_substations_from_csv(self, csv_file, substation_connections):
        df = pd.read_csv(csv_file, skiprows=1)

        #Replacing empty cells ('nan') with 9999, helps with reading the data since 'nan' doesn't work
        df.fillna(99999, inplace=True)

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
        print(unique_values)
        utility_centroids = {name: centroids[int(name.split(' ')[1])] for name in unique_values}
        # Create a dictionary with keys as the unique values and values as a sequence starting from 52
        starting_utl_number = 52
        unique_dict = {
            name: {
                'id': starting_utl_number + i,
                'latitude': utility_centroids[name][0],
                'longitude': utility_centroids[name][1],
                'num_of_subs': df.groupby('Utility Name').size()[name],
                'num_of_gens': get_num_of_gens(df, name)
            }
            for i, name in enumerate(unique_values)
        }

        substations = []
        relay_num=100
        for _, row in df.iterrows():
            TS_num = 99999
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
                # If the substation is a generation substation, we need to connect it to a transmission substation
                # from the pairs in substations_connections, find the pair that contains the current substation
                # then find the pair with minimum distance between them
                minimum_distance = 99999
                for pair in substation_connections:
                    if row['Sub Num'] in pair:
                        if minimum_distance > pair[2]:
                            minimum_distance = pair[2]
                            TS_num = pair[1] if row['Sub Num'] == pair[0] else pair[0]
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
                    genmvar=row["Gen Mvar"],
                    connecting_TS_num=TS_num)

            firewall = Firewall([], [], row['Latitude'], row['Longitude'],
                                utility=row["Utility Name"], substation=row["Sub Name"],
                                adminIP=f"10.{utl_ID}.{row['Sub Num']}.97",
                                ipaddress=f"10.{utl_ID}.{row['Sub Num']}.96", # 3 addresses, 67 (routing), 98 (corp), 2 (OT)
                                label=f"{row['Utility Name']}.{row['Sub Name']}..Firewall {row['Sub Num']}",
                                vlan='Corporate')
            router = Router([], [], utility=row["Utility Name"], substation=row["Sub Name"],
                                adminIP=f"10.{utl_ID}.{row['Sub Num']}.98",
                                ipaddress=f"10.{utl_ID}.{row['Sub Num']}.96", #change to 66 (routing subnet), and admin ip
                                label=f"{row['Utility Name']}.{row['Sub Name']}..Router {row['Sub Num']}",
                                vlan='Corporate')
            switch=Switch([], utility=row["Utility Name"], substation=row["Sub Name"],
                                adminIP=f"10.{utl_ID}.{row['Sub Num']}.1",
                                ipaddress=f"10.{utl_ID}.{row['Sub Num']}.0", #remove IP addresses, only admin ip
                                label=f"{row['Utility Name']}.{row['Sub Name']}.OT.Switch {(2*int(row['Sub Num'])-1)}",
                                vlan='OT')
            corp_switch=Switch([], utility=row["Utility Name"], substation=row["Sub Name"],
                                adminIP=f"10.{utl_ID}.{row['Sub Num']}.99",
                                ipaddress=f"10.{utl_ID}.{row['Sub Num']}.96", #remove IP addresses, only admin ip
                                label=f"{row['Utility Name']}.{row['Sub Name']}.Corporate.Switch {(2*int(row['Sub Num']))}",
                                vlan='Corporate')
            localDatabase = Host(openPorts=[16, 32], utility=row["Utility Name"], substation=row["Sub Name"],
                                adminIP=f"10.{utl_ID}.{row['Sub Num']}.100",
                                ipaddress=f"10.{utl_ID}.{row['Sub Num']}.96", #corp host IP: 99
                                label=f"{row['Utility Name']}.{row['Sub Name']}..LocalDatabase {(2*int(row['Sub Num'])-1)}",
                                vlan='Corporate')
            localWebServer = Host(openPorts=[16, 32], utility=row["Utility Name"], substation=row["Sub Name"],
                                adminIP=f"10.{utl_ID}.{row['Sub Num']}.100",
                                ipaddress=f"10.{utl_ID}.{row['Sub Num']}.96", #corp host IP: 100
                                label=f"{row['Utility Name']}.{row['Sub Name']}..LocalWebServer {(2*int(row['Sub Num']))}",
                                vlan='Corporate')
            hmi = Host([], utility=row["Utility Name"], substation=row["Sub Name"],
                                adminIP=f"10.{utl_ID}.{row['Sub Num']}.101",
                                ipaddress=f"10.{utl_ID}.{row['Sub Num']}.96", #corp host IP: 101
                                label=f"{row['Utility Name']}.{row['Sub Name']}..hmi {(2*int(row['Sub Num'])-1)}",
                                vlan='Corporate')
            host1 = Host(openPorts=[16, 32], utility=row["Utility Name"], substation=row["Sub Name"],
                                adminIP=f"10.{utl_ID}.{row['Sub Num']}.100",
                                ipaddress=f"10.{utl_ID}.{row['Sub Num']}.96", #corp host IP: 102
                                label=f"{row['Utility Name']}.{row['Sub Name']}..Host {(2*int(row['Sub Num'])-1)}",
                                vlan='Corporate')
            host2 = Host(openPorts=[16, 32], utility=row["Utility Name"], substation=row["Sub Name"],
                                adminIP=f"10.{utl_ID}.{row['Sub Num']}.100",
                                ipaddress=f"10.{utl_ID}.{row['Sub Num']}.96", #corp host IP: 103
                                label=f"{row['Utility Name']}.{row['Sub Name']}..Host {(2*int(row['Sub Num']))}",
                                vlan='Corporate')
            RC = RelayController(relayIPlist=["192.168.1.1", "192.168.1.2"], utility=row["Utility Name"], substation=row["Sub Name"],
                                 adminIP=f"10.{utl_ID}.{row['Sub Num']}.2",
                                 ipaddress=f"10.{utl_ID}.{row['Sub Num']}.0", #OT host IP: 3
                                 label=f"{row['Utility Name']}.{row['Sub Name']}..RC {row['Sub Num']}",
                                 vlan='OT')
            outstation = Host(openPorts=[16, 32], utility=row["Utility Name"], substation=row["Sub Name"],
                                adminIP=f"10.{utl_ID}.{row['Sub Num']}.100",
                                ipaddress=f"10.{utl_ID}.{row['Sub Num']}.96", #OT host IP: 4
                                label=f"{row['Utility Name']}.{row['Sub Name']}..outstation {(2*int(row['Sub Num']))}",
                                vlan='Corporate')

            #Add above nodes to substation
            sub.add_node(firewall)
            sub.add_node(router)
            sub.add_node(switch)
            sub.add_node(corp_switch)

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
            sub.add_node(host1)
            sub.add_node(host2)
            sub.add_node(localDatabase)
            sub.add_node(localWebServer)
            sub.add_node(hmi)
            sub.add_node(outstation)

            #Add the non-nodes objects to the substations
            sub.add_switch(switch)
            sub.add_rcs(RC)
            sub.add_subFirewall(firewall)
            sub.add_subRouter(router)
            sub.add_subSwitch(switch)
            sub.add_subRC(RC)

            #firewall command to add the firewalls
            firewall.add_acl_rule("acl0", "Allow DNP3", "10.52.1.","10.52.1.", "20000" ,"TCP", "allow")
            firewall.add_acl_rule("acl1", "Allow HTTPS", "10.52.1.","10.52.1.", "443" ,"TCP", "allow")
            firewall.add_acl_rule("acl2", "Block ICCP", "all","all", "102" ,"TCP", "block")
            firewall.add_acl_rule("acl3", "Block SQL", "all","all", "3306" ,"TCP", "block")

            #protocols added below to the components
            RC.set_protocol("DNP3", "20000", "TCP")
            host1.set_protocol("HTTPS", "443", "TCP")
            host2.set_protocol("HTTPS", "443", "TCP")
            localDatabase.set_protocol("SQL", "3306", "TCP")
            localWebServer.set_protocol("HTTPS", "443", "TCP")
            outstation.set_protocol("DNP3", "20000", "TCP")
            outstation.set_protocol("SQL", "3306", "TCP")
            hmi.set_protocol("HTTPS", "443", "TCP")

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
            # switch.Corp --> localDatabase
            sub.add_link(corp_switch.label, localDatabase.label, "Ethernet", 10.0, 10.0)
            # switch.Corp --> localWebServer
            sub.add_link(corp_switch.label, localWebServer.label, "Ethernet", 10.0, 10.0)

            substations.append(sub)
            name_json = f"Region.{row['Utility Name']}.{row['Sub Name']}.json"
            output_to_json_file(sub, filename=os.path.join(cwd,"Output\\Substations",name_json))

        return substations, unique_dict
    def generate_utilties(self, substations, utility_dict, topology, power_nwk):
        firewall_start = len(substations)+1
        router_start = len(substations)+1
        ems_start = 2501
        utilities = []
        for key, val in utility_dict.items():
            # Constructing the base part of the ID
            util_label = f"Region.{key}"
            print(key)
            utl_ID = val.get('id')

            if topology == 'statistics':
                util = Utility(
                    networkLan=f"10.{utl_ID}.0.0",
                    utl_id=utl_ID,
                    utility_name=key,
                    substations=[substation for substation in substations if substation.utility == key],
                    subFirewalls=[substation.substationFirewall for substation in substations if substation.utility == key],
                    latitude=0,
                    longitude=0
                )
            else:
                util = Utility(
                    networkLan=f"10.{utl_ID}.0.0",
                    utl_id=utl_ID,
                    utility_name=key,
                    substations=[substation for substation in substations if substation.utility == key],
                    subFirewalls=[substation.substationFirewall for substation in substations if
                                  substation.utility == key],
                    latitude=val.get('latitude'),
                    longitude=val.get('longitude')
                )

            utilFirewall=Firewall([], [], val.get('latitude'), val.get('longitude'),
                                utility=key, substation="",
                                adminIP=f"10.{utl_ID}.0.1",
                                ipaddress=f"10.{utl_ID}.0.0",
                                label=f"{key}.{key}..Firewall {firewall_start}",
                                vlan='1')
            utilRouter=Router(interfaces=["eth0", "eth1"], routingTable={}, utility=key, substation="",
                                adminIP=f"10.{utl_ID}.0.2",
                                ipaddress=f"10.{utl_ID}.0.0", #1
                                label=f"{key}.{key}..Router {router_start}",
                                vlan='1')
            utilSwitch=Switch([], utility=key, substation="",
                                adminIP=f"10.{utl_ID}.0.8",
                                ipaddress=f"10.{utl_ID}.0.0", #remove IP addresses, keep admin ip
                                label=f"{key}.{key}..Switch {ems_start}",
                                vlan='OT')
            utilEMS=Host(openPorts=[16, 32], utility=key, substation="utl",
                                adminIP=f"10.{utl_ID}.0.3",
                                ipaddress=f"10.{utl_ID}.0.0",
                                label=f"{key}.{key}..Host {ems_start}",
                                vlan='1')
            utilHMI=Host(openPorts=[16, 32], utility=key, substation="utl",
                                adminIP=f"10.{utl_ID}.0.3",
                                ipaddress=f"10.{utl_ID}.0.0",
                                label=f"{key}.{key}..Host {ems_start}",
                                vlan='1')            
            iccpServer=Host(openPorts=[16, 32], utility=key, substation="utl",
                                adminIP=f"10.{utl_ID}.0.3",
                                ipaddress=f"10.{utl_ID}.0.0",
                                label=f"{key}.{key}..Host {ems_start}",
                                vlan='1') #need to fix this information or see what needs to be changed
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
            util.add_node(utilHMI)
            util.add_node(iccpServer)
            util.add_node(substationsFirewall)
            util.add_node(substationsRouter)
            #Add only those substations that are inside the utility as nodes
            for s in substations:
                if s.utility_id == util.id:
                    util.add_node(s)
            util.add_node(DMZFirewall)

            # Add the non-node objects to the Utility
            util.add_utilityFirewall(utilFirewall)
            util.add_utilityRouter(utilRouter)
            util.add_utilitySwitch(utilSwitch)
            util.add_utilityEMS(utilEMS)
            util.add_iccpserver(iccpServer)
            util.add_substationsRouter(substationsRouter)
            util.add_substationsFirewall(substationsFirewall)
            util.add_DMZFirewall(DMZFirewall)

            #firewall command to add the firewalls
            utilFirewall.add_acl_rule("acl0", "Allow DNP3", "10.52.1.","10.52.1.", "20000" ,"TCP", "allow") #between utilEMS and SubRC
            utilFirewall.add_acl_rule("acl1", "Allow HTTPS", "10.52.1.","10.52.1.", "443" ,"TCP", "allow") #between utilHMI and SubWebServer
            utilFirewall.add_acl_rule("acl2", "Allow ICCP", "10.52.1.","10.52.1.", "102" ,"TCP", "allow") #between utilICCPServer and regICCPClient
            utilFirewall.add_acl_rule("acl3", "Block SQL", "all","all", "3306" ,"TCP", "block") #SQL is not to be found in the utility
            
            #protocols added below 
            utilEMS.set_protocol("DNP3", "20000", "TCP")
            iccpServer.set_protocol("ICCP", "102", "TCP")
            utilHMI.set_protocol("HTTPS", "443", "TCP")

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

            df1 = pd.read_csv("Branches_500.csv")

            if "star" in topology:
                #directly connect all substations to the utility
                for s in substations:
                    util.add_link(substationsRouter.label, s.substationRouter[0].label, "Ethernet", 10.0, 10.0)
            if "radial" in topology:
                for s in substations:
                    if hasattr(s, 'connecting_TS_num') and s.utility_id == util.id:
                        for substation in substations:
                            if substation.substationNumber == s.connecting_TS_num:
                                s_to = substation
                                break
                        print("Connecting substation object found with router label   :", s_to.substationRouter[0].label)
                        util.add_link(s_to.substationRouter[0].label, s.substationRouter[0].label, "Ethernet", 10.0, 10.0)
                    elif s.utility_id == util.id:
                        util.add_link(substationsRouter.label, s.substationRouter[0].label, "Ethernet", 10.0, 10.0)
            if "statistics" in topology:
                #generate connections between utility, substations using Zeyu's statistics
                number_of_substations = val.get('num_of_subs')
                number_of_generators = val.get('num_of_gens')
                print("Number of substations in utility: ", number_of_substations)
                print("Number of generators in utility: ", number_of_generators)
                statistics_based_graph, max_deg_node = generate_nwk(number_of_substations, number_of_generators)
                # get a list of all substation numbers in the utility
                substation_numbers = [s.substationNumber for s in substations if s.utility_id == util.id]
                #print the substation numbers in the utility to check along with the utility id
                logger.info(f"Substation numbers in utility: {substation_numbers}")
                logger.info(f"Number of substations: {len(substation_numbers)}")
                logger.info(f"Utility id: {util.id}")
                power_graph = power_nwk.subgraph(substation_numbers)
                #mapping = network_match(statistics_based_graph, power_graph)
                mapping = main(statistics_based_graph, power_graph)
                util_node = mapping[max_deg_node]
                logger.info(f"Mapping: {mapping}")
                logger.info(f"Number of subs in mapping: {len(mapping)}")
                #add node labels to the statistics based graph based on the mapping
                for node in statistics_based_graph.nodes:
                    statistics_based_graph.nodes[node]['label'] = mapping[node]
                #print labels of the nodes in the statistics based graph
                logger.info(f"Labels of the nodes in the statistics based graph: {statistics_based_graph.nodes(data=True)}")
                logger.info(
                    f"Labels of the nodes in the power based graph: {power_graph.nodes(data=True)}")
                #add links to the utility based on the statistics based graph
                for edge in statistics_based_graph.edges:
                    source = statistics_based_graph.nodes[edge[0]]['label']
                    logger.info(f"Source: {source}")
                    destination = statistics_based_graph.nodes[edge[1]]['label']
                    logger.info(f"Destination: {destination}")
                    #find the substation with substation number equal to source and destination
                    for substation in substations:
                        if substation.substationNumber == int(source):
                            source_substation = substation
                        if substation.substationNumber == int(destination):
                            destination_substation = substation
                        if substation.substationNumber == int(util_node):
                            util.latitude = substation.latitude
                            util.longitude = substation.longitude
                    logger.info(f"Source substation: {source_substation.substationNumber}")
                    logger.info(f"Destination substation: {destination_substation.substationNumber}")
                    util.add_link(source_substation.substationRouter[0].label, destination_substation.substationRouter[0].label, "Ethernet", 10.0, 10.0)
                    logger.info(f"Link added between {source_substation.substationRouter[0].label} and {destination_substation.substationRouter[0].label}")



            # utilityRouter --> DMZFirewall
            util.add_link(utilRouter.label, DMZFirewall.label, "Ethernet", 10.0, 10.0)

            utilities.append(util)
            name_json = f"Region.{key}.json"
            output_to_json_file(util, filename=os.path.join(cwd, "Output\\Utilities", name_json))
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
            regRouter = Router(interfaces=["eth0", "eth1"], routingTable={},
                                    utility="balancing_authority", substation="ba",
                                    adminIP=f"172.30.0.3",
                                    ipaddress=f"172.30.0.0",
                                    label=f"balancing_authority.ba..Router 1551",
                                    vlan='1')
            iccpClient = Host([],
                                    utility="balancing_authority", substation="ba",
                                    adminIP=f"172.30.0.1",
                                    ipaddress=f"172.30.0.0",
                                    label=f"balancing_authority.ba..Host 2801",
                                    vlan='1')

            # Add node objects
            reg.add_node(regFirewall)
            reg.add_node(regRouter)
            reg.add_node(iccpClient)
            for u in utilities:
                reg.add_node(u.utilityFirewall[0])

            # Add the non-node objects to the Utility
            reg.add_regRouter(regRouter)
            reg.add_regFirewall(regFirewall)
            reg.add_iccpClient(iccpClient)

            #firewall command to add the firewalls
            regFirewall.add_acl_rule("acl0", "Block ICCP", "all","all", "102" ,"TCP", "block") #between regICCPClient and utilICCPServer
            regFirewall.add_acl_rule("acl1", "Block HTTPS", "10.52.1.","10.52.1.", "443" ,"TCP", "block") #HTTPS is not to be found in the utility
            regFirewall.add_acl_rule("acl2", "Block DNP3", "10.52.1.","10.52.1.", "20000" ,"TCP", "block") #DNP3 is not to be found in the utility
            regFirewall.add_acl_rule("acl3", "Block SQL", "all","all", "3306" ,"TCP", "block") #SQL is not to be found in the utility

            #protocols added below to the router based on the ports
            iccpClient.set_protocol("ICCP", "102", "TCP")

            # Add links
            reg.add_link(iccpClient.label, regFirewall.label, "Ethernet", 10.0, 10.0)
            reg.add_link(regFirewall.label, regRouter.label, "Ethernet", 10.0, 10.0)
            for u in utilities:
                reg.add_link(regRouter.label, u.utilityRouter[0].label, "fiber", 10.0, 100.0)

            regulatory.append(reg)
            name_json = "Regulatory.json"
            output_to_json_file(reg, filename=os.path.join(cwd, "Output\\Regulatory", name_json))

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

def get_substation_connections(branches_csv, substations_csv, pw_case_object):
    df2 = pd.read_csv(substations_csv, skiprows=1)
    df2.fillna(99999, inplace=True)
    df = pd.read_csv(branches_csv)
    # Convert columns to tuples
    df['Pairs'] = list(zip(df['SubNumberFrom'], df['SubNumberTo']))
    df = df[df['SubNumberFrom'] != df['SubNumberTo']]
    # Find unique pairs
    unique_pairs0 = df['Pairs'].unique()
    # Display unique pairs
    # print(unique_pairs)
    unique_pairs = [None] * len(unique_pairs0)

    #make sure that the unique_pairs0 does not have pair[0] and pair[1] as both generation substations
    for pair in unique_pairs0:
        for index, row in df2.iterrows():
            #if both numbers in the pair are generation substations, remove the pair
            if row['Sub Num'] == pair[0] and row['Gen MW'] != 99999:
                if row['Sub Num'] == pair[1] and row['Gen MW'] != 99999:
                    # print("DELETED PAIR: ", pair)
                    unique_pairs0 = np.delete(unique_pairs0, np.where(unique_pairs0 == pair), axis=0)

    #find the distance between the substations using latitude and longitude information from df2 using haversine function
    for i in range(len(unique_pairs0)):
        for index, row in df2.iterrows():
            if row['Sub Num'] == unique_pairs0[i][0]:
                lat1 = row['Latitude']
                lon1 = row['Longitude']
            if row['Sub Num'] == unique_pairs0[i][1]:
                lat2 = row['Latitude']
                lon2 = row['Longitude']
        unique_pairs[i] = (unique_pairs0[i][0], unique_pairs0[i][1], haversine.haversine((lat1, lon1), (lat2, lon2)))

    #get graph from saw object
    power_graph = pw_case_object.to_graph("substation", geographic=True)
    # print(power_graph.nodes(data=True))
    # for node in power_graph.nodes():
    #     print("Node:", node, "Attributes:", power_graph.nodes[node])



    return unique_pairs, power_graph

def get_num_of_gens(df, name):
    try:
        # Return the count excluding rows where 'Gen MW' is 99999
        return df[df['Gen MW'] != 99999].groupby('Utility Name').size()[name]
    except KeyError:
        # Return 0 if the key is not found
        return 0
def generate_system_from_csv(csv_file, branches_csv):
    cps = CyberPhysicalSystem()

    filepath = r"D:\Github\ECEN689Project\New Code\ACTIVSg2000.pwb"
    print(filepath)
    saw = SAW(FileName=filepath)
    substation_connections, power_nwk = get_substation_connections(branches_csv, csv_file, saw)
    substations, utility_dict = cps.load_substations_from_csv(csv_file, substation_connections)
    utilities = cps.generate_utilties(substations, utility_dict, topology, power_nwk)
    regulatory = cps.generate_BA(substations, utilities)


generate_system_from_csv("Substation_2k.csv", "Branches_2k.csv")

