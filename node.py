#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 18 12:49:26 2019

@author: patrickw
"""

class regulatory():
    
    def __init__(self, region, utilities):
        self.region = region
        self.utilities = utilities
        
        self.id = "{}".format(region)
        
        self.nodes = []
        self.links = []
        
        #creates and connects an 1-ICCP Server, 1-Firewall, and 1-Regulaotry Router for the regulaotry agency
        self.ICCPServer = cyberNode(self.region,"", "10.10.10.10", str(self.region)+"_Regulatory_ICCP", "Regulaory", "")
        self.ICCPFirewall = firewall(self.region, "", "10.10.10.10", str(self.region)+"_Regulatory_Firewall", "Regulatory", "", "", "", "")
        self.regulatoryRouter = router(self.region, "", "10.10.10.10", str(self.region)+"_Regulatory_Router", "Regulatory", "", "")
        
        self.nodes.extend([self.ICCPServer,self.ICCPFirewall,self.regulatoryRouter])
        
        linkICCPServertoICCPFirewall = link(self.ICCPServer.id,self.ICCPFirewall.id,"serial",10000000,10)
        linkICCPFirewalltoRegRouter = link(self.ICCPFirewall.id,self.regulatoryRouter.id,"serial",10000000,10)
        
        self.links.extend([linkICCPServertoICCPFirewall,linkICCPFirewalltoRegRouter])
        
        #creates and connects the Regulaotry Router to each of the Ultility Routers
        for utility in self.utilities:
            utilityRouter = router(self.region, utility, "10.10.10.10", str(self.region)+"_Regulatory_Router", "Regulatory", "", "")
            
            self.nodes.extend([utilityRouter])
            
            linkRegRoutertoUtlRouter = link(self.regulatoryRouter.id,utilityRouter.id,"fiber",10000000,100)
            
            self.links.extend([linkRegRoutertoUtlRouter])
            
            
    def printLinks(self):
        for link in self.links:
            print(link.toJSONStr())
            
    def printNodes(self):
        for node in self.nodes:
            print(node.toJSONStr())
        

class utility():
    
    def __init__(self,region,utility,substations):
        self.region = region
        self.utility = utility
        self.substations = substations
        
        self.id = "{}.{}".format(self.region,self.utility)
        
        self.nodes = []
        self.links = []
        
        #creates a utllity 1-Router and 1-Firewall for the utlity
        self.utilityRouter = router(self.region, self.utility, "10.10.10.10", str(self.utility)+"_Utility_Router", "IT", "", "")
        self.utilityFirewall = firewall(self.region, self.utility, "10.10.10.10", str(self.utility)+"_Utility_Firewall", "IT", "", "", "", "")
        
        self.nodes.extend([self.utilityFirewall,self.utilityRouter])
        
        linkUtlRoutertoUtlFirewall = link(self.utilityRouter.id,self.utilityFirewall.id,"serial",10000000,10)
        
        self.links.extend([linkUtlRoutertoUtlFirewall])
        
        #creates and connects: 1-EMS, 1-EMS Firewall, 1-Router, and 1-On-Site (substation) firewall for each substation
        for substation in substations:
            substationEMS = cyberNode(self.region,self.utility, "10.10.10.10", str(substation)+"_Substation_EMS", "IT", "")
            substationFirewall = firewall(self.region, self.utility, "10.10.10.10", str(substation)+"_Substaion_Firewall", "IT", "", "", "", "")
            substationRouter = router(self.region, self.utility, "10.10.10.10", str(substation)+"_Substation_Router", "IT", "", "")
            substationOnSiteFirewall =  firewall(self.region, self.utility, "10.10.10.10", str(substation)+"_Substaion_Firewall", "IT", "", "", "", "")
            
            self.nodes.extend([substationFirewall,substationRouter,substationEMS, substationOnSiteFirewall])
            
            linkUtlFirewalltoEMS = link(self.utilityFirewall.id,substationEMS.id,"serial",10000000,10)
            linkSubEMStoFirewall = link(substationEMS.id,substationFirewall.id,"serial",10000000,10)
            linkSubFirewalltoSubRouter = link(substationFirewall.id,substationRouter.id,"serial",10000000,10)
            linkSubRoutertoOnSiteFirewall = link(substationRouter.id,substationOnSiteFirewall.id,"fiber",10000000,100)
            
            self.links.extend([linkUtlFirewalltoEMS,linkSubEMStoFirewall,linkSubFirewalltoSubRouter,linkSubRoutertoOnSiteFirewall])
            
    # adds a new DMZFirewall that faces the internet, a new Web Server (Cyber Node), and links the DMZFirewall to the Web Server, and the Web Server to the Utility EMS Firewall
    def addDMZ(self,adminIP,ports):
        self.DMZFirewall = firewall(self.region, self.utility, "10.10.10.10", str(self.utlity)+"_DMZ_Firewall", "DMZ", "", "", "", "")
        newWebServer = cyberNode(self.region,self.utility, adminIP, str(self.utlity)+"_Utility_Web_Server", "DMZ", ports)
            
        self.nodes.extend([self.DMZFirewall,newWebServer])
            
        linkUtlFirewalltoWebServer = link(self.utilityFirewall,newWebServer.id,"serial",1000000,10)
        linkDMZFirewalltoWebServer =  link(self.DMZFirewall.id,newWebServer.id,"serial",10000000,10)
            
        self.links.extend([linkUtlFirewalltoWebServer,linkDMZFirewalltoWebServer])
    
    def printLinks(self):
        for link in self.links:
            print(link.toJSONStr())
            
    def printNodes(self):
        for node in self.nodes:
            print(node.toJSONStr())
            

class substation():
    
    def __init__(self,region,utility,substation):
        self.region = region
        self.utility = utility
        self.substation = substation
        
        self.nodes = []
        self.links = []
        
        self.switches = []
        self.relayControllers = []
        
        self.id = "{}.{}.{}".format(region,utility,substation)
        
        self.genericSubstation()
        
    def genericSubstation(self):
        #creates a generic substation with: 1-Firewall, 1-Switch, 1-RelayController, and 2-Relay. 
        #Functions underneath will allow to add more Switches, Relays, and Cyber Nodes to the substation.
        self.substationFirewall = firewall(self.region, self.utility, "10.10.10.10", str(self.substation)+"_Substaion_Firewall", "OT", "", "", "", "")
        self.substationSwitch = switch(self.region, self.utility, "10.10.10.10", str(self.substation)+"_Substation_Switch_OT", "OT", "")
        self.substationRelayController = relayController(self.region, self.utility, self.substation, "10.10.10.10", str(self.substation)+"_Substation_Relay_Controller", "OT", "")
        self.substationRelay1 = relay(self.region, self.utility,self.substation, "10.10.10.10", str(self.substation)+"_Substation_Relay", "OT", "", "")
        self.substationRelay2 = relay(self.region, self.utility, self.substation,"10.10.10.10", str(self.substation)+"_Substation_Relay", "OT", "", "")
        
        #generic substation nodes added to the nodes[] list
        self.nodes.extend([self.substationFirewall,self.substationSwitch,self.substationRelayController,self.substationRelay1,self.substationRelay2])
        
        #adds to switches[] list so that Relay Conroller and Cyber Nodes can be added to Switch based on the Switches VLAN
        self.switches.append(self.substationSwitch)
        #adds to relayControllers[] list so that Relays and Cyber Nodes can be added a specific Relay Controller based on the ther Relay Controllers id
        self.relayControllers.append(self.substationRelayController)
        
        #creates a generic link for the subsation: Firewall to Swtich, Switch to Relay Controller, Relay Controller to Relay1, and Relay Cotnroller to Relay2
        linkFirewalltoSwitch = link(self.substationFirewall.id,self.substationSwitch.id,"serial",10000000,10)
        linkSwitchtoRelayController = link(self.substationSwitch.id,self.substationRelayController.id,"serial",10000000,10)
        linkRelayControllertoRelay1 = link(self.substationRelayController.id,self.substationRelay1.id,"serial",10000000,10)
        linkRelayControllertoRelay2 = link(self.substationRelayController.id,self.substationRelay2.id,"serial",10000000,10)
        
        #generic links added to links[] list
        self.links.extend([linkFirewalltoSwitch,linkSwitchtoRelayController,linkRelayControllertoRelay1,linkRelayControllertoRelay2])
        
    #adds a new node and link for new Relay to the already exsisting Relay Controller in __init__() function
    #addRelay parameters: adminIP (), busNumber (bus number the relay is on), and relayType ('load' or 'transmission' relay)
    def addRelay(self, adminIP,busNumber,relayType):
        newRelay = relay(self.region, self.utility, self.subStation, adminIP, str(self.substation)+"_Substation_Relay", "OT", busNumber, relayType)
        
        self.nodes.append(newRelay)
        
        linkRelayControllertoNewRelay = link(self.substationRelayController.id,newRelay.id,"serial",10000000,10)
        
        self.links.append(linkRelayControllertoNewRelay)
       
    #adds a new node and link for new Switch to the already exsisting Relay Controller in __init__() function
    #addRelay parameters: adminIP (), vlan (vlan the new Switch connects to the firewall), and macTable (MAC Table of the switch)    
    def addSwitch(self, adminIP, vlan, macTable):
        newSwitch = switch(self.region, self.utility, adminIP, str(self.substation)+"_Substation_Switch_"+str(vlan), vlan, macTable)
        
        self.nodes.append(newSwitch)
        
        linkFirewalltoNewSwitch = link(self.substationFirewall.id,newSwitch.id,"serial",1000000,10)
        
        self.links.append(linkFirewalltoNewSwitch)
        
        
    def addCyberNode(self, adminIP, typ, vlan, ports):
        newCyberNode = cyberNode(self.region,self.utility, adminIP, str(self.substation)+typ, vlan, ports)
        
        self.nodes.append(newCyberNode)
        
        # if there is a Switch with that VLAN, then add new Cyber Node to that VLAN
        for switch in self.switches:
            if switch.vlan == vlan:
                linkSwitchtoCyberNode = link(switch.id,newCyberNode.id,"serial",1000000,10)
                
                self.links.append(linkSwitchtoCyberNode)
                return
        
        #if there is not Switch with that VLAN, then create a new Switch with the VLAN
        newSwitch = switch(self.region, self.utility, adminIP, str(self.substation)+"_Substation_Switch_"+str(vlan), vlan, "")
        
        self.nodes.append(newSwitch)
        
        linkFirewalltoNewSwitch = link(self.substationFirewall.id,newSwitch.id,"serial",1000000,10)
        
        self.links.append(linkFirewalltoNewSwitch)
        
        linkSwitchtoCyberNode = link(newSwitch.id,newCyberNode.id,"serial",1000000,10)
        
        self.links.append(linkSwitchtoCyberNode)
        
    def printLinks(self):
        for link in self.links:
            print(link.toJSONStr())
            
    def printNodes(self):
        for node in self.nodes:
            print(node.toJSONStr())
            
        
#link is a parent class with the parameters: src (source node), dst (destitation node), typ (type of link), bdw (bandwidth of link), and dist (distance of link)
class link():
    def __init__(self, src, dst, typ, bdw, dist):
        self.src = src
        self. dst = dst
        self.type = typ
        self.bandwidth = bdw
        self.distance = dist
        
    def toJSONStr(self):
        newLink = {
                "source": self.src,
          "destintation": self.dst,
                  "type": self.type,
             "bandwidth": self.bandwidth,
              "distance": self.distance
                }
        return newLink

#node is a parent class with the parameters: region (regularoy agency), utility (utility number), adminIP (IP used to remotely configure node), label (condensed description of node), and vlan (vlan node is on)
class node:
    def __init__(self,region, utility, adminIP,label,vlan):
        self.adminIP = adminIP
        self.label = label
        self.vlan = vlan
        
        self.id = "{}.{}.0.{}.0".format(region,utility,vlan)
        
    def __str__(self):
        return self.id
    
    def __add__(self,other):
        connectingLink = link(self.id, other.id, "serial", "1000000", "100")
        return connectingLink
        
        
#cyberNode is a subclass of node with an additional parameter: ports (used to store the application ports that are open on the device)
class cyberNode(node):
    def __init__(self,region, utility, adminIP, label, vlan, ports):
        super().__init__(region, utility, adminIP, label, vlan)
        self.ports = ports
        
        self.id = "{}.{}.0.{}.".format(region,utility,vlan)
        
    def toJSONStr(self):
         newCyberNode = {
                 "id": self.id,
              "label": self.label,
           "admin_IP": self.adminIP,
               "VLAN": self.vlan
            }
         return newCyberNode
     
#switch is a subclass of node with an additional parameter: macTable (used to store the mac address of the devices connect to the Switch)
class switch(node):
    def __init__(self,region, utility, adminIP, label, vlan, macTable):
        super().__init__(region, utility, adminIP, label, vlan)
        self.macTable = macTable
        
        self.id = "{}.{}.1.{}.".format(region,utility,vlan)
        
    def toJSONStr(self):
         newSwitchNode = {
                 "id": self.id,
              "label": self.label,
           "admin_IP": self.adminIP,
               "VLAN": self.vlan,
          "MAC_table": self.macTable
            }
         return newSwitchNode
     
#router is a subclass of node with an additional parameters: interfaces (connected interfaces) and routerTable (router table information)
class router(node):
    def __init__(self,region, utility, adminIP, label, vlan, interfaces, routerTable):
        super().__init__(region, utility, adminIP, label, vlan)
        self.interfaces = interfaces
        self.routerTable = routerTable
        
        self.id = "{}.{}.1.{}.".format(region,utility,vlan)
        
    def toJSONStr(self):
         newRouterNode = {
                 "id": self.id,
              "label": self.label,
           "admin_IP": self.adminIP,
               "VLAN": self.vlan,
         "interfaces": self.interfaces,
       "router_table": self.routerTable
            }
         return newRouterNode
    
#relay is a subclass of node with an additional parameters: busNumber (Bus Number for relay) and relayType (load or transfer relay)
class relay(node):
    def __init__(self,region, utility, subStation, adminIP, label, vlan, busNumber, relayType='load'):
        super().__init__(region, utility, adminIP, label, vlan)
        self.busNumber = busNumber
        self.relayType = relayType
        self.subStation = subStation
        
        self.id = "{}.{}.{}.{}.".format(region,utility,subStation,vlan)
        
    def toJSONStr(self):
         newRelayNode = {
                 "id": self.id,
              "label": self.label,
           "admin_IP": self.adminIP,
               "VLAN": self.vlan,
         "bus_number": self.busNumber,
       "router_table": self.relayType
            }
         return newRelayNode

#RTU (remote terminal unit) is a subclass of node with an additional parameter: breakerList (list of breakers)
class RTU(node):
    def __init__(self,region, utility, subStation, adminIP, label, vlan, breakerList):
        super().__init__(region, utility, adminIP, label, vlan)
        self.breakerList = breakerList
        self.subStation = subStation
        
        self.id = "{}.{}.{}.{}.".format(region,utility,subStation,vlan)
        
    def toJSONStr(self):
         newRTUNode = {
                 "id": self.id,
              "label": self.label,
           "admin_IP": self.adminIP,
               "VLAN": self.vlan,
         "breakers": self.breakerList
            }
         return newRTUNode
        
#firewall is a subclass of node with an additional parameters: interfaces (lused interfaces), acl (access control list), lat (latitude), and lon (longitude)
class firewall(node):
    def __init__(self,region, utility, adminIP, label, vlan, interfaces, acl, lat, lon):
        super().__init__(region, utility, adminIP, label, vlan)
        self.interfaces = interfaces
        self.acl = acl
        self. lat = lat
        self.lon = lon
        
        self.id = "{}.{}.1.{}.".format(region,utility,vlan)
        
    def toJSONStr(self):
         newFirewallNode = {
                 "id": self.id,
              "label": self.label,
           "admin_IP": self.adminIP,
               "VLAN": self.vlan,
           "latitude": self.lat,
          "longitude": self.lon,
         "interfaces": self.interfaces,
                "acl": self.acl
            }
         return newFirewallNode
     
#relayController is a subclass of node with an additional parameter: relayIPList (list of IP address for attached relays)
class relayController(node):
    def __init__(self,region, utility, subStation, adminIP, label, vlan, relayIPList):
        super().__init__(region, utility, adminIP, label, vlan)
        self.subStation = subStation
        self.relayIPList = relayIPList
        
        self.id = "{}.{}.{}.{}.".format(region,utility,subStation,vlan)
        
    def toJSONStr(self):
         newRelayControllerNode = {
                 "id": self.id,
              "label": self.label,
           "admin_IP": self.adminIP,
               "VLAN": self.vlan,
      "relay_IP_List": self.relayIPList
            }
         return newRelayControllerNode
        
nodeA = cyberNode('ERCOT',"LIDOS",'10.10.12.1','ICCP_Server','corporate','12')
nodeB = cyberNode('ERCOT',"Benjiman",'10.10.12.1','ICCP_Server','corporate','12')

linkA = nodeA+nodeB
print(linkA.toJSONStr())
print(nodeA.toJSONStr())

print("---------")

substationA = substation("ERCOT","McAllen",273)

substationA.printNodes()
substationA.printLinks()
    
print("---------")
    
utilityA = utility("ERCOT","McAllen",[500,300,200,100])


utilityA.printNodes()
utilityA.printLinks()
    
print("---------")
    
regulatoryA = regulatory("ERCOT", ["McAllen","Houston","College Station"])

regulatoryA.printNodes()
regulatoryA.printLinks()
