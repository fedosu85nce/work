#
# IMPORTS
#
from snack import *
from modules.network.network import Network

from viewer.__data__ import EDIT
from viewer.__data__ import BACK
from viewer.__data__ import NEXT
from viewer.__data__ import LISTNETIFACE_SELECT_DEVICE
from viewer.__data__ import LISTNETIFACE_CONFIG_NET
from viewer.__data__ import UP
from viewer.__data__ import DOWN

#
# CONSTANTS
#


#
# CODE
#
class ListNetworkifaces:
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
        self.__msg = TextboxReflowed(40, LISTNETIFACE_SELECT_DEVICE.localize())
        self.__list = Listbox(5, scroll=1, returnExit=1)
        self.__buttonsBar = ButtonBar(self.__screen, [(EDIT.localize(), "edit"),
            (BACK.localize(), "back"),(NEXT.localize(), "next")])
        self.__devices = Network.getAvailableInterfaces()
        self.__unactive = Network.getUnactiveInterfaces()
    # __init__()

    def __show(self):
        """
        Shows screen once

        @rtype: integer
        @returns: status of operation
        """
        self.__grid = GridForm(self.__screen, LISTNETIFACE_CONFIG_NET.localize(), 1, 3)
        self.__grid.add(self.__msg, 0, 0)
        self.__grid.add(self.__list, 0, 1)
        self.__grid.add(self.__buttonsBar, 0, 2)

        result = self.__grid.run()
        self.__screen.popWindow()
        rc = self.__buttonsBar.buttonPressed(result)

        return (rc, self.__list.current(), self.__devices.get(self.__list.current()))
    # __show()

    def run(self):
        """
        Draws the screen

        @rtype: integer
        @returns: status of operation
        """
        devicesUp = Network.getLinkedInterfaces()
        #sortedDevices = sorted(self.__devices, key=self.__devices.get)
        sortedDevices = sorted(self.__devices)
        for dev in sortedDevices:
            bridge = "br%s" % dev
            if dev in devicesUp:
                active = UP.localize()
            elif bridge in devicesUp:
                active = UP.localize() + ' - %s' % bridge
            else:
                active = DOWN.localize()
            display = "%s [ %s ] (%s)" % (dev, self.__devices.get(dev), active)
            self.__list.append(display, dev)
        # to ensure the actived interfaces are at the top of the list
        # add the rest of the OSA interfaces to the list here
        sortedDevices = sorted(self.__unactive)
        for dev in sortedDevices:
            display = "%s %s (%s)" % (dev,
                                      self.__unactive.get(dev),
                                      DOWN.localize())
            self.__list.append(display, dev)
        return self.__show()
    # run()

# ListNetworkifaces
