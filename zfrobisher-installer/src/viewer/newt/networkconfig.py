#
# IMPORTS
#
from modules.network.netdevice import NetDevice
from modules.network.network import Network
from ui.config import *
from snack import *

from viewer.__data__ import OK
from viewer.__data__ import BACK
from viewer.__data__ import NETWORKCFG_DEVICE_LABEL
from viewer.__data__ import NETWORKCFG_MACADDR_LABEL
from viewer.__data__ import NETWORKCFG_DHCP_LABEL
from viewer.__data__ import NETWORKCFG_IP_LABEL
from viewer.__data__ import NETWORKCFG_NETMASK_LABEL
from viewer.__data__ import NETWORKCFG_GATEWAY_LABEL
from viewer.__data__ import NETWORKCFG_DEVICE_CONFIG
from viewer.__data__ import NETWORKCFG_BRIDGE_LABEL
from viewer.__data__ import ERROR_INVALID_ENTRY
from viewer.__data__ import ERROR_INVALID_ENTRY_MSG
from viewer.__data__ import ENABLE_LABEL


#
# CONSTANTS
#


#
# CODE
#
class NetworkConfig:
    """
    Represents the network interface configuration screen
    """

    def __init__(self, screen, dev, macaddr):
        """
        Constructor

        @type  screen: SnackScreen
        @param screen: SnackScreen instance

        @type  dev: string
        @param dev: network interface name
        """
        self.__task = [False]
        self.__screen = screen
        self.__dev = NetDevice(dev)
        self.__interface = dev
        self.__macaddr = macaddr

        self.__hwdev = Entry(20, "%s" % dev)
        self.__hwdev.setFlags(FLAG_DISABLED, FLAGS_SET)

        self.__macAddress = Entry(20, macaddr)
        self.__macAddress.setFlags(FLAG_DISABLED, FLAGS_SET)

        self.__dhcp = Checkbox("")
        self.__ip = Entry(20, "")
        self.__netmask = Entry(20, "")
        self.__gateway = Entry(20, "")
        self.__bridge = Checkbox("")
        self.__enable = Checkbox("")

        self.__hwdevLabel = Label(NETWORKCFG_DEVICE_LABEL.localize())
        self.__macAddressLabel = Label(NETWORKCFG_MACADDR_LABEL.localize())
        self.__dhcpLabel = Label(NETWORKCFG_DHCP_LABEL.localize())
        self.__ipLabel = Label(NETWORKCFG_IP_LABEL.localize())
        self.__netmaskLabel = Label(NETWORKCFG_NETMASK_LABEL.localize())
        self.__gatewayLabel = Label(NETWORKCFG_GATEWAY_LABEL.localize())
        self.__bridgeLabel = Label(NETWORKCFG_BRIDGE_LABEL.localize() % dev)
        self.__enableLabel = Label(ENABLE_LABEL.localize())

        self.__contentGrid = Grid(2, 7)
        self.__contentGrid.setField(self.__hwdevLabel, 0, 0, anchorLeft=1)
        self.__contentGrid.setField(self.__macAddressLabel, 0, 1, anchorLeft=1)
        self.__contentGrid.setField(self.__dhcpLabel, 0, 2, anchorLeft=1)
        self.__contentGrid.setField(self.__ipLabel, 0, 3, anchorLeft=1)
        self.__contentGrid.setField(self.__netmaskLabel, 0, 4, anchorLeft=1)
        self.__contentGrid.setField(self.__gatewayLabel, 0, 5, anchorLeft=1)
        #self.__contentGrid.setField(self.__bridgeLabel, 0, 6, anchorLeft=1)
        self.__contentGrid.setField(self.__enableLabel, 0, 6, anchorLeft=1)

        self.__contentGrid.setField(self.__hwdev, 1, 0, (1, 0, 0, 0))
        self.__contentGrid.setField(self.__macAddress, 1, 1, (1, 0, 0, 0))
        self.__contentGrid.setField(self.__dhcp, 1, 2, (1, 0, 0, 0), anchorLeft=1)
        self.__contentGrid.setField(self.__ip, 1, 3, (1, 0, 0, 0))
        self.__contentGrid.setField(self.__netmask, 1, 4, (1, 0, 0, 0))
        self.__contentGrid.setField(self.__gateway, 1, 5, (1, 0, 0, 0))
        #self.__contentGrid.setField(self.__bridge, 1, 6, (1, 0, 0, 0), anchorLeft=1)
        self.__contentGrid.setField(self.__enable, 1, 6, (1, 0, 0, 0), anchorLeft=1)

        self.__dhcp.setCallback(self.useDynamicCheckBox)

        self.__buttonsBar = ButtonBar(self.__screen, [(OK.localize(), "ok"),
                                      (BACK.localize(), "back")])

        self.__grid = GridForm(self.__screen, NETWORKCFG_DEVICE_CONFIG.localize(), 1, 3)
        self.__grid.add(self.__contentGrid, 0, 0, (0, 0, 0, 1))
        self.__grid.add(self.__buttonsBar, 0, 1)

        self.useDynamicCheckBox()
    # __init__()

    def useDynamicCheckBox(self):
        """
        Handles the dhcp check box

        @rtype: None
        @returns: nothing
        """
        if self.__dhcp.selected():
            state = FLAGS_SET
        else:
            state = FLAGS_RESET

        for i in self.__ip, self.__netmask, self.__gateway:
            i.setFlags(FLAG_DISABLED, state)
    # useDynamicCheckBox()

    def __saveConfig(self):
        """
        Write the configuration into the file

        @rtype: None
        @returns: nothing
        """
        # bridge
        if self.__bridge.selected():
            self.__dev.setBridge(True)
        else:
            self.__dev.setBridge(False)

        # device
        self.__dev.setDev(self.__interface, self.__macaddr)

        # onboot
        if self.__hasLink():
            if self.__enable.selected():
                self.__dev.setOnBoot(True)
            else:
                self.__dev.setOnBoot(False)
        else:
            self.__dev.setOnBoot(False)

        # dns
        self.__dev.setDNS()

        # dhcp
        if self.__dhcp.selected():
            self.__dev.enableDHCP(True)
        else:
            self.__dev.enableDHCP(False)
            self.__dev.setIp(self.__ip.value())
            self.__dev.setNetmask(self.__netmask.value())
            self.__dev.setGateway(self.__gateway.value())

        # Saving network cfg file
        Network.writeConfigFile(self.__dev.getEthConfigFile())
        if self.__dev.hasBridge():
            Network.writeConfigFile(self.__dev.getBrConfigFile())
        else:
            Network.deleteBrConfigFile(self.__interface)
    # __saveConfig()

    def __hasLink(self):
        """
        Return the link status of the NIC

        @rtype: boolean
        @returns: True if NIC has link
        """
        activeLinkInterfaces = Network.getLinkedInterfaces()
        link = False
        if self.__interface in activeLinkInterfaces:
            link = True
        return link
    # __hasLink()

    def run(self):
        """
        Draws the screen

        @rtype: integer
        @returns: status of operation
        """
        # dhcp
        if self.__dev.getBootProto() == "dhcp":
            self.__dhcp.setValue('*')

        # bridge
        if self.__dev.hasBridge():
            self.__bridge.setValue('*')

        # onboot
        if self.__hasLink():
            if self.__dev.getOnBoot():
                self.__enable.setValue('*')
        else:
            self.__enable.setFlags(FLAG_DISABLED, FLAGS_SET)

        self.__grid.setCurrent(self.__dhcp)

        self.__ip.set(Network.removeDoubleQuotes(self.__dev.getIp()))
        self.__netmask.set(Network.removeDoubleQuotes(self.__dev.getNetmask()))
        self.__gateway.set(Network.removeDoubleQuotes(self.__dev.getGateway()))

        self.useDynamicCheckBox()

        result = self.__grid.run()
        self.__screen.popWindow()
        rc = self.__buttonsBar.buttonPressed(result)

        # struct the data entered for returning
        network = {}

        if rc == "ok":
            if self.__dhcp.selected() or self.__ip.value() != "" or not self.__enable.selected():
                self.__saveConfig()

                if self.__dhcp.selected():
                    network['bootProto'] = 'dhcp'
                    network['ip'] = ''
                else:
                    network['bootProto'] = 'none'
                    network['ip'] = self.__ip.value()
                    network['gateway'] = self.__gateway.value()
                    network['netmask'] = self.__netmask.value()
                    network['hostname'] = ''

                if self.__bridge.selected():
                    network['bridge'] = True
                else:
                    network['bridge'] = False

                if self.__enable.selected():
                    network['onboot'] = True
                else:
                    network['onboot'] = False

                network['nodefroute'] = False
                network['device'] = self.__interface
                return (rc, network)
            else:
                self.showErrorEntry()
                return ("failed", network)
        else:
            return (rc, network)
    # run()

    def showErrorEntry(self):
        """
        Displays an error about the invalid entry

        @rtype: nothing
        @returns: nothing
        """
        ButtonChoiceWindow(self.__screen, ERROR_INVALID_ENTRY.localize(),
                           ERROR_INVALID_ENTRY_MSG.localize(),
                           buttons=[(OK.localize(), 'ok')],
                           width=50)
    # showErrorEntry()

# NetworkConfig
