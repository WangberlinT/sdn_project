"""Example Topology Manager Template
CSCI1680

This class is meant to serve as an example for how you can track the
network's topology from netwokr events.

**You are not required to use this file**: feel free to extend it,
change its structure, or replace it entirely.

"""

from ryu.topology.switches import Port, Switch, Link

class Device():
    """Base class to represent an device in the network.

    Any device (switch or host) has a name (used for debugging only)
    and a set of neighbors.
    """
    def __init__(self, name):
        self.name = name
        self.neighbors = set()
        self.father = None

    def add_neighbor(self, dev):
        self.neighbors.add(dev)

    def get_neighbors(self):
        return self.neighbors
    
    def remove_neighbor(self,device):
        self.neighbors.remove(device)

    def setFather(self,father):
        self.father = father

    def cleanFather(self):
        self.father = None

    def __str__(self):
        return "{}({})\nneighbors:{}".format(self.__class__.__name__,
                               self.name, self.get_neighbors())


class TMSwitch(Device):
    """Representation of a switch, extends Device

    This class is a wrapper around the Ryu Switch object,
    which contains information about the switch's ports
    """

    def __init__(self, name, switch):
        super(TMSwitch, self).__init__(name)

        self.switch = switch
        # pm_table : Port-Mac pair
        self.pm_table = {}
        # TODO:  Add more attributes as necessary

    def get_dpid(self):
        """Return switch DPID"""
        return self.switch.dp.id

    def get_ports(self):
        """Return list of Ryu port objects for this switch
        """
        return self.switch.ports

    def get_dp(self):
        """Return switch datapath object"""
        return self.switch.dp

    def set_pm_table(self, port, mac):
        self.pm_table[mac] = port

    def get_link_port(self, mac):
        return self.pm_table[mac]
        
    def topo_str(self):
        return super(TMSwitch, self).__str__(self)

    def __str__(self):
        return "switch{}".format(self.get_dpid())

    def del_pm_link(self, mac): 
         del self.pm_table[mac]



class TMHost(Device):
    """Representation of a host, extends Device

    This class is a wrapper around the Ryu Host object,
    which contains information about the switch port to which
    the host is connected
    """

    def __init__(self, name, host):
        super(TMHost, self).__init__(host)

        self.host = host

    def get_mac(self):
        return self.host.mac

    def get_ips(self):
        return self.host.ipv4

    def get_port(self):
        """Return Ryu port object for this host"""
        return self.host.port
    
    def topo_str(self):
        return super(TMHost, self).__str__(self)

    def __str__(self):
        return "Host "+self.get_ips()[0]


class TopoManager():
    """
    Example class for keeping track of the network topology

    """
    def __init__(self):
        # TODO:  Initialize some data structures
        self.all_devices = []
        self.ARPTable = {}; # store the ip address : Mac address pair

    def add_switch(self, switch):
        self.all_devices.append(switch)

    def add_host(self, host):
        self.all_devices.append(host)
        self.addARPTable(host)

    def find_switch_by_port(self,port):
        for device in self.all_devices:
            if isinstance(device,TMSwitch):
                 if port in device.get_ports():
                    return device
    
    def find_tmswitch_by_dpid(self,dpid):
        for device in self.all_devices:
            if isinstance(device,TMSwitch):
                if device.get_dpid() == dpid:
                    return device

    def find_host_by_mac(self,mac):
        for device in self.all_devices:
            if isinstance(device,TMHost):
                if device.get_mac == mac:
                    return device

    def addARPTable(self,host):
        iplist = host.get_ips()
        macobj = host.get_mac()
        for i in range(0,len(iplist)):
            self.ARPTable[iplist[i]] = macobj

    def deleteSwitch(self,switch):
        self.all_devices.remove(switch)
        print("remove:%s"%(switch))
        for device in self.all_devices:
            if switch in device.get_neighbors():
                device.remove_neighbor(switch)
            print("device: %s"%(device))
                
