#!/usr/bin/python

#
# IMPORTS
#
from subprocess import Popen, PIPE
from time import sleep

import ethtool
import fileinput
import os
import re
import shlex
import shutil
import uuid


#
# CONSTANTS
#
XML_FILE = '/opt/ibm/zkvm-installer/modules/network/kop.xml'


#
# CODE
#
class Network:
    """
    Utilities to get network information
    """

    def __new__(cls):
        raise NotImplementedError("This class cannot be instantiated.")
    # __new__()

    def getVirtualNic():
        """
        Returns all virtual network interfaces available on the system

        @rtype:   list
        @returns: list of Virtual NIC's
        """
        proc = Popen(['ls', '/sys/devices/virtual/net'], stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()
        if proc.returncode != 0:
            raise Exception("NETWORK: Failed to list virtual net devices (exit code = %s):\n%s" % (proc.returncode, err))
        return out.rstrip().split("\n")
    # getVirtualNic
    getVirtualNic = staticmethod(getVirtualNic)

    def getCmdLineNIC():
        """
        Returns network interface name if it was changed by boot command line

        @rtype:   str
        @returns: NIC name from boot commad line
        """
        proc = Popen(['cat', '/proc/cmdline'], stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()
        if proc.returncode != 0:
            raise Exception("NETWORK: Failed to get cmdline from /proc/cmdlline (exit code = %s):\n%s" % (proc.returncode, err))
        cmdLine = out.rstrip()
        ifName = None
        for i in cmdLine.split(" "):
            if i.startswith("ifname"):
                ifName = i.split("=")[1].split(":")[0]
        return ifName
    # getCmdLineNIC
    getCmdLineNIC = staticmethod(getCmdLineNIC)

    def getUdevPredictableName(dev):
        """
        Returns the mapped network interface name based on udev predictable rules.
        Respected network interfaces predefined in boot command line.

        @rtype:   str
        @returns: NIC name according UDEV predictable rules.
        """
        device = None
        ifName = Network.getCmdLineNIC()
        if ifName == dev:
            device = ifName
        else:
            strCmd1 = "udevadm info --query=property --path=/sys/class/net/%s"
            cmd2 = "grep ID_NET_NAME_PATH"
            cmd1 = strCmd1 % dev
            proc1 = Popen(cmd1.split(" "), stdout=PIPE)
            proc2 = Popen(cmd2.split(" "), stdin=proc1.stdout, stdout=PIPE)
            proc1.stdout.close()
            out, err = proc2.communicate()
            if proc2.returncode == 0:
                # Found udev predictable NIC name
                device = out.rstrip().split('=')[1]
            elif proc2.returncode == 1:
                # No udev predictable NIC name, use the same dev
                device = dev
            else:
                raise Exception("NETWORK: Failed to get predictable network name from udev (exit code = %s):\n%s" % (proc2.returncode, err))
        return device
    # getUdevPredictableName
    getUdevPredictableName = staticmethod(getUdevPredictableName)

    def getLinkedInterfaces(liveDVD=True):
        """
        Return a list of all network interfaces on the system with active link
        (the same as ethtool.get_active_devices(), however, it also works
        when the system is booted via liveDVD and the network must be started
        manually - Network.startLiveDVDNetwork())

        @type mountDir: boolean
        @param mountDir: True is running in liveDVD

        @rtype:   array
        @returns: list of NIC with active link
        """
        interfaces = []
        devices = ethtool.get_devices()
        for dev in devices:
            cmd = ['ethtool', dev]
            proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
            out, err = proc.communicate()
            if proc.returncode != 0:
                raise Exception("NETWORK: Failed to execute ethtool on %s (exit code = %s):\n%s" % (dev, proc.returncode, err))
            if out.rstrip().endswith("Link detected: yes"):
                if liveDVD:
                    device = Network.getUdevPredictableName(dev)
                else:
                    device = dev
                interfaces.append(device)
        return interfaces
    # getLinkedInterfaces()
    getLinkedInterfaces = staticmethod(getLinkedInterfaces)

    def getAvailableInterfaces(liveDVD=True):
        """
        Returns all the network interfaces (eth/en[pP]) available on the system

        @type liveDVD: boolean
        @param liveDVD: True is running in liveDVD

        @rtype:   dict
        @returns: (key = ethernet interface / value = mac addresss) available
        """
        interfaces = {}
        devices = ethtool.get_devices()
        virtualIfaces = Network.getVirtualNic()
        for dev in devices:
            if dev not in virtualIfaces:
                if liveDVD:
                    device = Network.getUdevPredictableName(dev)
                else:
                    device = dev
                interfaces[device] = ethtool.get_hwaddr(dev)
        return interfaces
    # getAvailableInterfaces
    getAvailableInterfaces = staticmethod(getAvailableInterfaces)

    def getUnactiveInterfaces(liveDVD=True):
        """
        Return all the unconfigured interfaces (eth/en[pP]) exist on the system

        @type liveDVD: boolean
        @param liveDVD: True is running in liveDVD

        @rtype: dict
        @returns : (key=interface device bus ID / value=type of the interface)
        """
        interfaces = {}
        proc = Popen(['znetconf', '-u'], stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()
        if proc.returncode != 0:
            raise Exception(("NETWORK: Failed to list unconfigurd "
                             "net devices (exit code = %s):\n%s")
                            % (proc.returncode, err))
        split_str = re.compile(r'-+')
        dev_str_list = split_str.split(out)
        if len(dev_str_list) > 1:
            dev_list = dev_str_list[1].strip().split("\n")
        else:
            return interfaces
        for dev_item in dev_list:
            dev_parts = dev_item.split(" ")
            dev_type = "%s%s" % (dev_parts[2], dev_parts[3])
            # filter the non-OSA interfaces out
            if cmp(dev_type, "OSA(QDIO)") == 0:
                interfaces[dev_parts[0]] = dev_type
        return interfaces
    # getUnactiveInterfaces
    getUnactiveInterfaces = staticmethod(getUnactiveInterfaces)

    def setInterfaceActived(busId, portName, portNum, layer2):
        """
        Set the interface specified by busId to active status

        @type busId: string
        @param busId: the bus ID of the selected network interface

        @type portName: string
        @param portName: set the port name of the network interface

        @type portNum: int
        @param portName: set the port number of the network interface

        @type layer2: boolean
        @param layer2: set the device working mode, True=layer2, False=layer3
        """
        option_str = ""
        if len(portName) > 0:
            option_str = option_str + " -o portname=%s" % portName
        if layer2:
            option_str = option_str + " -o layer2=1"
        else:
            option_str = option_str + " -o layer2=0"
        option_str = option_str + " -o portno=%d" % portNum
        argument = " -a %s " % busId
        proc = Popen(['znetconf', "%s" % argument], stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()
        if proc.returncode != 0:
            raise Exception(("NETWORK: Failed to active net"
                             " devices %s (exit code = %s):\n%s")
                            % (busId, proc.returncode, err))
        eth_name = ""
        with open('/sys/bus/ccwgroup/devices/%s/if_name'
                  % (busId.split(',')[0])) as f:
            eth_name = f.read()
            eth_name = eth_name[:-1]
        mac_addr = ""
        with open('/sys/class/net/%s/address' % eth_name) as g:
            mac_addr = g.read()
            mac_addr = mac_addr[:-1]

        dev_conf = {}
        dev_conf['NAME'] = '\"%s\"' % eth_name
        dev_conf['UUID'] = '\"%s\"' % str(uuid.uuid4())
        dev_conf['NETBOOT'] = 'no'
        dev_conf['SUBCHANNELS'] = '\"%s\"' % busId
        dev_conf['OPTIONS'] = '\"%s\"' % option_str
        dev_conf['DEVICE'] = '%s' % eth_name
        dev_conf['HWADDR'] = '%s' % mac_addr
        dev_conf['NETTYPE'] = '\"qeth\"'

        Network.writeConfigFile(dev_conf)

        return (argument, eth_name, mac_addr)
    # setInterfaceActived
    setInterfaceActived = staticmethod(setInterfaceActived)

    def getActiveInterfaces(liveDVD=True):
        """
        Returns all the network interfaces (eth/en[pP] available on the system
        with network configured

        @type mountDir: boolean
        @param mountDir: True is running in liveDVD

        @rtype:   array
        @returns: list of NIC with active link
        """
        interfaces = []
        devices = list(Network.getAvailableInterfaces(liveDVD).keys())
        for dev in devices:
            cmd1 = "ip address show %s" % dev
            proc1 = Popen(shlex.split(cmd1), stdout=PIPE, stderr=PIPE)
            cmd2 = "grep inet"
            proc2 = Popen(shlex.split(cmd2), stdin=proc1.stdout, stdout=PIPE, stderr=PIPE)
            proc1.stdout.close()
            output, err = proc2.communicate()
            if output.lstrip().startswith("inet "):
                if liveDVD:
                    device = Network.getUdevPredictableName(dev)
                else:
                    device = dev
                interfaces.append(device)
        return interfaces
    # getActiveInterfaces
    getActiveInterfaces = staticmethod(getActiveInterfaces)

    def deleteBrConfigFile(dev, mountDir=None):
        """
        Bring down, delete network bridge and delete its configuration file

        @type configFile: dict
        @type configFile: network device which bridge will be deleted

        @type mountDir: str
        @param mountDir: mounted directory if is in auto mode

        @rtype: None
        @returns: nothing
        """
        bridge = "br%s" % dev
        ifcfgFile = "/etc/sysconfig/network-scripts/ifcfg-%s" % bridge
        if mountDir:
            ifcfgFile = mountDir + ifcfgFile
        if os.path.exists(ifcfgFile):
            os.remove(ifcfgFile)
        bridgePath = "/sys/class/net/%s" % bridge
        if not os.path.exists(bridgePath):
            return

        # Bring down and delete bridge interface
        cmdDown = ['ip', 'link', 'set', bridge, 'down']
        cmdDelete = ['ip', 'link', 'del', bridge]

        if mountDir:
            cmdDown.insert(0, mountDir)
            cmdDown.insert(0, 'chroot')
            cmdDelete.insert(0, mountDir)
            cmdDelete.insert(0, 'chroot')

        proc = Popen(cmdDown, stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()
        proc = Popen(cmdDelete, stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()
    # deleteBrConfigFile()
    deleteBrConfigFile = staticmethod(deleteBrConfigFile)

    def removeDoubleQuotes(text):
        """
        Strip first and last double quotes from string

        @type  text: str
        @param text: text to be evaluated

        @rtype: str
        @returns: text
        """
        if text:
            if text.startswith('"'):
                text = text[1:]
            if text.endswith('"'):
                text = text[:-1]
        return text
    # removeDoubleQuotes()
    removeDoubleQuotes = staticmethod(removeDoubleQuotes)

    def writeConfigFile(configFile, mountDir=None):
        """
        Write the new configuration into the file

        @type configFile: dict
        @type configFile: content of network config file

        @type mountDir: str
        @param mountDir: mounted directory if is in auto mode

        @rtype: None
        @returns: nothing
        """
        # remove double quotes from NIC name
        ifname = Network.removeDoubleQuotes(configFile['DEVICE'])
        ifcfgFile = "/etc/sysconfig/network-scripts/ifcfg-%s" % ifname
        if mountDir:
            ifcfgFile = mountDir + ifcfgFile

        line = "# Generated by IBM zKVM installer\n"
        with open(ifcfgFile, "w") as fd:
            fd.write(line)
            for key, value in configFile.iteritems():
                line = "%s=%s\n" % (key, value)
                fd.write(line)

        # if configFile['DEVICE'].startswith("br") and configFile['ONBOOT'] == 'yes':
        #     ifcfgFile = "/etc/sysconfig/network-scripts/ifcfg-eth%s" % configFile['DEVICE'][2:]
        #     if not os.path.isfile(ifcfgFile):
        #         ifcfgFile = "/etc/sysconfig/network-scripts/ifcfg-enp%s" % configFile['DEVICE'][2:]
        #         if not os.path.isfile(ifcfgFile):
        #             ifcfgFile = "/etc/sysconfig/network-scripts/ifcfg-enP%s" % configFile['DEVICE'][2:]
        #     if mountDir:
        #         ifcfgFile = mountDir + ifcfgFile
        #     searchExp = "ONBOOT=no"
        #     replaceExp = "ONBOOT=yes"
        #     for line in fileinput.input(ifcfgFile, inplace=1):
        #         print line.replace(searchExp, replaceExp),
    # writeConfigFile()
    writeConfigFile = staticmethod(writeConfigFile)

    def copyConfigFile(mountDir):
        """
        Copy configuration from ISO to installed system

        @type configFile: str
        @type configFile: mount path dir of installed system

        @rtype: None
        @returns: nothing
        """
        if not mountDir:
            raise Exception("NETWORK: invalid system mount point")

        ifcfgDir = '/etc/sysconfig/network-scripts/'
        ifcfgDirInstalled = mountDir + ifcfgDir
        ifcfgFiles = [f for f in os.listdir(ifcfgDir) if re.match(r'ifcfg-.*', f)]
        # ifcfgFiles = filter(lambda f: re.match(r'ifcfg-.*', f), os.listdir(ifcfgDir))
        ifcfgFiles.remove('ifcfg-lo')

        for srcFile in ifcfgFiles:
            destFile = ifcfgDirInstalled + srcFile
            srcFile = ifcfgDir + srcFile
            shutil.copy(srcFile, destFile)

    # copyConfigFile()
    copyConfigFile = staticmethod(copyConfigFile)

    def restartNetworkService(mountDir=None, nic=None):
        """
        Restart network service using sysmtectl (systemd)

        @type mountDir: str
        @param mountDir: mounted directory if is in auto mode
        @type nic: str
        @param nic: network interface

        @rtype: None
        @returns: Nothing
        """
        # /etc/sysconfig/network is required for network service script
        networkFile = '/etc/sysconfig/network'
        if mountDir:
            networkFile = mountDir + networkFile
        if not os.path.isfile(networkFile):
            with open(networkFile, 'a'):
                os.utime(networkFile, None)

        # Restart network service
        if mountDir:
            # auto mode
            proc = Popen(['chroot', mountDir, '/sbin/chkconfig', 'network', 'on'], stdout=PIPE, stderr=PIPE)
            out, err = proc.communicate()
            if proc.returncode != 0:
                raise Exception("NETWORK: Failed to enable network service (exit code = %s):\n%s" % (proc.returncode, err))
        elif nic:
            nics = [nic]
            bridge = "br%s" % nic
            ifcfgFilePattern = "/etc/sysconfig/network-scripts/ifcfg-%s"
            activeNics = Network.getLinkedInterfaces(False)
            # only restart nic if it has an active link
            if nic in activeNics or bridge in activeNics:
                ifcfgFile = ifcfgFilePattern % bridge
                if os.path.exists(ifcfgFile):
                    nics.append(bridge)

                for iface in nics:
                    proc = Popen(['ifdown', iface], stdout=PIPE, stderr=PIPE)
                    out, err = proc.communicate()
                    if proc.returncode != 0:
                        raise Exception("NETWORK: Failed to deactivate %s (exit code = %s):\n%s" % (iface, proc.returncode, err))

                    # Only start network config if ONBOOT=yes
                    ifcfgFile = ifcfgFilePattern % iface
                    onboot = "ONBOOT=yes"
                    if onboot in open(ifcfgFile).read():
                        proc = Popen(['ifup', iface], stdout=PIPE, stderr=PIPE)
                        out, err = proc.communicate()
                        if proc.returncode != 0:
                            raise Exception("NETWORK: Failed to activate %s (exit code = %s):\n%s" % (iface, proc.returncode, err))
        else:
            # manual mode
            # restart network service
            proc = Popen(['systemctl', 'restart', 'network.service'], stdout=PIPE, stderr=PIPE)
            out, err = proc.communicate()
            if proc.returncode != 0:
                raise Exception("NETWORK: Failed to restart network service (exit code = %s):\n%s" % (proc.returncode, err))

            # enable network service
            proc = Popen(['systemctl', 'enable', 'network.service'], stdout=PIPE, stderr=PIPE)
            out, err = proc.communicate()
            if proc.returncode != 0:
                raise Exception("NETWORK: Failed to enable network service (exit code = %s):\n%s" % (proc.returncode, err))
    # restartNetworkService()
    restartNetworkService = staticmethod(restartNetworkService)

    def disableNIC(mountDir, nic):
        """
        Disable network interface (ONBOOT=no).

        @type mountDir: str
        @param mountDir: mounted directory if is in auto mode
        @type nic: str
        @param nic: network interface

        @rtype  : nothing
        @returns: nothing
        """
        bridge = "br%s" % nic
        nics = [nic, bridge]
        ifcfgFilePattern = "/etc/sysconfig/network-scripts/ifcfg-%s"
        for iface in nics:
            ifcfgFile = ifcfgFilePattern % iface
            if mountDir:
                ifcfgFile = mountDir + ifcfgFile
            if os.path.isfile(ifcfgFile):
                searchExp = "ONBOOT=yes"
                replaceExp = "ONBOOT=no"
                for line in fileinput.input(ifcfgFile, inplace=1):
                    print line.replace(searchExp, replaceExp),
    # disableNIC()
    disableNIC = staticmethod(disableNIC)

    def setNTP(mountDir):
        proc = Popen(['/bin/ln', '-s', '/usr/lib/systemd/system/ntpd.service', mountDir+'/etc/systemd/system/multi-user.target.wants/ntpd.service'], stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()
        if proc.returncode != 0:
            raise Exception("NETWORK: Failed to enable ntpdate service (exit code = %s):\n%s" % (proc.returncode, err))
    # setNTP()
    setNTP = staticmethod(setNTP)

    def activeLinkInterfaces(interfaces):
        """
        Active link (ifconfig nic up) for the given NICs

        @type interfaces: list
        @param interfaces: list of the NICs to be activated (link)

        @rtype  : nothing
        @returns: nothing
        """
        # Active NIC's link
        for iface in interfaces:
            cmd = ['ifconfig', iface, 'up']
            proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
            out, err = proc.communicate()
            if proc.returncode != 0:
                raise Exception("NETWORK: Failed to activate link on liveDVD %s (exit code = %s):\n%s" % (cmd, proc.returncode, err))
        # wait link up
        sleep(5)
    # activeLinkInterfaces()
    activeLinkInterfaces = staticmethod(activeLinkInterfaces)

    def deactiveLinkInterfaces(interfaces):
        """
        Deactive link (ifconfig nic down) for the given NICs

        @type interfaces: list
        @param interfaces: list of the NICs to be deactivated (link)

        @rtype  : nothing
        @returns: nothing
        """
        # Active NIC's link
        for iface in interfaces:
            cmd = ['ifconfig', iface, 'down']
            proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
            out, err = proc.communicate()
            if proc.returncode != 0:
                raise Exception("NETWORK: Failed to deactivate link on liveDVD %s (exit code = %s):\n%s" % (cmd, proc.returncode, err))
        # wait link up
        sleep(5)
    # deactiveLinkInterfaces()
    deactiveLinkInterfaces = staticmethod(deactiveLinkInterfaces)

    def startLiveDVDNetwork():
        """
        Try to start network (dhcp) when boot from liveDVD.

        @rtype  : nothing
        @returns: nothing
        """
        # Get all NICs
        interfaces = Network.getAvailableInterfaces(False)
        # Do not reconfigure NIC defined by user in boot line
        ifName = Network.getCmdLineNIC()
        if ifName and interfaces.get(ifName):
            del interfaces[ifName]

        # Active NIC's link
        Network.activeLinkInterfaces(interfaces.keys())

        # Release NIC's
        cmd = ['dhclient', '-r']
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()
        if proc.returncode != 0:
            raise Exception("NETWORK: Failed to release NIC's on liveDVD %s (exit code = %s):\n%s" % (cmd, proc.returncode, err))

        # Remove virtual NIC's
        virtualInterfaces = Network.getVirtualNic()
        activeInterfaces = Network.getLinkedInterfaces()
        for iface in virtualInterfaces:
            activeInterfaces.remove(iface)

        # Try to configure network for each NIC's
        cmd = ['dhclient']
        cmd = cmd + activeInterfaces
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()
        if proc.returncode != 0:
            raise Exception("NETWORK: Failed to configure network on liveDVD %s (exit code = %s):\n%s" % (cmd, proc.returncode, err))
        # wait 3 seconds per NIC
        sleep(len(activeInterfaces)*3)
    # startLiveDVDNetwork()
    startLiveDVDNetwork = staticmethod(startLiveDVDNetwork)

# Network
