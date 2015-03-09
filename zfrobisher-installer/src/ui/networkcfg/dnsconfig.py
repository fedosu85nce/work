#!/usr/bin/python

#
# IMPORTS
#
import os
import socket

from snack import *
from modules.network.dns import DNS


#
# CONSTANTS
#


#
# CODE
#
class DNSConfig:
    """
    Represents the DNS configuration screen
    """

    def __init__(self, screen):
        """
        Constructor

        @type  screen: SnackScreen
        @param screen: SnackScreen instance
        """
        self.__screen = screen
        self.__dns = DNS()

        self.__hostnameLabel = Label("Hostname")
        self.__primaryDNSLabel = Label("Primary DNS")
        self.__secondaryDNSLabel = Label("Secondary DNS")
        self.__searchListLabel = Label("Search")

        self.__hostname = Entry(15, socket.gethostname())
        self.__primaryDNS = Entry(15, self.__dns.getPrimaryDNS())
        self.__secondaryDNS = Entry(15, self.__dns.getSecondaryDNS())
        self.__searchList = Entry(15, self.__dns.getSearchList())

        self.__contentGrid = Grid(2, 4)
        self.__contentGrid.setField(self.__hostnameLabel, 0, 0, anchorLeft=1)
        self.__contentGrid.setField(self.__primaryDNSLabel, 0, 1, anchorLeft=1)
        self.__contentGrid.setField(self.__secondaryDNSLabel, 0, 2, anchorLeft=1)
        self.__contentGrid.setField(self.__searchListLabel, 0, 3, anchorLeft=1)

        self.__contentGrid.setField(self.__hostname, 1, 0, (1, 0, 0, 0))
        self.__contentGrid.setField(self.__primaryDNS, 1, 1, (1, 0, 0, 0))
        self.__contentGrid.setField(self.__secondaryDNS, 1, 2, (1, 0, 0, 0))
        self.__contentGrid.setField(self.__searchList, 1, 3, (1, 0, 0, 0))

        self.__buttonsBar = ButtonBar(self.__screen,(("OK","ok"),("Back","back")))

        self.__grid = GridForm(self.__screen, "DNS Configuration", 1, 2)
        self.__grid.add(self.__contentGrid, 0, 0, (0,0,0,1))
        self.__grid.add(self.__buttonsBar, 0, 1)
    # __init__()

    def __writeConfig(self):
        """
        Write configuration into the file

        @rtype: None
        @returns: nothing
        """
        hostname = self.__hostname.value()
        os.popen("hostname %s" % hostname)

        self.__dns.setPrimaryDNS(self.__primaryDNS.value())
        self.__dns.setSecondaryDNS(self.__secondaryDNS.value())
        self.__dns.setSearchList(self.__searchList.value())
        self.__dns.write()
    # __writeConfig()

    def run(self):
        """
        Draws the screen

        @rtype: integer
        @returns: status of operation
        """
        result = self.__grid.run()
        self.__screen.popWindow()
        rc = self.__buttonsBar.buttonPressed(result)

        if rc == "back":
            return -1

        self.__writeConfig()
        return 0
    # run()

# DNSConfig
