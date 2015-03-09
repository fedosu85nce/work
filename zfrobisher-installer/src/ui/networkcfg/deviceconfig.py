#!/usr/bin/python

#
# IMPORTS
#
from modules.network.netdevice import NetDevice
from modules.network.network import Network
from ui.config import *
from snack import *


#
# CONSTANTS
#
BUTTON_OK = "OK"

ERROR_INVALID_ENTRY = "Invalid Entry"
ERROR_INVALID_ENTRY_MSG = "Either DHCP must be select, or IP must be provided."


#
# CODE
#
class DeviceConfig:
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

        self.__hwdevLabel = Label("Device")
        self.__macAddressLabel = Label("MAC Address")
        self.__dhcpLabel = Label("Use DHCP")
        self.__ipLabel = Label("Static IP")
        self.__netmaskLabel = Label("Netmask")
        self.__gatewayLabel = Label("Default gateway IP")
        self.__bridgeLabel = Label("Create Network Bridge (br%s)" % dev)
        self.__enableLabel = Label("Enable")

        self.__contentGrid = Grid(2, 8)
        self.__contentGrid.setField(self.__hwdevLabel, 0, 0, anchorLeft=1)
        self.__contentGrid.setField(self.__macAddressLabel, 0, 1, anchorLeft=1)
        self.__contentGrid.setField(self.__dhcpLabel, 0, 2, anchorLeft=1)
        self.__contentGrid.setField(self.__ipLabel, 0, 3, anchorLeft=1)
        self.__contentGrid.setField(self.__netmaskLabel, 0, 4, anchorLeft=1)
        self.__contentGrid.setField(self.__gatewayLabel, 0, 5, anchorLeft=1)
        self.__contentGrid.setField(self.__bridgeLabel, 0, 6, anchorLeft=1)
        self.__contentGrid.setField(self.__enableLabel, 0, 7, anchorLeft=1)

        self.__contentGrid.setField(self.__hwdev, 1, 0, (1, 0, 0, 0))
        self.__contentGrid.setField(self.__macAddress, 1, 1, (1, 0, 0, 0))
        self.__contentGrid.setField(self.__dhcp, 1, 2, (1, 0, 0, 0), anchorLeft=1)
        self.__contentGrid.setField(self.__ip, 1, 3, (1, 0, 0, 0))
        self.__contentGrid.setField(self.__netmask, 1, 4, (1, 0, 0, 0))
        self.__contentGrid.setField(self.__gateway, 1, 5, (1, 0, 0, 0))
        self.__contentGrid.setField(self.__bridge, 1, 6, (1, 0, 0, 0), anchorLeft=1)
        self.__contentGrid.setField(self.__enable, 1, 7, (1, 0, 0, 0), anchorLeft=1)

        self.__dhcp.setCallback(self.useDynamicCheckBox)

        self.__buttonsBar = ButtonBar(self.__screen,
                                      (("Save", "save"), ("Back", "back")))

        self.__grid = GridForm(self.__screen, "Network Device Configuration", 1, 3)
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
        activeLinkInterfaces = Network.getLinkedInterfaces(False)
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

        self.__grid.setCurrent(self.__dhcp)

        # bridge
        if self.__dev.hasBridge():
            self.__bridge.setValue('*')

        # onboot
        if self.__hasLink():
            if self.__dev.getOnBoot():
                self.__enable.setValue('*')
        else:
            self.__enable.setFlags(FLAG_DISABLED, FLAGS_SET)

        self.__grid.setCurrent(self.__bridge)

        self.__ip.set(Network.removeDoubleQuotes(self.__dev.getIp()))
        self.__netmask.set(Network.removeDoubleQuotes(self.__dev.getNetmask()))
        self.__gateway.set(Network.removeDoubleQuotes(self.__dev.getGateway()))

        self.useDynamicCheckBox()

        result = self.__grid.run()
        self.__screen.popWindow()
        rc = self.__buttonsBar.buttonPressed(result)

        if rc == "save":
            if self.__dhcp.selected() or self.__ip.value() != "" or not self.__enable.selected():
                self.__saveConfig()
                msg = TextboxReflowed(40, "Configuring %s interface..." % self.__hwdev.value())
                g = GridForm(self.__screen, "IBM zKVM", 1, 2)
                g.add(msg, 0, 0)
                g.draw()
                self.__screen.refresh()

                try:
                    # restart network service
                    Network.restartNetworkService(None, self.__interface)
                    return 0
                except Exception as e:
                    Network.disableNIC(None, self.__interface)
                    ButtonChoiceWindow(self.__screen, "ERROR",
                                       "Failed to configure %s interface:\n%s" % (self.__interface, e), buttons=[BUTTON_OK],
                                       width=40)
                    return -1
                finally:
                    self.__screen.popWindow()
            else:
                ButtonChoiceWindow(self.__screen, ERROR_INVALID_ENTRY,
                                   ERROR_INVALID_ENTRY_MSG, buttons=[BUTTON_OK],
                                   width=50)
                return 1
        if rc == "back":
            return 1
    # run()
# DeviceConfig
