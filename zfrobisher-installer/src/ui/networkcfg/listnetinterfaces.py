#!/usr/bin/python

#
# IMPORTS
#
from snack import *
from modules.network.network import Network
from subprocess import Popen, PIPE
from ui.networkcfg.deviceconfig import DeviceConfig

#
# CONSTANTS
#


#
# CODE
#
class ListNetInterfaces:
    """
    Represents the network interface list screen
    """

    def __init__(self, screen):
        """
        Constructor

        @type  screen: SnackScreen
        @param screen: SnackScreen instance
        """
        self.__screen = screen
        self.__msg = TextboxReflowed(40, "Select the device on the list to be configured:")
        self.__list = Listbox(5, scroll=1, returnExit=1)
        self.__buttonsBar = ButtonBar(self.__screen, [("OK", "ok"),
                                                      ("Back", "back")])
        self.__devices = Network.getAvailableInterfaces(False)
    # __init__()

    def __show(self):
        """
        Shows screen once

        @rtype: integer
        @returns: status of operation
        """
        self.__grid = GridForm(self.__screen, "Configure network", 1, 3)
        self.__grid.add(self.__msg, 0, 0)
        self.__grid.add(self.__list, 0, 1)
        self.__grid.add(self.__buttonsBar, 0, 2)

        result = self.__grid.run()
        self.__screen.popWindow()
        rc = self.__buttonsBar.buttonPressed(result)

        if rc == "ok":
            rc = -1
            while rc == -1:
                window = DeviceConfig(self.__screen, self.__list.current(), self.__devices.get(self.__list.current()))
                rc = window.run()

        if rc == "back":
            return -1

        return rc
    # __show()

    def __activeInterfaces(self):
        """
        Active link (ifconfig nic up) for the NICs with no link

        @rtype  : list
        @returns: list of NICs with link
        """
        interfaces = self.__devices
        activeInterfaces = Network.getLinkedInterfaces(False)
        deactiveInterfaces = [f for f in interfaces.keys() if not f in activeInterfaces]
        Network.activeLinkInterfaces(deactiveInterfaces)
        activeInterfaces = Network.getLinkedInterfaces(False)
        return activeInterfaces
    # __activeInterfaces()

    def __deactiveInterfaces(self):
        """
        Deactive link (ifconfig nic down) for NICs not changes by user.
        Restore initial state for them, i.e., no link
        """
        cmd = "grep -s ONBOOT /etc/sysconfig/network-scripts/ifcfg-*"
        proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()
        if proc.returncode == 0:
            interfaces = self.__devices
            deactiveLinkInterfacesAll = []
            for fname in out.split():
                if fname.endswith("no"):
                    iface = fname.split("-")[-1].split(":")[0]
                    deactiveLinkInterfacesAll.append(iface)
            deactiveLinkInterfaces = [f for f in deactiveLinkInterfacesAll if f in interfaces.keys()]
            if len(deactiveLinkInterfaces):
                Network.deactiveLinkInterfaces(deactiveLinkInterfaces)
    # __deactiveInterfaces()

    def run(self):
        """
        Draws the screen

        @rtype: integer
        @returns: status of operation
        """
        devicesUp = self.__activeInterfaces()
        sortedDevices = sorted(self.__devices)
        for dev in sortedDevices:
            bridge = "br%s" % dev
            if dev in devicesUp:
                active = 'UP'
            elif bridge in devicesUp:
                active = 'UP - %s' % bridge
            else:
                active = 'DOWN'
            display = "%s [ %s ] (%s)" % (dev, self.__devices.get(dev), active)
            self.__list.append(display, dev)

        rc = self.__show()

        while rc == 1:
            rc = self.__show()

        # Restore untouched NICs to their previous state
        self.__deactiveInterfaces()
        return rc
    # run()
# ListNetInterfaces
