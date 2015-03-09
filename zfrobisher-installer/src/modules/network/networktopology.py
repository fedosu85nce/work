#!/usr/bin/python

#
# IMPORTS
#
from controller.zkvmerror import ZKVMError
from modules.scriptbase import ScriptBase
from modules.network.network import Network
from subprocess import Popen, PIPE

import fileinput
import logging
import os
import pprint
import re
import traceback


#
# CODE
#
class NetworkTopology(ScriptBase):
    """
    Configure network topology
    """

    def __init__(self):
        """
        Contructor

        @type  name: string
        @param name: network interface name (default = None)
        """
        self.__logger = logging.getLogger(__name__)
        self.__configFile = {
            'DEVICE': None,
            'TYPE': 'Ethernet',
            'HWADDR': None,
            'BOOTPROTO': 'none',
            'ONBOOT': 'no',
        }
    # __init__()

    def __setEthConfigFile(self, dev, mac, devActiveList):
        """
        Set the device, mac address and onboot params

        @type  dev: str
        @param dev: device name
        @type  mac: str
        @param mac: mac address
        @type devActiveList: list
        @param devActiveList: list with NIC with network configured

        @rtype: None
        @returns: Nothing
        """
        self.__configFile['DEVICE'] = dev
        self.__configFile['HWADDR'] = mac
        if dev in devActiveList:
            # Network configured by the IBM zKVM installer
            # the default setup for this case is dhcp
            self.__configFile['ONBOOT'] = 'yes'
            self.__configFile['BOOTPROTO'] = 'dhcp'
        else:
            self.__configFile['ONBOOT'] = 'no'
            self.__configFile['BOOTPROTO'] = 'none'
    # __setEthConfigFile()

    def __fixDracutIfcfgFiles(self, devDict):
        """
        Fix ifcfg files generated by dracut that does not use UDEV predictable NIC name

        @type devDict: dict
        @param devDict: dictionary with device name and MAC addr

        @rtype: None
        @returns: Nothing
        """
        # get list of ifcfg files created by dracut
        ifcfgDir = '/etc/sysconfig/network-scripts/'
        ifcfgFiles = ["/etc/sysconfig/network-scripts/%s" % f for f in os.listdir(ifcfgDir) if re.match(r'ifcfg-.*', f)]
        ifcfgFiles.remove('/etc/sysconfig/network-scripts/ifcfg-lo')
        self.__logger.debug("ifcfg files create by dracut:")
        self.__logger.debug("%s" % ifcfgFiles)

        for dev, mac in devDict.iteritems():
            for ifcfgFile in ifcfgFiles:
                dracutDev = ifcfgFile.split('-')[-1]

                # Handling netmask in CIDR format, i.e. IP and netmask in the
                # format: xxx.xxx.xxx.xxx/yy
                # Dracut will create "PREFIX=yy" entry in ifcfg file
                # Need to replace/convert it to "NETMASK=xxx.xxx.xxx.xxx
                prefix = "PREFIX="
                if prefix in open(ifcfgFile).read():
                    with open(ifcfgFile) as f:
                        content = f.readlines()
                    for line in content:
                        if line.startswith(prefix):
                            self.__logger.debug("Found %s in %s" % (line.rstrip(), ifcfgFile))
                            searchExp = line
                        elif line.startswith("IPADDR="):
                            self.__logger.debug("Found %s in %s" % (line.rstrip(), ifcfgFile))
                            ipAddr = line
                    if searchExp and ipAddr:
                        number = searchExp.split("=")[-1].rstrip()
                        number = number.lstrip('"').rstrip('"')
                        ipAd = ipAddr.split("=")[-1].rstrip()
                        ipAd = ipAd.lstrip('"').rstrip('"')
                        cmd = "ipcalc --netmask %s/%s" % (ipAd, number)
                        self.__logger.debug("Getting netmask in CIDR format: %s" % cmd)
                        proc = Popen(cmd.split(" "), stdin=PIPE, stdout=PIPE)
                        out, err = proc.communicate()
                        if proc.returncode != 0:
                            raise Exception("networktopology: Failed to get netmask from ipcalc command (%s) (exit code = %s): %s" % (cmd, proc.returncode, err))
                    replaceExp = out
                    self.__logger.debug("Replace %s with %s in %s" % (searchExp.rstrip(), replaceExp.rstrip(), ifcfgFile))
                    for line in fileinput.input(ifcfgFile, inplace=1):
                        print line.replace(searchExp, replaceExp),

                # Fix DEVICE and NAME field in case ifcfg file does not use
                # UDEV predictable NIC name. Rename the file to reflact it, as
                # well.
                if mac in open(ifcfgFile).read():
                    self.__logger.debug("macaddr %s found in %s" % (mac, ifcfgFile))
                    if dracutDev != dev:
                        self.__logger.debug("Edit %s to use udev predictable NIC name (%s)" % (ifcfgFile, dev))
                        searchExp = "DEVICE=\"%s\"" % dracutDev
                        replaceExp = "DEVICE=%s" % dev
                        for line in fileinput.input(ifcfgFile, inplace=1):
                            print line.replace(searchExp, replaceExp),
                        searchExp = "NAME=\"%s\"" % dracutDev
                        replaceExp = "NAME=%s" % dev
                        for line in fileinput.input(ifcfgFile, inplace=1):
                            print line.replace(searchExp, replaceExp),
                        newIfcfgFile = "/etc/sysconfig/network-scripts/ifcfg-%s" % dev
                        os.rename(ifcfgFile, newIfcfgFile)
                    # ifcfg already handled, remove it from file list
                    ifcfgFiles.remove(ifcfgFile)
                    break
    # __fixDracutIfcfgFiles()

    def onPreInstall(self, data):
        """
        Handles the pre install event
        @type  data: dict
        @param data: relevant arguments for that given event
        @rtype: None
        @returns: Nothing
        """
        try:
            self.__logger.info("Executing NetworkTopology module (EVT_PRE_INSTALL).")
            # NIC status
            interfaces = Network.getAvailableInterfaces(False)
            activeLinkInterfaces = Network.getLinkedInterfaces(False)
            activeInterfaces = Network.getActiveInterfaces(False)
            udevInterfaces = Network.getAvailableInterfaces()
            udevActiveLinkInterfaces = Network.getLinkedInterfaces()
            udevActiveInterfaces = Network.getActiveInterfaces()
            self.__logger.debug("Network interfaces:")
            for line in pprint.pformat(interfaces).split('\n'):
                self.__logger.debug(line)
            self.__logger.debug("Network interfaces with link:")
            self.__logger.debug("%s" % activeLinkInterfaces)
            self.__logger.debug("Network interfaces with network configured:")
            self.__logger.debug("%s" % activeInterfaces)
            self.__logger.debug("Network interfaces (UDEV):")
            for line in pprint.pformat(udevInterfaces).split('\n'):
                self.__logger.debug(line)
            self.__logger.debug("Network interfaces with link (UDEV):")
            self.__logger.debug("%s" % udevActiveLinkInterfaces)
            self.__logger.debug("Network interfaces with network configured (UDEV):")
            self.__logger.debug("%s" % udevActiveInterfaces)

            # Configure network interfaces and bridges
            devDict = udevInterfaces
            devActiveList = udevActiveInterfaces
            if devDict:
                self.__fixDracutIfcfgFiles(devDict)
                for dev, mac in devDict.iteritems():
                    ifcfgFile = "/etc/sysconfig/network-scripts/ifcfg-%s" % dev
                    if not os.path.isfile(ifcfgFile):
                        self.__setEthConfigFile(dev, mac, devActiveList)
                        self.__logger.debug("Writing on ISO image ifcfg file:")
                        self.__logger.debug("%s" % ifcfgFile)
                        for line in pprint.pformat(self.__configFile).split('\n'):
                            self.__logger.debug(line)
                        Network.writeConfigFile(self.__configFile)
            else:
                self.__logger.debug("No NIC available!")
        except Exception as e:
            self.__logger.critical("Failed NetworkTopology module")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("PREINSTALL", "NETWORKTOPOLOGY", "PRE_MODULES")
    # onPostInstall()

# NetworkTopology
