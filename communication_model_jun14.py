# -*- coding: utf-8 -*-
"""
Spyder Editor
This program builds the communication model for the South Zone (Mcallen) of Texas Synthetic Grid
This is a temporary script file.

We will build a graph where each node will be considered as one of the cyber components.
And each link will be modelled as the communication link between the nodes.
Attributes of the Nodes will be depended on Node types: Host System, Switch, Router, Firewall, Relays
Attributes of the Edges will be : source, source type, target, target type, distance, datarates.

Example: Relay communication in substation X with the Main Control Center (let say Ercot Taylor in our case) 

||********|| ICCP **********    ********   ICCP over   ********     **********     ||********||
|          |<---> |Firewall|<-->|Router| <-----------> |Router|<--->|Firewall|<--->|          |
|  ERCOT   |      **********    ********      MPLS     ********     **********     | UTILITY  |
|  Taylor  |                                                                       |   EMS    |
|          |                                                                       |  ICCP    |
|  ICCP    | ICCP **********    ********   ICCP over   ********     **********     |  Client/ |
|  Server/ |<---> |Firewall|<-->|Router| <------------>|Router|<--->|Firewall|<--->|  Server  |
|  Client  |      **********    ********      DACS     ********     **********     ||********|| 
||********||

We detrmine which substation be allocated to which utility based on the clustering on distance.
Each Utility is roughly controlling 10-12 Substations through different communication techniques.

||********|| DNP3 **********    ********       **********                    *****************
|          |<---> |Firewall|<-->|Router|<----->|Wireless|<----Wireless------>|Serial FW Sub A|
| UTILITY  |      **********    ********       **********                    *****************
|  EMS     |                      ^   ^              ^                     *****************          
|          |                      |   |    *******   |-----WiFi link------>|  IP FW Sub X  |                 
|  DNP3    |                      |   |--->|SONET|                         *****************
|  Server/ |                      |        ******* similarly for SONET(Fiber)
|  Client  |                      |---->**********  
||********||                            |Cellular| similarly for Cellular NW 
                                        **********

Inside the substation 
***************       ********        ******************          *********
| IP FW Sub X |<----->|Switch|<------>|Relay controller|<-------->|Relay A|
***************       ********        ******************<-----    *********
                                                             |    ********* 
                                                             ---->|Relay B|
                                                                  *********
"""          


import json
import xlrd
import gmplot
from collections import defaultdict
from sklearn.cluster import KMeans
import numpy as np
import random

def isNotInNeighbors(lookingFor,list):
    for bus in list:
        for neighbor in bus["Neighbors"]:
            if neighbor["NodeID"] == lookingFor:
                return 0
    return 1

#creates a google map object
gmap3 = gmplot.GoogleMapPlotter(26.626, -98.1836, 9)
gmap4 = gmplot.GoogleMapPlotter(26.626, -98.1836, 9)

#sets the path for the excel file
excelFilePath = "McAllenSubstationCoordinates.xls"

#create excel object in python
excelFileObj = xlrd.open_workbook(excelFilePath)
#get the first sheet in excel file. First sheet has substation number(NodeID), and latitude and longitude
firstSheet = excelFileObj.sheet_by_index(0)
#gets the number of rows in fist sheet
firstSheetLength = firstSheet.nrows

# refernce Bus list
refBusList = []
latList = []
longList = []

for i in range(1,firstSheetLength):
    singleBus = {
        "NodeID": firstSheet.cell_value(i,1),
        "Cost":"",
        "Port":"",
        "IPAddress":"",
        "LinkType": "",
        "SubstationNumber":firstSheet.cell_value(i,2),
        "Longitude":firstSheet.cell_value(i,3),
        "Latitude":firstSheet.cell_value(i,4),
        "City":firstSheet.cell_value(i,0)
        }
    latList.append(firstSheet.cell_value(i,4))
    longList.append(firstSheet.cell_value(i,3))
    refBusList.append(singleBus)

gmap3.scatter( latList, longList, '# FF0000', size = 40, marker = False ) 
gmap3.plot(latList, longList, 'cornflowerblue', edge_width = 2.5)
gmap3.draw( "map13.html" ) 

gmap4.heatmap( latList, longList )
gmap4.draw( "heatMap.html" ) 

mcAllenBusList = []
#get the second sheet in excel file
secondSheet = excelFileObj.sheet_by_index(1)
#gets the number of rows in second sheet
secondSheetLength = secondSheet.nrows
#used to know if the bus is a Neighbor bus and not a new bus
isNeighbor = 0
duplicateBus = 0

#sets the first 'From bus' in the excel sheet
newestBus = {}
count = 0
for i in range(1,secondSheetLength):
    nextBus = secondSheet.cell_value(i,0)
    neighborBusNumber = secondSheet.cell_value(i,1)
         #search refBusArray for current Bus
    for checkBuses in mcAllenBusList:
        #if fromBus has been added to mcAllenBusList alread, populate neighbors
        duplicateBus = 0
        if nextBus == checkBuses["NodeID"]:
            for potentialNeighborBus in refBusList:
                if (potentialNeighborBus["NodeID"] == neighborBusNumber):
                    isNeighbor = 1
                    if isNotInNeighbors(potentialNeighborBus["NodeID"],mcAllenBusList):
                        checkBuses["Neighbors"].append(potentialNeighborBus)
    #if new fromBus, then add it to mcAllen List
    if isNeighbor == 0:
        for lookupNewBus in refBusList:
            if lookupNewBus["NodeID"] == nextBus:
                count = count+1
                newestBus = {
                        "NodeID": lookupNewBus["NodeID"],
                        "SubstationNumber": lookupNewBus["SubstationNumber"],
                        "Cost":lookupNewBus["Cost"],
                        "Port":lookupNewBus["Port"],
                        "IPAddress":lookupNewBus["IPAddress"],
                        "LinkType": "",
                        "Longitude": lookupNewBus["Longitude"],
                        "Latitude": lookupNewBus["Latitude"],
                        "City":lookupNewBus["City"],
                        "Neighbors": []
                        }
                mcAllenBusList.append(newestBus)
                #add first neighbor bus
                for neighborBus in refBusList:
                    if neighborBus["NodeID"] == neighborBusNumber:
                        newestBus["Neighbors"].append(neighborBus)
                        break
    isNeighbor = 0

print(len(mcAllenBusList))
#group all the nodes by substationNumber
groups = defaultdict(list)
for obj in mcAllenBusList:
    groups[obj["SubstationNumber"]].append(obj)
grouped_by_substation = groups.values()
print(len(grouped_by_substation))

# construction of the communication network
# extract the distance between each 
thirdSheet = excelFileObj.sheet_by_index(2)
#gets the number of rows in third sheet
thirdSheetLength = thirdSheet.nrows

# sort the substation by their number of neighbors
sortedMcAllenBySubs= []
for obj in grouped_by_substation:
    count=0
    subStationID=""
    sublongitude = 0.0
    sublatitude  = 0.0
    for i in obj:
        if i["Latitude"]:
            count = count + 1
            subStationID = i["SubstationNumber"]
            sublatitude += i["Latitude"]
            sublongitude += i["Longitude"]
    if(subStationID!=""):
        subDetail ={
        "SubstationID":subStationID,
        "BranchCount":count,
        "AvgLatitude":sublatitude/count,
        "AvgLongitude":sublongitude/count
        }
        sortedMcAllenBySubs.append(subDetail)


utilityCount = 7

print(len(sortedMcAllenBySubs))
lat = [o["AvgLatitude"] for o in sortedMcAllenBySubs]
lon= [m["AvgLongitude"] for m in sortedMcAllenBySubs]
A = [lat, lon]
B = [list(x) for x in zip(*A[::-1])]
X = np.array(B)
#print(X)
# Number of clusters is the number of utilities
kmeans = KMeans(n_clusters=utilityCount)
# Fitting the input data
kmeans = kmeans.fit(X)
# Getting the cluster labels
labels = kmeans.predict(X)

# Allocate substations to the utilities based on the clustering
utilityAllocatedMcAllen= []
for obj in sortedMcAllenBySubs:
    subDetail = {
        "SubstationID": obj["SubstationID"],
        "Utility":labels[sortedMcAllenBySubs.index(obj)]+1,  #since the label are allocated from 0 we add 1
        "BranchCount": obj["BranchCount"],
        "AvgLatitude": obj["AvgLatitude"],
        "AvgLongitude": obj["AvgLongitude"]
    }
    utilityAllocatedMcAllen.append(subDetail)

utilitygroups = defaultdict(list)
for obj in utilityAllocatedMcAllen:
    utilitygroups[obj["Utility"]].append(obj)
subGroupedByUtility = utilitygroups.values()
print(subGroupedByUtility)

# from hereon we will be start adding nodes and links for the communication model at substation level first

# Every Utility will have their own WAN.. each utility will have a router that connects to all the substations under it
# through different ways of communication i.e. SONET, WiFi and Cellular, there can be Power Line Carrier Communication
Nodes=[]; Links=[]; LinkType =["microwave", "sonet", "cellular","plc"];
for obj in subGroupedByUtility:
  for utility in obj:
    router = {
        "id": "Router_" + str(utility["Utility"]),
        "type": "router",
        "ips": "10.0.0.4",  # this will be actually list of IPs based on the number of interfaces it has
        "table":"" # this would have the routing table for that router. It will be also a list
    }
  Nodes.append(router)
  for substation in obj:
        firewall = {
            "id": "Firewall_" + str(substation["SubstationID"]),
            "type": "firewall",
            "firewallType": "Serial",  # there will two types of firewall interfaces active for a subs..Serial or IP
            "ips": "10.50.50.1",  # this will be also based on number of interfaces
            "acl": ""  # it would be the list of Access Control List defined in the Firewall
        }
        Nodes.append(firewall)
        # substation firewall cum router to utility router
        routerLinks = {
            "source": firewall["id"],
            "target": router["id"],
            "linkType": str(LinkType[random.randint(0,len(LinkType)-1)]),
            "dataRate": 2000000  # for example 2 Mbps
        }
        switch = {
            "id": "Switch_" + str(substation["SubstationID"]),
            "type": "switch",
            "ips": "10.50.50.1"  # this will be also based on number of interfaces
        }
        Nodes.append(switch)
        switchToFirewallLink ={
            "source": switch["id"],
            "target": firewall["id"],
            "dataRate": 2000000  # for example 2 Mbps
        }
        # Add 2 to 3 cyber host and 4 to 5 relays in each substation..number of relay can be fetched from the power
        # Power system case directly
        cyberHosts = random.randint(2,3)
        relays = random.randint(4,5)
        for i in range(cyberHosts):
            cyberHost = {
            "id": "host_" +str(substation["SubstationID"])+"_"+str(i+1),
            "type": "host",
            "hostType": "database server",   # there can be multiple type of devices
            "ip": "10.50.50.1",  # this will be also based on number of interfaces
            "port": []   # all the ports will be depended on the services running
            }
            Nodes.append(cyberHost)
            cyberLinkToSwitch = {
                "source": cyberHost["id"],
                "target": switch["id"],
                "dataRate": 2000000    #for example 2 Mbps
            }
            Links.append(cyberLinkToSwitch)

        for r in range(relays):
            relay = {
            "id": "relay_" +str(substation["SubstationID"])+"_"+str(r+1),
            "type": "relay",
            "relayType": "OC",   # OC or D OC is over current relay, D is distance relay
            "ip": "10.50.50.1",  # this will be also based on number of interfaces
            "port": []
            }
            Nodes.append(relays)
            relayLinkToSwitch = {
                "source": relay["id"],
                "target": switch["id"],
                "dataRate": 2000000  # for example 2 Mbps
            }
            Links.append(relayLinkToSwitch)


# Add the communication model between the ERCOT and utility WAN
'''
Example: Relay communication in substation X with the Main Control Center (let say Ercot Taylor in our case) 

||********|| ICCP **********    ********   ICCP over   ********     **********     ||********||
|          |<---> |Firewall|<-->|Router| <-----------> |Router|<--->|Firewall|<--->|          |
|  ERCOT   |      **********    ********      MPLS     ********     **********     | UTILITY  |
|  Taylor  |                                                                       |   EMS    |
|          |                                                                       |  ICCP    |
|  ICCP    | ICCP **********    ********   ICCP over   ********     **********     |  Client/ |
|  Server/ |<---> |Firewall|<-->|Router| <------------>|Router|<--->|Firewall|<--->|  Server  |
|  Client  |      **********    ********      DACS     ********     **********     ||********|| 
||********||

'''


# In our case we modelled lets say the cluster size as 7, we would have that many utility WAN
emsCenterERCOT = 2 # Taylor and Austin
for ems in range(emsCenterERCOT):
    routerMPLS = {
        "id": "Router_MPLS_" + str(ems),
        "type": "router",
        "ips": "10.50.50.1",  # this will be also based on number of interfaces
        "table":""  # this would have the routing table for that router. It will be also a list
    }
    routerDACS = {
        "id": "Router_DACS_" + str(ems),
        "type": "router",
        "ips": "10.50.50.1",  # this will be also based on number of interfaces
        "table":""  # this would have the routing table for that router. It will be also a list
    }
    firewallMPLS = {
        "id": "Firewall_MPLS_" + str(ems),
        "type": "firewall",
        "firewallType": "ip",  # there will two types of firewall interfaces active for a subs..Serial or IP
        "ips": "10.50.50.1",  # this will be also based on number of interfaces
        "acl": ""  # it would be the list of Access Control List defined in the Firewall
    }
    firewallDACS = {
        "id": "Firewall_DACS_" + str(ems),
        "type": "firewall",
        "firewallType": "dacs",  # there will two types of firewall interfaces active for a subs..Serial or IP
        "ips": "10.50.50.1",  # this will be also based on number of interfaces
        "acl": ""  # it would be the list of Access Control List defined in the Firewall
    }
    Nodes.append(routerMPLS)
    Nodes.append(routerDACS)
    Nodes.append(firewallMPLS)
    Nodes.append(firewallDACS)
    routerLinkToFirewallMPLS = {
        "source": routerMPLS["id"],
        "target": firewallMPLS["id"],
        "dataRate": 2000000  # for example 2 Mbps
    }
    routerLinkToFirewallDACS = {
        "source": routerDACS["id"],
        "target": firewallDACS["id"],
        "dataRate": 2000000  # for example 2 Mbps
    }
    Links.append(routerLinkToFirewallMPLS)
    Links.append(routerLinkToFirewallDACS)

    # add a switch to the firewalls to attach the ICCP client and server for each utility in the ERCOT EMS
    switchERCOT = {
        "id": "Switch_ERCOT_" + str(ems),
        "type": "switch",
        "ips": "10.50.50.1"  # this will be also based on number of interfaces
    }
    Nodes.append(switchERCOT)
    switchLinkToMPLSFirewall ={
            "source": switchERCOT["id"],
            "target": firewallMPLS["id"],
            "dataRate": 2000000  # for example 2 Mbps
        }
    switchLinkToDACSFirewall = {
        "source": switchERCOT["id"],
        "target": firewallDACS["id"],
        "dataRate": 2000000  # for example 2 Mbps
    }
    Links.append(switchLinkToMPLSFirewall)
    Links.append(switchLinkToDACSFirewall)

    for eachUtilityWAN in range(utilityCount):
        routerMPLSUtility = {
            "id": "Router_MPLS_" + str(ems)+"_"+str(eachUtilityWAN),
            "type": "router",
            "ips": "10.50.50.1",  # this will be also based on number of interfaces
            "table":""  # this would have the routing table for that router. It will be also a list
        }
        routerDACSUtility = {
            "id": "Router_DACS_" + str(ems)+"_"+str(eachUtilityWAN),
            "type": "router",
            "ips": "10.50.50.1",  # this will be also based on number of interfaces
            "table": ""  # this would have the routing table for that router. It will be also a list
        }
        firewallMPLSUtility = {
            "id": "Firewall_MPLS_" + str(ems)+"_"+str(eachUtilityWAN),
            "type": "firewall",
            "firewallType": "ip",  # there will two types of firewall interfaces active for a subs..Serial or IP
            "ips": "10.50.50.1",  # this will be also based on number of interfaces
            "acl": ""  # it would be the list of Access Control List defined in the Firewall
        }
        firewallDACSUtility = {
            "id": "Firewall_DACS_" + str(ems)+"_"+str(eachUtilityWAN),
            "type": "firewall",
            "firewallType": "dacs",  # there will two types of firewall interfaces active for a subs..Serial or IP
            "ips": "10.50.50.1",  # this will be also based on number of interfaces
            "acl": ""  # it would be the list of Access Control List defined in the Firewall
        }
        Nodes.append(routerMPLSUtility)
        Nodes.append(routerDACSUtility)
        Nodes.append(firewallMPLSUtility)
        Nodes.append(firewallDACSUtility)
        routerLinkToFirewallMPLSUtility = {
            "source": routerMPLSUtility["id"],
            "target": firewallMPLSUtility["id"],
            "dataRate": 2000000  # for example 2 Mbps
        }
        routerLinkToFirewallDACSUtility = {
            "source": routerDACSUtility["id"],
            "target": firewallDACSUtility["id"],
            "dataRate": 2000000  # for example 2 Mbps
        }
        Links.append(routerLinkToFirewallMPLSUtility)
        Links.append(routerLinkToFirewallDACSUtility)

        # create links between the routers at ERCOT end and utility end
        interRouterLinkMPLS = {
            "source": routerMPLSUtility["id"],
            "target": routerMPLS["id"],
            "type": "mpls",
            "dataRate": 2000000  # for example 2 Mbps
        }
        interRouterLinkDACS = {
            "source": routerDACSUtility["id"],
            "target": routerDACS["id"],
            "type": "dacs",
            "dataRate": 2000000  # for example 2 Mbps
        }
        Links.append(interRouterLinkMPLS)
        Links.append(interRouterLinkDACS)

        # create ICCP client and server in the utility as well as ERCOT side and attach to their switches
        switchUtility = {
            "id": "Switch_ERCOT_" + str(ems)+"_"+str(eachUtilityWAN),
            "type": "switch",
            "ips": "10.50.50.1"  # this will be also based on number of interfaces
        }
        Nodes.append(switchUtility)
        switchLinkToMPLSFirewallUtility = {
            "source": switchUtility["id"],
            "target": firewallMPLSUtility["id"],
            "dataRate": 2000000  # for example 2 Mbps
        }
        switchLinkToDACSFirewallUtility = {
            "source": switchUtility["id"],
            "target": firewallDACSUtility["id"],
            "dataRate": 2000000  # for example 2 Mbps
        }
        Links.append(switchLinkToMPLSFirewallUtility)
        Links.append(switchLinkToDACSFirewallUtility)

        # add them only once
        if (ems == 1):
            iccpNodeERCOT = {
            "id": "host_" +str(ems)+"_"+str(eachUtilityWAN),
            "type": "host",
            "hostType": "iccp",   # there can be multiple type of devices
            "ip": "10.50.50.1",  # this will be also based on number of interfaces
            "port": []   # all the ports will be depended on the services running
            }
            iccpNodeUtility = {
            "id": "host_iccp_"+str(eachUtilityWAN),
            "type": "host",
            "hostType": "iccp",   # there can be multiple type of devices
            "ip": "10.50.50.1",  # this will be also based on number of interfaces
            "port": []   # all the ports will be depended on the services running
            }
            Nodes.append(iccpNodeERCOT)
            Nodes.append(iccpNodeUtility)

            iccpLinkToSwitchUtility = {
            "source": iccpNodeUtility["id"],
            "target": switchUtility["id"],
            "dataRate": 2000000  # for example 2 Mbps
            }
            iccpLinkToSwitchERCOT = {
            "source": iccpNodeERCOT["id"],
            "target": switchERCOT["id"],
            "dataRate": 2000000  # for example 2 Mbps
            }

            Links.append(iccpLinkToSwitchERCOT)
            Links.append(iccpLinkToSwitchUtility)

# Create Graph
graphJson = [{
            "directed": False,
            "graph": {},
            "nodes": json.dumps(Nodes),
            "links": json.dumps(Links),
            "multigraph": False
}]
modelFile = open("commModelwithERCOT.json","w")
modelFile.write(json.dumps(graphJson))
modelFile.close


# Each utilities connection with ERCOT EMS...ERCOT cyber components model



print(mcAllenBusList[29])

#puts the mcAllenBusList into a mcAllen dict
#mcAllen = {
       # "McAllen": mcAllenBusList
        #}
#converts dict to JSON string
JSONstr = json.dumps(mcAllenBusList)

#print(JSONstr)
print("Number of Busses Added:"+str(count))

outputFile = open("JSONOutputFile4.txt","w")
outputFile.write(JSONstr)
outputFile.close
