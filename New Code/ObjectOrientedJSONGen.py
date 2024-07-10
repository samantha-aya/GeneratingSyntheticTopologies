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
import matplotlib.pyplot as plt
import time

import logging

start_json = time.time()
cwd = os.getcwd()
# Configure logging
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.basicConfig(filename=os.path.join(cwd, 'progress.log'), filemode='w', level=logging.INFO)
#logging.basicConfig(filename='C:/ECEN689Project/New Code/progress.log', filemode='w', level=logging.INFO)
logger = logging.getLogger()

config = configparser.ConfigParser()
config.read('settings.ini')
topology = config['DEFAULT']['topology_configuration']

class Node:
    def __init__(self, utility, substation, label, vlan):
        self.utility = utility
#        if vlan == 'Corporate':
#            self.subnetMask = '255.255.255.224'
#        elif vlan == 'OT':
#            self.subnetMask = '255.255.255.192'
        self.vlan = vlan
        self.substation = substation
        self.label = label
        self.compromised = False
class Firewall(Node):
    def __init__(self, acls, interfaces, Latitude, Longitude, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.acls = {}
        self.interfaces = {}
        self.Latitude = Latitude
        self.Longitude = Longitude

    def add_interfaces(self, interfaceLabel, interfaceIP, subnet):
        #this allows for an interface to be added with an ip address
        #multiple interfaces can be added
        firewallInterface = {
            "label": interfaceLabel, #or type? for example: eth0
            "ipaddress": interfaceIP,
            "subnet": subnet
        }
        if interfaceLabel in self.interfaces:
            self.interfaces[interfaceLabel].append(firewallInterface)
        else:
            self.interfaces[interfaceLabel] = [firewallInterface]

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
        self.interfaces = {}
        self.routingTable = {}

    def add_interfaces(self, interfaceLabel, interfaceIP, subnet):
        #this allows for an interface to be added with an ip address
        #multiple interfaces can be added
        routerInterface = {
            "label": interfaceLabel, #or type? for example: eth0
            "ipaddress": interfaceIP,
            "subnet": subnet
        }
        if interfaceLabel in self.interfaces:
            self.interfaces[interfaceLabel].append(routerInterface)
        else:
            self.interfaces[interfaceLabel] = [routerInterface]
        
class Switch(Node):
    def __init__(self, arpTable, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.arpTable = arpTable
class RelayController(Node):
    def __init__(self, ipaddress, subnetMask, relayIPlist, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ipAddress = ipaddress
        self.subnetMask = subnetMask
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
    def __init__(self, ipaddress, subnetMask, openPorts, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ipAddress = ipaddress
        self.subnetMask = subnetMask
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
        self.OTHosts = [f"10.{utl_id}.{substation_num}.{i}" for i in range(1, 62)]
        self.routeAddress = networklan[:-1] + "64"
        self.routeSubnetMask ="255.255.255.224"
        self.routingHosts = [f"10.{utl_id}.{substation_num}.{i}" for i in range(65, 94)]
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
        self.regulatory = ""

    def add_regulatory(self, reg):
        self.regulatory = reg
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
                minimum_distance = int(99999)
                for pair in substation_connections:
                    if row['Sub Num'] in pair:
                        print(pair)
                        print(minimum_distance)
                        if minimum_distance > int(pair[2]):
                            minimum_distance = int(pair[2])
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
                                label=f"{row['Utility Name']}.{row['Sub Name']}..Firewall {row['Sub Num']}",
                                vlan='Corporate')

            router = Router([], routingTable={}, utility=row["Utility Name"], substation=row["Sub Name"],
                                label=f"{row['Utility Name']}.{row['Sub Name']}..Router {row['Sub Num']}",
                                vlan='Corporate')
            switch=Switch([], utility=row["Utility Name"], substation=row["Sub Name"],
                                label=f"{row['Utility Name']}.{row['Sub Name']}.OT.Switch {(2*int(row['Sub Num'])-1)}",
                                vlan='OT')
            corp_switch=Switch([], utility=row["Utility Name"], substation=row["Sub Name"],
                                label=f"{row['Utility Name']}.{row['Sub Name']}.Corporate.Switch {(2*int(row['Sub Num']))}",
                                vlan='Corporate')
            localDatabase = Host(openPorts=[16, 32], utility=row["Utility Name"], substation=row["Sub Name"],
                                ipaddress=f"10.{utl_ID}.{row['Sub Num']}.68", #corp host IP: 68
                                subnetMask="255.255.255.244",
                                label=f"{row['Utility Name']}.{row['Sub Name']}..LocalDatabase {(2*int(row['Sub Num'])-1)}",
                                vlan='Corporate')
            localWebServer = Host(openPorts=[16, 32], utility=row["Utility Name"], substation=row["Sub Name"],
                                ipaddress=f"10.{utl_ID}.{row['Sub Num']}.69", #corp host IP: 69
                                subnetMask="255.255.255.244",
                                label=f"{row['Utility Name']}.{row['Sub Name']}..LocalWebServer {(2*int(row['Sub Num']))}",
                                vlan='Corporate')
            hmi = Host(openPorts=[16, 32], utility=row["Utility Name"], substation=row["Sub Name"],
                                ipaddress=f"10.{utl_ID}.{row['Sub Num']}.70", #corp host IP: 70
                                subnetMask="255.255.255.244",
                                label=f"{row['Utility Name']}.{row['Sub Name']}..hmi {(2*int(row['Sub Num'])-1)}",
                                vlan='Corporate')
            host1 = Host(openPorts=[16, 32], utility=row["Utility Name"], substation=row["Sub Name"],
                                ipaddress=f"10.{utl_ID}.{row['Sub Num']}.66", #corp host IP: 66
                                subnetMask="255.255.255.244",
                                label=f"{row['Utility Name']}.{row['Sub Name']}..Host {(2*int(row['Sub Num'])-1)}",
                                vlan='Corporate')
            host2 = Host(openPorts=[16, 32], utility=row["Utility Name"], substation=row["Sub Name"],
                                ipaddress=f"10.{utl_ID}.{row['Sub Num']}.67", #corp host IP: 67
                                subnetMask="255.255.255.244",
                                label=f"{row['Utility Name']}.{row['Sub Name']}..Host {(2*int(row['Sub Num']))}",
                                vlan='Corporate')
            RC = RelayController(relayIPlist=["192.168.1.1", "192.168.1.2"], utility=row["Utility Name"], substation=row["Sub Name"],
                                 ipaddress=f"10.{utl_ID}.{row['Sub Num']}.2", #OT host IP: 2
                                 subnetMask="255.255.255.192",
                                 label=f"{row['Utility Name']}.{row['Sub Name']}..RC {row['Sub Num']}",
                                 vlan='OT')
            outstation = Host(openPorts=[16, 32], utility=row["Utility Name"], substation=row["Sub Name"],
                                ipaddress=f"10.{utl_ID}.{row['Sub Num']}.3", #OT host IP: 3
                                subnetMask="255.255.255.192",
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

            # commands to add interfaces to routers and firewalls
            firewall.add_interfaces("eth0", f"10.{utl_ID}.{row['Sub Num']}.1","255.255.255.192") # interface to OT network
            firewall.add_interfaces("eth1", f"10.{utl_ID}.{row['Sub Num']}.97","255.255.255.252") # interface to routing network
            firewall.add_interfaces("eth2", f"10.{utl_ID}.{row['Sub Num']}.65","255.255.255.244") # interface to corporate network
            router.add_interfaces("eth0", f"10.{utl_ID}.{row['Sub Num']}.98","255.255.255.252") # routing subnet (internal)
            router.add_interfaces("eth1", f"10.{utl_ID}.{row['Sub Num']}.101","255.255.255.252") # routing subnet (external) ***this one will be changed

            #firewall command to add the firewalls
            firewall.add_acl_rule("acl0", "Allow DNP3", f"10.{utl_ID}.0.11",f"10.{utl_ID}.{row['Sub Num']}.3", "20000" ,"TCP", "allow") #from EMS to outstation
            firewall.add_acl_rule("acl1", "Allow HTTPS", f"10.{utl_ID}.0.12",f"10.{utl_ID}.{row['Sub Num']}.100", "443" ,"TCP", "allow") #HMI to web server
            firewall.add_acl_rule("acl2", "Allow SQL", f"10.{utl_ID}.{row['Sub Num']}.99",f"10.{utl_ID}.{row['Sub Num']}.3", "3306" ,"TCP", "allow") #from database to outstation

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
        metrics_df = pd.DataFrame()
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
                                ipaddress=f"10.{utl_ID}.0.21", #interface to router (to BA Firewall)
                                #ipaddress=f"10.{utl_ID}.0.9", #interface to EMS/HMI subnet
                                label=f"{key}.{key}..UtilityFirewall {firewall_start}",
                                vlan='1')

            utilRouter=Router(interfaces=["eth0", "eth1"], routingTable={}, utility=key, substation="",
                                ipaddress=f"10.{utl_ID}.0.0", #1
                                label=f"{key}.{key}..UtilityRouter {router_start}",
                                vlan='1')

            utilRouter=Router(interfaces=["eth0", "eth1"], routingTable={}, utility=key, substation="",
                                label=f"{key}.{key}..Router {router_start}",
                                vlan='1')
            utilSwitch=Switch([], utility=key, substation="",
                                label=f"{key}.{key}..Switch {ems_start}",
                                vlan='OT')
            utilCorpSwitch = Switch([], utility=key, substation="",
                                ipaddress=f"10.{utl_ID}.0.0",  # remove IP addresses, keep admin ip
                                label=f"{key}.{key}.Corporate.Switch {ems_start}",
                                vlan='Corporate')
            utilEMS=Host(openPorts=[16, 32], utility=key, substation="utl",
                                ipaddress=f"10.{utl_ID}.0.11",
                                label=f"{key}.{key}..EMS {ems_start}",
                                vlan='1')
            utilHMI=Host(openPorts=[16, 32], utility=key, substation="utl",
                                ipaddress=f"10.{utl_ID}.0.12",
                                label=f"{key}.{key}..HMI {ems_start}",
                                vlan='1')
            iccpServer=Host(openPorts=[16, 32], utility=key, substation="utl",
                                ipaddress=f"10.{utl_ID}.0.3",
                                label=f"{key}.{key}..ICCPServer {ems_start}",
                                subnetMask="255.255.255.248",
                                label=f"{key}.{key}..Host {ems_start}",
                                vlan='1')
            utilHMI=Host(openPorts=[16, 32], utility=key, substation="utl",
                                ipaddress=f"10.{utl_ID}.0.12",
                                subnetMask="255.255.255.248",
                                label=f"{key}.{key}..Host {ems_start}",
                                vlan='1')
            iccpServer=Host(openPorts=[16, 32], utility=key, substation="utl",
                                ipaddress=f"10.{utl_ID}.0.3",
                                subnetMask="255.255.255.248",
                                label=f"{key}.{key}..Host {ems_start}",
                                vlan='1') #need to fix this information or see what needs to be changed
            router_start = router_start + 1

            substationsRouter=Router([], routingTable={}, utility=key, substation="",
                                ipaddress=f"10.{utl_ID}.0.18",
                                     # we will need one other interface (and IP) for each substation link
                                label=f"{key}.{key}..SubstationRouter {router_start}",
                                vlan='1')
            firewall_start = firewall_start+1
            substationsFirewall=Firewall([], [], val.get('latitude'), val.get('longitude'),
                                utility=key, substation="",
                                ipaddress=f"10.{utl_ID}.0.17", #interfact to substation router
                                #ipaddress=f"10.{utl_ID}.0.10", #interface to EMS/HMI subnet
                                label=f"{key}.{key}..SubstationFirewall {firewall_start}",
                                vlan='1')
            firewall_start = firewall_start + 1
            DMZFirewall=Firewall([], [], val.get('latitude'), val.get('longitude'),
                                utility=key, substation="",
                                ipaddress=f"10.{utl_ID}.0.26", #interface to router (to BA firewall)
                                #ipaddress=f"10.{utl_ID}.0.2", #interface to ICCP server
                                label=f"{key}.{key}..DMZFirewall {firewall_start}",
                                vlan='1')
            firewall_start = firewall_start + 1
            router_start = router_start + 1

            util.add_node(utilFirewall)
            util.add_node(utilRouter)
            util.add_node(utilSwitch)
            util.add_node(utilCorpSwitch)
            util.add_node(utilEMS)
            util.add_node(utilHMI)
            util.add_node(iccpServer)
            util.add_node(substationsFirewall)
            util.add_node(substationsRouter)
            #Add only those substations that are inside the utility as nodes
            for s in substations:
                if s.utility_id == util.id:
                    util.add_node(s)
                    substationsRouter.add_interfaces(f"eth{s.substationNumber}", f"10.{util.id}.{s.substationNumber}.102","255.255.255.252")  # routing subnet (external) ***this one will be changed
                    substationsFirewall.add_acl_rule("acl0", "Allow DNP3", f"10.{util.id}.0.11", f"10.{utl_ID}.{s.substationNumber}.2", "20000", "TCP","allow")  # between utilEMS and SubRC,  outstation IP: f"10.{utl_ID}.{row['Sub Num']}.3"
                    substationsFirewall.add_acl_rule("acl1", "Allow HTTPS", f"10.{util.id}.0.12", f"10.{utl_ID}.{s.substationNumber}.100", "443", "TCP","allow")  # between utilHMI and SubWebServer (in substation)

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

            # commands to add interfaces to firewalls and routers
            substationsFirewall.add_interfaces("eth0", f"10.{utl_ID}.0.17","255.255.255.252") #interfact to substation router
            substationsFirewall.add_interfaces("eth1", f"10.{utl_ID}.0.10","255.255.255.248") #interface to EMS/HMI subnet
            utilFirewall.add_interfaces("eth0", f"10.{utl_ID}.0.9","255.255.255.248") #interface to EMS/HMI subnet
            utilFirewall.add_interfaces("eth1", f"10.{utl_ID}.0.21","255.255.255.252") #interface to router (to BA Firewall)
            DMZFirewall.add_interfaces("eth0", f"10.{utl_ID}.0.2","255.255.255.248") #interface to ICCP server
            DMZFirewall.add_interfaces("eth1", f"10.{utl_ID}.0.26","255.255.255.252") #interface to router (to BA firewall)
            substationsRouter.add_interfaces("eth0", f"10.{utl_ID}.0.18","255.255.255.252") #interface to internal UCC
            utilRouter.add_interfaces("eth0", f"10.{utl_ID}.0.22","255.255.255.252") #interface towards util firewall
            utilRouter.add_interfaces("eth1", f"10.{utl_ID}.0.25","255.255.255.252") #interface towards DMZ
            utilRouter.add_interfaces("eth2", f"10.{utl_ID}.0.33","255.255.255.252") #interface towards BA

            #firewall command to add the firewall acls
            utilFirewall.add_acl_rule("acl0", "Allow DNP3", "10.52.1.","10.52.1.", "20000" ,"TCP", "allow") #between utilEMS and SubRC
            utilFirewall.add_acl_rule("acl1", "Allow HTTPS", "10.52.1.","10.52.1.", "443" ,"TCP", "allow") #between utilHMI and SubWebServer
            utilFirewall.add_acl_rule("acl2", "Allow ICCP", "10.52.1.","10.52.1.", "102" ,"TCP", "allow") #between utilICCPServer and regICCPClient
            utilFirewall.add_acl_rule("acl3", "Block SQL", "all","all", "3306" ,"TCP", "block") #SQL is not to be found in the utility

            #protocols added below
            #substationsFirewall.add_acl_rule("acl0", "Allow DNP3", f"10.{utl_ID}.0.11","XXX.3", "20000" ,"TCP", "allow") #between utilEMS and SubRC,  outstation IP: f"10.{utl_ID}.{row['Sub Num']}.3"
            #substationsFirewall.add_acl_rule("acl1", "Allow HTTPS", f"10.{utl_ID}.0.12","XXX.12", "443" ,"TCP", "allow") #between utilHMI and SubWebServer (in substation)
            DMZFirewall.add_acl_rule("acl2", "Allow ICCP", f"172.30.0.6",f"10.{utl_ID}.0.3", "102" ,"TCP", "allow") #between utilICCPServer and regICCPClient
            DMZFirewall.add_acl_rule("acl3", "Allow ICCP", f"10.{utl_ID}.0.3",f"10.{utl_ID}.0.11", "102" ,"TCP", "allow") #between utilICCPServer and utilEMS
            utilFirewall.add_acl_rule("acl4", "Allow ICCP", f"10.{utl_ID}.0.3", f"10.{utl_ID}.0.11", "102" ,"TCP", "allow") #allow HMI to send util data to ICCP server
            
            #protocols added below
            utilEMS.set_protocol("DNP3", "20000", "TCP")
            iccpServer.set_protocol("ICCP", "102", "TCP")
            utilHMI.set_protocol("HTTPS", "443", "TCP")


            # corporate switch to ICCP server
            util.add_link(utilCorpSwitch.label, iccpServer.label, "Ethernet", 10.0, 10.0)
            # DMZ firewall to corporate switch
            util.add_link(DMZFirewall.label, utilCorpSwitch.label, "Ethernet", 10.0, 10.0)
            # router to DMZ firewall
            util.add_link(utilRouter.label, DMZFirewall.label, "Ethernet", 10.0, 10.0)

            # router --> firewall
            util.add_link(utilRouter.label, utilFirewall.label, "Ethernet", 10.0, 10.0)
            # utility_firewall --> EMSswitch
            util.add_link(utilFirewall.label, utilSwitch.label, "Ethernet", 10.0, 10.0)
            # switch --> EMS
            util.add_link(utilSwitch.label, utilEMS.label, "Ethernet", 10.0, 10.0)
            # switch --> HMI
            util.add_link(utilSwitch.label, utilHMI.label, "Ethernet", 10.0, 10.0)

            # EMSSwitch --> substationrouter
            util.add_link(utilSwitch.label, substationsFirewall.label, "Ethernet", 10.0, 10.0)
            # substationrouter --> substationFirewall
            util.add_link(substationsFirewall.label, substationsRouter.label, "Ethernet", 10.0, 10.0)
            # substationsRouter --> individual substation routers
            if "star" in topology:
                #directly connect all substations to the utility
                for s in substations:
                    if s.utility_id == util.id:
                        util.add_link(substationsRouter.label, s.substationRouter[0].label, "Ethernet", 10.0, 10.0)
            if "radial" in topology:
                for s in substations:
                    if s.utility_id == util.id:
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
                statistics_based_graph, max_deg_node, metrics_dict = generate_nwk(number_of_substations, number_of_generators)
                metrics_dict['Utility'] = utl_ID
                # store metrics_dict into metrics_df
                metrics_df = metrics_df._append(metrics_dict, ignore_index=True)
                # get a list of all substation numbers in the utility
                substation_numbers = [s.substationNumber for s in substations if s.utility_id == util.id]
                #print the substation numbers in the utility to check along with the utility id
                logger.info(f"Substation numbers in utility: {substation_numbers}")
                logger.info(f"Number of substations: {len(substation_numbers)}")
                logger.info(f"Utility id: {util.id}")
                power_graph = power_nwk.subgraph(substation_numbers)
                #mapping = network_match(statistics_based_graph, power_graph)
                mapping = main(statistics_based_graph, power_graph, util.id)
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

            metrics_df.to_csv("Output\\metrics.csv", index=False)
        return utilities

    def generate_BA(self, substations, utilities, case, n_ba):
        regulatory = []
        if n_ba > 1:
            print('n_ba > 1')
            num_regs = n_ba
            # cluster utilities into 30 clusters
            kmeans = KMeans(n_clusters=num_regs, random_state=0).fit([[u.latitude, u.longitude] for u in utilities])
            # Extracting the centroids
            centroids = kmeans.cluster_centers_
            # Adding the cluster labels (regulatory names) to the original DataFrame
            for i, u in enumerate(utilities):
                u.add_regulatory(f"Regulatory {kmeans.labels_[i]}")
            # Create a dictionary with keys as the unique values and values as a sequence starting from 1
            starting_reg_number = 1
            unique_dict_reg = {
                name: {
                    'id': starting_reg_number + i,
                    'latitude': centroids[i][0],
                    'longitude': centroids[i][1],
                    'num_of_utils': len([u for u in utilities if u.regulatory == name])
                }
                for i, name in enumerate([f"Regulatory {i}" for i in range(num_regs)])
            }

            print(unique_dict_reg)
            for key, val in unique_dict_reg.items():
                print(key)
                reg = Regulatory(
                    label=f"{key}",
                    networklan=f"172.{val.get('id')}.0.0",
                    utils=[u for u in utilities if u.regulatory == key],
                    utilFirewalls=[u.utilityFirewall for u in utilities if u.regulatory == key],
                    latitude=val.get('latitude'),
                    longitude=val.get('longitude')
                )
                regFirewall = Firewall([], [], reg.latitude, reg.longitude,
                                    utility="balancing_authority", substation="ba",
                                    label=f"balancing_authority.ba..Firewall 1701",
                                    vlan='1')
                regRouter = Router(interfaces=["eth0", "eth1"], routingTable={},
                                   utility="balancing_authority", substation="ba",
                                   label=f"balancing_authority.ba..Router 1551",
                                   vlan='1')
                iccpClient = Host(utility="balancing_authority", substation="ba",
                                  ipaddress=f"172.{val.get('id')}.0.6",  # interface to firewall %%%subnetMask = "255.255.255.XXX"
                                  subnetMask = "255.255.255.252", #ideally every host, and router interface, and firewall interface should have a subnet mask attribute
                                  label=f"balancing_authority.ba..Host 2801",
                                  vlan='1')

                # Add node objects
                reg.add_node(regFirewall)
                reg.add_node(regRouter)
                reg.add_node(iccpClient)

                # Add the non-node objects to the Utility
                reg.add_regRouter(regRouter)
                reg.add_regFirewall(regFirewall)
                reg.add_iccpClient(iccpClient)

                # protocols added below to the router based on the ports
                # commands to add interfaces to firewalls and routers
                regFirewall.add_interfaces("eth0", f"172.{val.get('id')}.0.2", "255.255.255.252")  # interface to router
                regFirewall.add_interfaces("eth1", f"172.{val.get('id')}.0.5", "255.255.255.252")  # interface to ICCP server
                regRouter.add_interfaces("eth0", f"172.{val.get('id')}.0.1", "255.255.255.252")  # interface to firewall
                #regRouter.add_interfaces(f"eth{val.get('id')}", f"172.{val.get('id')}.0.34", "255.255.255.252")  # interface to UCC #this one will be changed based on UCC subnet (interface towards UCC)

                # protocols added below to the router based on the ports
                iccpClient.set_protocol("ICCP", "102", "TCP")

                # Add links
                reg.add_link(iccpClient.label, regFirewall.label, "Ethernet", 10.0, 10.0)
                reg.add_link(regFirewall.label, regRouter.label, "Ethernet", 10.0, 10.0)

                for u in utilities:
                    reg.add_node(u.utilityFirewall[0])
                    # firewall command to add the firewalls
                    regRouter.add_interfaces(f"eth{u.id}", f"10.{u.id}.0.34","255.255.255.252")  # routing subnet (external) ***this one will be changed
                    regFirewall.add_acl_rule("acl0", "Allow ICCP", f"172.{val.get('id')}.0.6", f"10.{u.id}.0.3", "102", "TCP","allow")  # between utilICCPServer and regICCPClient
                    reg.add_link(regRouter.label, u.utilityRouter[0].label, "fiber", 10.0, 100.0)
                regulatory.append(reg)
                name_json = f"Regulatory{val.get('id')}.json"
                output_to_json_file(reg, filename=os.path.join(cwd, "Output\\Regulatory", name_json))

        else:
            print('n_ba <= 1')
            # cluster utilities into 30 clusters
            kmeans = KMeans(n_clusters=1, random_state=0).fit([[u.latitude, u.longitude] for u in utilities])
            # Extracting the centroids
            centroid = kmeans.cluster_centers_
            reg = Regulatory(
                label="Regulatory",
                networklan="172.30.0.0",
                utils=utilities,
                utilFirewalls=[ut.utilityFirewall for ut in utilities],
                latitude=centroid[0][0],
                longitude=centroid[0][1]
            )
            regFirewall = Firewall([], [], reg.latitude, reg.longitude,
                                    utility="balancing_authority", substation="ba",
                                    label=f"balancing_authority.ba..Firewall 1701",
                                    vlan='1')
            regRouter = Router(interfaces=["eth0", "eth1"], routingTable={},
                                    utility="balancing_authority", substation="ba",
                                    label=f"balancing_authority.ba..Router 1551",
                                    vlan='1')
            iccpClient = Host(openPorts=[16, 32],utility="balancing_authority", substation="ba",
                                    ipaddress=f"172.30.0.6", #interface to firewall
                                    subnetMask = "255.255.255.252", #ideally every host, and router interface, and firewall interface should have a subnet mask attribute
                                    label=f"balancing_authority.ba..Host 2801",
                                    vlan='1')

            # Add node objects
            reg.add_node(regFirewall)
            reg.add_node(regRouter)
            reg.add_node(iccpClient)

            # Add the non-node objects to the Utility
            reg.add_regRouter(regRouter)
            reg.add_regFirewall(regFirewall)
            reg.add_iccpClient(iccpClient)

            # protocols added below to the router based on the ports
            # commands to add interfaces to firewalls and routers
            regFirewall.add_interfaces("eth0", f"172.30.0.2", "255.255.255.252") #interface to router
            regFirewall.add_interfaces("eth1", f"172.30.0.5", "255.255.255.252") #interface to ICCP server
            regRouter.add_interfaces("eth0", f"172.30.0.1", "255.255.255.252") #interface to firewall

            #protocols added below to the router based on the ports
            iccpClient.set_protocol("ICCP", "102", "TCP")

            # Add links
            reg.add_link(iccpClient.label, regFirewall.label, "Ethernet", 10.0, 10.0)
            reg.add_link(regFirewall.label, regRouter.label, "Ethernet", 10.0, 10.0)

            for u in utilities:
                reg.add_node(u.utilityFirewall[0])
                # firewall command to add the firewalls
                regFirewall.add_acl_rule("acl0", "Allow ICCP", f"172.30.0.6", f"10.{u.id}.0.3", "102", "TCP",
                                         "allow")  # between utilICCPServer and regICCPClient
                reg.add_link(regRouter.label, u.utilityRouter[0].label, "fiber", 10.0, 100.0)
                regRouter.add_interfaces(f"eth{u.id}", f"10.{u.id}.0.34","255.255.255.252")  # interface to UCC #this one will be changed based on UCC subnet (interface towards UCC)

            regulatory.append(reg)
            name_json = f"Regulatory{reg.label}.json"
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
def get_substation_connections(branches_csv, substations_csv, pw_case_object, dist_file):

    if not os.path.exists(dist_file):
        print('creating csv file')
        df2 = pd.read_csv(substations_csv, skiprows=1)
        df2.fillna(99999, inplace=True)
        df = pd.read_csv(branches_csv)
        # Convert columns to tuples
        df['Pairs'] = list(zip(df['SubNumberFrom'], df['SubNumberTo']))
        df = df[df['SubNumberFrom'] != df['SubNumberTo']]
        # convert Gen MW column to float
        df2['Gen MW'] = df2['Gen MW'].astype(int)
        # Find unique pairs
        unique_pairs0 = df['Pairs'].unique()
        # Display unique pairs
        # print(unique_pairs)
        unique_pairs = [None] * len(unique_pairs0)

        #make sure that the unique_pairs0 does not have pair[0] and pair[1] as both generation substations
        for pair in unique_pairs0:
            matching_row0 = df2[df2['Sub Num'] == pair[0]]
            matching_row1 = df2[df2['Sub Num'] == pair[1]]
            # print(matching_row1)
            #if both numbers in the pair are generation substations, remove the pair
            if matching_row1['Gen MW'].values[0] != 99999 and matching_row0['Gen MW'].values[0] != 99999:
                print("DELETED PAIR: ", pair)
                unique_pairs0 = np.array([row for row in unique_pairs0 if not np.array_equal(row, pair)])

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

        # convert unique pairs to a dataframe with three columns
        unique_pairs_df = pd.DataFrame(unique_pairs, columns=['SubNumberFrom', 'SubNumberTo', 'Distance'])
        unique_pairs_df.to_csv(dist_file, index=False)
    else:
        print('Read from csv file')
        unique_pairs_df = pd.read_csv(dist_file)

    # convert the unique pairs dataframe to a unique_pairs[i] = (unique_pairs0[i][0], unique_pairs0[i][1], haversine.haversine((lat1, lon1), (lat2, lon2)))
    unique_pairs = unique_pairs_df.to_numpy()

    #get graph from saw object
    if pw_case_object is None:
        power_graph = None
    else:
        power_graph = pw_case_object.to_graph("substation", geographic=True)
        plt.plot(power_graph)

    print("Power graph funciton executed")
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
def generate_system_from_csv(csv_file, branches_csv, filepath, n_ba, dist_file):
    cps = CyberPhysicalSystem()
    if no_powerworld:
        substation_connections, power_nwk = get_substation_connections(branches_csv, csv_file, None, dist_file)
        substations, utility_dict = cps.load_substations_from_csv(csv_file, substation_connections)
        utilities = cps.generate_utilties(substations, utility_dict, topology, power_nwk)
        regulatory = cps.generate_BA(substations, utilities, selected_case, n_ba)
    else:
        saw = SAW(FileName=filepath)
        substation_connections, power_nwk = get_substation_connections(branches_csv, csv_file, saw, dist_file)
        substations, utility_dict = cps.load_substations_from_csv(csv_file, substation_connections)
        utilities = cps.generate_utilties(substations, utility_dict, topology, power_nwk)
        regulatory = cps.generate_BA(substations, utilities, selected_case, n_ba)

n_ba = int(config['DEFAULT']['n_ba'])
print('Number of BAs:', n_ba)
no_powerworld = config['DEFAULT']['no_powerworld']
if 'True' in no_powerworld:
    no_powerworld = True
else:
    no_powerworld = False
print('No PowerWorld:', no_powerworld)
selected_case = config['DEFAULT']['case']
print('Selected case:', selected_case)
if '2k' in selected_case:
    filepath = os.path.join(cwd, 'ACTIVSg2000.pwb')
    sub_file = "Substation_2k.csv"
    branch_file = "Branches_2k.csv"
    dist_file = '2k_substation_distances.csv'
elif '500' in selected_case:
    filepath = os.path.join(cwd, 'ACTIVSg500.pwb')
    sub_file = "Substation_500bus.csv"
    branch_file = "Branches_500.csv"
    dist_file = '500_substation_distances.csv'
elif '10k' in selected_case:
    filepath = os.path.join(cwd, 'ACTIVSg10k.pwb')
    sub_file = "Substation_10k.csv"
    branch_file = "Branches_10k.csv"
    dist_file = '10k_substation_distances.csv'

print('Filename:', filepath)
generate_system_from_csv(sub_file, branch_file, filepath, n_ba, dist_file)

end_json = time.time()
total_time_json = end_json - start_json
print(f"{total_time_json:.2f} seconds")  #output time with 2 decimal places