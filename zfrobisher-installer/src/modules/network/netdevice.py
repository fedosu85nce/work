#!/usr/bin/python

#
# IMPORTS
#
from controller.zkvmerror import ZKVMError
from modules.scriptbase import ScriptBase
from modules.network.network import Network

import logging
import os
import pprint
import re
import traceback

#
# CONSTANTS
#
IFCFG_FILE = "/etc/sysconfig/network-scripts/ifcfg-%s"


#
# CODE
#
class NetDevice(ScriptBase):
    """
    Represents a network interface

    IMPORTANT:
      __loadConfigFile() - Must be the first method to be executed
      setBridge() - Must be the second method to be executed
    """

    def __init__(self, name=None):
        """
        Contructor

        @type  name: string
        @param name: network interface name (default = None)
        """
        self.__logger = logging.getLogger(__name__)
        self.__ethConfigFile = {
            'DEVICE': None,
            'TYPE': 'Ethernet',
            'HWADDR': None,
            'BOOTPROTO': 'none',
            'ONBOOT': 'no',
        }
        self.__brConfigFile = {
            'DEVICE': None,
            'TYPE': 'Bridge',
            'ONBOOT': 'no',
            'BOOTPROTO': 'none',
            'NM_CONTROLLED': 'no',
            'DELAY': '0',
        }
        self.__mountDir = None
        self.__hostname = None
        self.__hasBridge = False
        if name:
            self.__loadConfigFile(name)
    # __init__()

    def __loadConfigFile(self, name):
        """
        Load previous network cfg file
        Must be executed before setBridge()

        @type  name: string
        @param name: network interface card name (NIC)
        """
        self.__ethConfigFile = self.__parseConfigFile(name)
        if self.__ethConfigFile.get('BRIDGE'):
            self.setBridge(True)
            bridge = "br%s" % name
            self.__brConfigFile = self.__parseConfigFile(bridge)
        else:
            self.setBridge(False)
    # __loadConfigFile()

    def __parseConfigFile(self, dev):
        """
        Parse IFCFG_FILE into a dictionary

        @rtype: dict
        @returns: dictionary with the content file parsed
        """
        try:
            result = {}
            ifcfgFile = IFCFG_FILE % dev
            if self.__mountDir:
                ifcfgFile = self.__mountDir + ifcfgFile

            if os.path.exists(ifcfgFile):
                with open(ifcfgFile) as fd:
                    content = fd.readlines()

                for line in content:
                    if line.startswith("#"):
                        continue

                    key, value = line.strip().split("=", 1)
                    result[key] = value
            else:
                self.__logger.critical("No previous IFCFG_FILE (%s) found" % ifcfgFile)
                raise ZKVMError("PREINSTALL", "NETDEV", "INVALID_NIC")
            return result
        except ZKVMError:
            raise
        except Exception as e:
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("PREINSTALL", "NETDEV", "PRE_MODULES")
    # __parseConfigFile()

    def setBridge(self, value=True):
        """
        Set if network bridge will be used or not.
        Must be executed after __loadConfigFile()

        @type  value: boolean
        @param value: True/False

        @rtype: None
        @returns: nothing
        """
        self.__hasBridge = value
    # setBridge()

    def hasBridge(self):
        """
        Return if network bridge is used or not.

        @rtype: boolean
        @returns: True/False
        """
        return self.__hasBridge
    # hasBridge()

    def setDNS(self):
        """
        If DNS set exist on ifcfg file move it accordingly.

        @rtype: None
        @returns: nothing
        """
        entriesMoved = []
        if self.__hasBridge:
            for k, v in self.__ethConfigFile.iteritems():
                if re.match('DNS[0-9]', k):
                    self.__brConfigFile[k] = v
                    entriesMoved.append(k)
            if entriesMoved:
                self.__logger.debug("Moving DNS entries from NIC to bridge:")
                self.__logger.debug("%s" % entriesMoved)
                for i in entriesMoved:
                    del self.__ethConfigFile[i]
        else:
            for k, v in self.__brConfigFile.iteritems():
                if re.match('DNS[0-9]', k):
                    self.__ethConfigFile[k] = v
                    entriesMoved.append(k)
            if entriesMoved:
                self.__logger.debug("Moving DNS entries from bridge to NIC:")
                self.__logger.debug("%s" % entriesMoved)
                for i in entriesMoved:
                    del self.__brConfigFile[i]
    # setDNS()

    def setDev(self, dev, macaddr):
        """
        Sets device name and mac address to the network interface and brigde if
        the last one is applicable

        @type  dev: string
        @param dev: device name
        @type  macaddr: string
        @param macaddr: mac address

        @rtype: None
        @returns: nothing
        """
        self.__ethConfigFile['DEVICE'] = dev
        self.__ethConfigFile['TYPE'] = 'Ethernet'
        if macaddr:
            self.__ethConfigFile['HWADDR'] = macaddr
        bridge = "br%s" % dev
        if self.__hasBridge:
            self.__ethConfigFile['BRIDGE'] = bridge
            self.__ethConfigFile['NM_CONTROLLED'] = 'no'
            self.__brConfigFile['DEVICE'] = bridge
            self.__brConfigFile['TYPE'] = 'Bridge'
            self.__brConfigFile['NM_CONTROLLED'] = 'no'
            self.__brConfigFile['DELAY'] = '0'
        else:
            if self.__ethConfigFile.get('BRIDGE'):
                del self.__ethConfigFile['BRIDGE']
            if self.__ethConfigFile.get('NM_CONTROLLED'):
                del self.__ethConfigFile['NM_CONTROLLED']
    # setDev()

    def setOnBoot(self, value):
        """
        Set ONBOOT parameter

        @type  value: boolean
        @param value: True/False

        @rtype: None
        @returns: nothing
        """
        if value:
            self.__ethConfigFile["ONBOOT"] = 'yes'
        else:
            self.__ethConfigFile["ONBOOT"] = 'no'
        if self.__hasBridge:
            self.__brConfigFile["ONBOOT"] = self.__ethConfigFile.get('ONBOOT')
    # setOnBoot()

    def getOnBoot(self):
        """
        Return ONBOOT state

        @rtype: boolean
        @returns: True/False
        """
        enable = False
        if self.__hasBridge:
            if self.__brConfigFile.get("ONBOOT") == 'yes':
                enable = True
        else:
            if self.__ethConfigFile.get("ONBOOT") == 'yes':
                enable = True
        return enable
    # getOnBoot()

    def enableDHCP(self, flag):
        """
        Enable/Disable DHCP configuration.

        @type  flag: boolean
        @param flag: True to enable DHCP; False otherwise

        @rtype: None
        @returns: nothing
        """
        if flag:
            if self.__hasBridge:
                self.__brConfigFile["BOOTPROTO"] = "dhcp"
                for key in ["IPADDR", "NETMASK", "GATEWAY"]:
                    if key in self.__brConfigFile.keys():
                        del self.__brConfigFile[key]
                self.__ethConfigFile["BOOTPROTO"] = "none"
            else:
                self.__ethConfigFile["BOOTPROTO"] = "dhcp"

            for key in ["IPADDR", "NETMASK", "GATEWAY"]:
                if key in self.__ethConfigFile.keys():
                    del self.__ethConfigFile[key]
        else:
            if self.__hasBridge:
                self.__brConfigFile["BOOTPROTO"] = "none"
            self.__ethConfigFile["BOOTPROTO"] = "none"
    # enableDHCP()

    def setIp(self, value):
        """
        Sets IP address to the network interface

        @type  value: string
        @param value: IP address

        @rtype: None
        @returns: nothing
        """
        if self.__hasBridge:
            self.__brConfigFile["IPADDR"] = value
            if self.__ethConfigFile.get('IPADDR'):
                del self.__ethConfigFile['IPADDR']
        else:
            self.__ethConfigFile["IPADDR"] = value
    # setIp()

    def getIp(self, default=""):
        """
        Returns the IP address

        @type  default: string
        @param default: default value

        @rtype: string
        @returns: IP address or default value if it is None
        """
        if self.__hasBridge:
            ip = self.__brConfigFile.get("IPADDR")
        else:
            ip = self.__ethConfigFile.get("IPADDR")

        if ip is not None:
            return ip

        return default
    # getIp()

    def setNetmask(self, value):
        """
        Sets network mask address to the network interface

        @type  value: string
        @param value: network mask address

        @rtype: None
        @returns: nothing
        """
        if self.__hasBridge:
            self.__brConfigFile["NETMASK"] = value
            if self.__ethConfigFile.get('NETMASK'):
                del self.__ethConfigFile['NETMASK']
        else:
            self.__ethConfigFile["NETMASK"] = value
    # setNetmask()

    def getNetmask(self, default=""):
        """
        Returns the network mask

        @type  default: string
        @param default: default value

        @rtype: string
        @returns: network mask address or default value if it is None
        """
        if self.__hasBridge:
            netmask = self.__brConfigFile.get("NETMASK")
        else:
            netmask = self.__ethConfigFile.get("NETMASK")

        if netmask is not None:
            return netmask

        return default
    # getNetmask()

    def setGateway(self, value):
        """
        Sets gateway to the network interface

        @type  value: string
        @param value: gateway

        @rtype: None
        @returns: nothing
        """
        if self.__hasBridge:
            self.__brConfigFile["GATEWAY"] = value
            if self.__ethConfigFile.get('GATEWAY'):
                del self.__ethConfigFile['GATEWAY']
        else:
            self.__ethConfigFile["GATEWAY"] = value
    # setGateway()

    def getGateway(self, default=""):
        """
        Returns the gateway

        @type  default: string
        @param default: default value

        @rtype: string
        @returns: gateway or default value if it is None
        """
        if self.__hasBridge:
            gateway = self.__brConfigFile.get("GATEWAY")
        else:
            gateway = self.__ethConfigFile.get("GATEWAY")

        if gateway is not None:
            return gateway

        return default
    # getGateway()

    def setHostname(self, value):
        """
        Sets hostname

        @type  value: string
        @param value: hostname

        @rtype: None
        @returns: nothing
        """
        self.__hostname = value
    # setHostname()

    def getHostname(self, default=""):
        """
        Returns the hostname

        @type  default: string
        @param default: default value

        @rtype: string
        @returns: hostname or default value if it is None
        """
        hostname = self.__hostname

        if hostname is not None:
            return hostname

        return default
    # getHostname()

    def getBootProto(self):
        """
        Retuns the boot protocol

        @rtype: string
        @returns: boot protocol associated to the network interface
        """
        if self.__hasBridge:
            bootproto = self.__brConfigFile.get("BOOTPROTO")
        else:
            bootproto = self.__ethConfigFile.get("BOOTPROTO")
        return bootproto
    # getBootProto()

    def getEthConfigFile(self):
        """
        Returns the content of network intergace config file

        @rtype: dict
        @returns: dictionary with the content of network interface config file
        """
        return self.__ethConfigFile
    # getEthConfigFile()

    def getBrConfigFile(self):
        """
        Returns the content of network bridge config file

        @rtype: dict
        @returns: dictionary with the content of network bridge config file
        """
        if self.__hasBridge:
            return self.__brConfigFile
        else:
            return None
    # getBrConfigFile()

    def setNoDefRoute(self, noDefRoute):
        """
        Do not allow the interface being set as the default route.

        @type  value: bootlean

        @rtype: None
        @returns: nothing
        """
        if noDefRoute:
            if self.__hasBridge:
                self.__brConfigFile["DEFROUTE"] = "no"
                self.__brConfigFile["PEERROUTES"] = "no"
                if self.__ethConfigFile.get('DEFROUTE'):
                    del self.__ethConfigFile['DEFROUTE']
                if self.__ethConfigFile.get('PEERROUTES'):
                    del self.__ethConfigFile['PEERROUTES']
            else:
                self.__ethConfigFile["DEFROUTE"] = "no"
                self.__ethConfigFile["PEERROUTES"] = "no"
    # setNoDefRoute()

    def __saveIfcfgFile(self):
        """
        Save ifcfg file for current NIC and for its bridge, if it is applicable.

        @rtype: None
        @returns: Nothing
        """
        # Saving network cfg file
        self.__logger.debug("Writing on ISO image ethConfigFile:")
        for line in pprint.pformat(self.__ethConfigFile).split('\n'):
            self.__logger.debug(line)
        Network.writeConfigFile(self.__ethConfigFile)
        if self.__hasBridge:
            self.__logger.debug("Writing on ISO image brConfigFile:")
            for line in pprint.pformat(self.__brConfigFile).split('\n'):
                self.__logger.debug(line)
            Network.writeConfigFile(self.__brConfigFile)
        else:
            Network.deleteBrConfigFile(self.__ethConfigFile['DEVICE'])
    # __saveIfcfgFile()

    def __setNIC(self, data):
        """
        Create ifcfg file based on kickstart.

        @type  data: dict
        @param data: NIC information

        @rtype: None
        @returns: Nothing
        """
        self.__logger.debug("Setting NIC's according kickstart.")
        # userdefine
        for network in data['model'].get('network'):
            # validate device
            if network.get('device'):
                #dev = network['device']
                #device = Network.getUdevPredictableName(dev)
                device = network['device']
            else:
                self.__logger.critical("Missing interface name in kickstart file.")
                raise ZKVMError("PREINSTALL", "NETDEV", "NO_NIC")
            # load previous configuration.
            self.__loadConfigFile(device)
            # bridge
            if network.get('bridge'):
                self.setBridge(True)
            # device
            self.setDev(device, None)
            # onboot
            if not network.get('onboot') is None:
                self.setOnBoot(network['onboot'])
            # dns
            self.setDNS()
            # dhcp
            if network['bootProto'] == "dhcp" and not network['ip']:
                self.enableDHCP(True)
            else:
                self.enableDHCP(False)
                if network.get('ip'):
                    self.setIp(network['ip'])
                if network.get('gateway'):
                    self.setGateway(network['gateway'])
                if network.get('netmask'):
                    self.setNetmask(network['netmask'])
                if network.get('hostname'):
                    self.setHostname(network['hostname'])
            self.setNoDefRoute(network['nodefroute'])

            # Saving network cfg file
            self.__saveIfcfgFile()
    # __setNIC()

    def __setAllDHCP(self):
        """
        Config all NIC's to DHCP.

        @rtype: None
        @returns: Nothing
        """
        self.__logger.debug("Setting all NIC's to DHCP.")

        # Verify if there is a NIC redefined by bootline
        ifname = Network.getCmdLineNIC()
        if ifname is not None:
            # load previous configuration.
            self.__loadConfigFile(ifname)
            # set redefined NIC in bootline to DHCP
            self.enableDHCP(True)

            # Saving network cfg file
            self.__saveIfcfgFile()
    #__setAllDHCP()

    def onPreInstall(self, data):
        """
        Handles the pre install event
        @type  data: dict
        @param data: relevant arguments for that given event
        @rtype: None
        @returns: Nothing
        """
        try:
            self.__logger.info("Executing NetDevice module (EVT_PRE_INSTALL).")
            if data['model'].get('network'):
                if (len(data['model'].get('network')) == 1 and
                        data['model'].get('network')[0].get('device') == '' and
                        data['model'].get('network')[0].get('bootProto') == 'dhcp'):
                    # set all NIC's to DHCP
                    self.__setAllDHCP()
                else:
                    # set NIC's according kickstart
                    self.__setNIC(data)
            #if data['model'].get('isKickstart'):
            #    self.__logger.debug("Restarting network services in ISO image...")
            #    Network.restartNetworkService()
        except ZKVMError:
            self.__logger.critical("Failed NetDev module")
            raise
        except Exception as e:
            self.__logger.critical("Failed NetDev module")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("PREINSTALL", "NETDEV", "PRE_MODULES")
    # onPretInstall()

# NetDevice
