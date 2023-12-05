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

||********|| DNP3 **********    ********       *******                     *****************
|          |<---> |Firewall|<-->|Router|<----->|Wi-Fi|<----WiFi link------>|Serial FW Sub A|
| UTILITY  |      **********    ********       *******                     *****************
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
import os
import xlrd
import random
import string

#get input substation data from excel
cwd = os.getcwd()

#If output folder does not exist then create one
if not os.path.exists(os.path.join(cwd, '../Output\\')):
    os.makedirs(os.path.join(cwd, '../Output\\'))
output_folder = os.path.join(cwd, '../Output\\')

#Function generates a random universial device number
def randUUIN():
    return (random.randint(1, 99999))
    

#Function is used to add a new node to the utilityNodes list
#Parameters: label = human name, utility = utility provider number, substation_number = substation number, typ = type of node, ipv4 = IP address, VLAN = whose VLAN, OSILayer = highest OSI_Layer of device
def newNode(label,utility,subNum,typ,ipv4, vlan, OSILayer, Attr):
    #Create a new node
    node = {
            "id":str(utility)+"."+str(subNum)+"."+str(vlan)+"."+str(randUUIN()),
            "label": label,
            "utility": utility,
            "substation_number": subNum,
            "type": typ,
            "ipv4": ipv4,
            "VLAN": vlan,
            "OSI_layer": OSILayer
            }
    #Add any specific attributes the node needs 
    if len(Attr)<2: return node
    Attribute = Attr.split(',')
    for it in Attribute:
        keyValue = it.split(':')
        node[keyValue[0]] = keyValue[1]
    #Add new node to list of Nodes
    return node
    
#Function is used to new links to the ultilityLinks list
#Parameters: src = source of connection, trg = target of connection, type = type of connection, bandwidth = connection bandwidth in bps
def newLink(src,trg,typ,bdwdth):
    #create a new node
    link = {
            "source":src,
            "target":trg,
            "type": typ,
            "bandwidth": bdwdth
            }
    #Add new link to list of Links
    return link

#Function is used to print a List to a file
# parameters: outputList = list of files to print to file, filePath = file path for file to be written to
def writeToFile(outputList, filePath):
    modelFile = open(filePath+".json","w")
    modelFile.write(json.dumps(outputList))
    modelFile.close()

#utilityNum = 1
#substationNumbers = [290,293,512] #get substation information from Excel or JSON

#Function is used to create a typical network mapping of a substation
# parameters: substationNumbers = list of substation number for a utility, utilityNumber = number assigned for that utility
def generateSubstationLevel(substationNumbers,utilityNumber):
    substationNodes = []
    substationLinks = []
    #substationNodes = [1,2,3,4,5,6]
    #substationLinks = [1,2,3,4]
    
    for subNum in substationNumbers:

        subFirewall = newNode(str(subNum)+"_firewall",utilityNumber,subNum,"firewall","10.10.10.1",1,7,"acl: ")
        subSwitch = newNode(str(subNum)+"_switch",utilityNumber,subNum,"switch","10.10.10.2",1,2,"table: ")
        subRTU = newNode(str(subNum)+"_RTU",utilityNumber,subNum,"rtu","10.10.10.3",1,2,"table: ")
        subRelayA = newNode(str(subNum)+"_relay",utilityNumber,subNum,"relay","10.10.10.4",1,3,"")
        subRelayB = newNode(str(subNum)+"_relay",utilityNumber,subNum,"relay","10.10.10.5",1,3,"")
        #subRelayC = newNode(str(subNum)+"_relay",utilityNumber,subNum,"relay","10.10.10.6",1,3,"")

    
        substationNodes.extend([subFirewall,subSwitch,subRelayA,subRelayB])
    
        linkFirewalltoSwitch = newLink(subFirewall["id"],subSwitch["id"],"serial",10000000)
        linkSwitchtoRTU = newLink(subSwitch["id"],subRTU["id"],"serial",10000000)
        linkRTUtoRelayA = newLink(subRTU["id"],subRelayA["id"],"serial",10000000)
        linkRTUtoRelayB = newLink(subRTU["id"],subRelayB["id"],"serial",10000000)
    
        substationLinks.extend([linkFirewalltoSwitch,linkSwitchtoRTU,linkRTUtoRelayA,linkRTUtoRelayB])
    
        writeToFile(substationNodes+substationLinks,os.path.join(output_folder,(str(subNum)+"_substation")))      #write nodes and links to a file; one file per substaion
    
        #ClearNodes and Links for next substation
        substationNodes = []
        substationLinks = []

#Function is used to create a mapping of the utility internal network with the link from utility to the substation
#   parameters: substationNumbers = list substation numbers within a utility, utilityNumbers = list of utility numbers 
def generateUtilityLevel(substationNumbers, utilityNumbers):
    utilityNodes = []
    utilityLinks = []
    #utilityNodes = [1,2,3,4,5,6]
    #utilityLinks = [1,2,3,4]
    
    for utilityNum in utilityNumbers:
    
        utilityEMS = newNode(str(utilityNum)+"_utility_EMS",utilityNumbers,0,"ems","10.10.10.254",0,7,"")         #utility EMS node
        utilityFirewall = newNode(str(utilityNum)+"_utility_Firewall",utilityNumbers,0,"firewall","10.10.10.254",0,7,"acl: ")    #utility Firewall node
        utilityRouter = newNode(str(utilityNum)+"_utility_Router",utilityNumbers,0,"router","10.10.10.254",0,3,"")      #utility Router node
    
        utilityNodes.extend([utilityEMS, utilityFirewall, utilityRouter])
    
        linkEMStoFirewall = newLink(utilityEMS["id"],utilityFirewall["id"],"ethernet",10000000)
        linkFirewalltoRouter = newLink(utilityFirewall["id"],utilityRouter["id"],"ethernet",10000000)
    
        utilityLinks.extend([linkEMStoFirewall,linkFirewalltoRouter])
    
        for subStation in substationNumbers:
            substationFirewall = newNode(str(subStation)+"_substation_Firewall",utilityNum,subStation,"ems","10.10.10.254",0,7,"acl: ")    #utility Firewall node
        
            utilityNodes.append(substationFirewall)
        
            linkUtilitytoSubstation = newLink(utilityRouter["id"],substationFirewall["id"],"sonnet",10000000)
        
            utilityLinks.append(linkUtilitytoSubstation)
    
        writeToFile(utilityNodes+utilityLinks,os.path.join(output_folder,(str(utilityNum)+"_utility")))     #write nodes and links to a file; one file per utility

        ##writeToFile(substationNodes+substationLinks,str(utilityNum)+"_utility")     #write nodes and links to a file; one file per u
        utilityNodes = []
        utilityLinks = []
    
        
        
def generateRegulatoryLevel(utilityNumbers):
    regulatoryNodes = []
    regulatoryLinks = []
    
    regulatoryICCPServer = newNode("0_regulatory_EMS",0,0,"iccp_server","50.50.50.254",0,7,"")         #regulatory EMS node
    regulatoryFirewall = newNode("0_regulatory_Firewall",0,0,"firewall","50.50.50.254",0,7,"acl: ")    #regulatory Firewall node
    regulatoryRouter = newNode("0_regulatory_Router",0,0,"router","50.50.50.254",0,3,"")               #regulatory Router node
    
    regulatoryNodes.extend([regulatoryICCPServer, regulatoryFirewall, regulatoryRouter])
    
    linkICCPtoFirewall = newLink(regulatoryICCPServer["id"],regulatoryFirewall["id"],"ethernet",10000000)
    linkFirewalltoRouter = newLink(regulatoryFirewall["id"],regulatoryRouter["id"],"ethernet",10000000)
    
    regulatoryLinks.extend([linkICCPtoFirewall,linkFirewalltoRouter])
    
    for utilityNum in utilityNumbers:
        utilityFirewall = newNode(str(utilityNum)+"_utility_Firewall",utilityNum,0,"firewall","50.50.50.254",0,7,"acl: ")    #utility Firewall node
        utilityRouter = newNode(str(utilityNum)+"_utility_Router",utilityNum,0,"router","50.50.50.254",0,3,"")               #utlity Router node
        utilityEMSServer = newNode(str(utilityNum)+"_utility_EMS",utilityNum,0,"ems_server","50.50.50.254",0,7,"")         #utility EMS node
    
        regulatoryNodes.extend([utilityFirewall, utilityRouter, utilityEMSServer])
    
        linkRoutertoRouter = newLink(regulatoryRouter["id"],utilityRouter["id"],"isp",10000000)
        linkRoutertoFirewall = newLink(utilityRouter["id"],utilityFirewall["id"],"ethernet",10000000)
        linkFirewalltoEMS = newLink(utilityFirewall["id"],utilityEMSServer["id"],"ethernet",10000000)
        
        regulatoryLinks.extend([linkRoutertoRouter,linkRoutertoFirewall,linkFirewalltoEMS])
    
    writeToFile(regulatoryNodes+regulatoryLinks,os.path.join(output_folder,"ERCOT_regulatory"))
        
        
        
