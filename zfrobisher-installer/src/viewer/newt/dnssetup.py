#
# IMPORTS
#
import socket

from modules.network.dns import DNS
from snack import *

from viewer.__data__ import OK
from viewer.__data__ import BACK
from viewer.__data__ import SKIP
from viewer.__data__ import DNSSETUP_HOSTNAME_LABEL
from viewer.__data__ import DNSSETUP_FST_DNS_LABEL
from viewer.__data__ import DNSSETUP_SND_DNS_LABEL
from viewer.__data__ import DNSSETUP_SEARCH_LABEL
from viewer.__data__ import DNSSETUP_CONFIG_DNS


#
# CONSTANTS
#


#
# CODE
#
class DNSSetup:
    """
    Represents the DNS configuration screen
    """

    def __init__(self, screen, data):
        """
        Constructor

        @type  screen: SnackScreen
        @param screen: SnackScreen instance
        """
        self.__screen = screen
        self.__dns = DNS()

        self.__hostnameLabel = Label(DNSSETUP_HOSTNAME_LABEL.localize())
        self.__primaryDNSLabel = Label(DNSSETUP_FST_DNS_LABEL.localize())
        self.__secondaryDNSLabel = Label(DNSSETUP_SND_DNS_LABEL.localize())
        self.__searchListLabel = Label(DNSSETUP_SEARCH_LABEL.localize())

        data_dns = data['model'].get('dns')

        hostname = socket.gethostname() if not data_dns else data_dns['hostname']
        primarydns = self.__dns.getPrimaryDNS() if not data_dns else data_dns['primary']
        secondarydns = self.__dns.getSecondaryDNS() if not data_dns else data_dns['secondary']
        searchlist = self.__dns.getSearchList() if not data_dns else data_dns['search']

        self.__hostname = Entry(15, hostname)
        self.__primaryDNS = Entry(15, primarydns)
        self.__secondaryDNS = Entry(15, secondarydns)
        self.__searchList = Entry(15, searchlist)

        self.__contentGrid = Grid(2, 4)
        self.__contentGrid.setField(self.__hostnameLabel, 0, 0, anchorLeft=1)
        self.__contentGrid.setField(self.__primaryDNSLabel, 0, 1, anchorLeft=1)
        self.__contentGrid.setField(self.__secondaryDNSLabel, 0, 2, anchorLeft=1)
        self.__contentGrid.setField(self.__searchListLabel, 0, 3, anchorLeft=1)

        self.__contentGrid.setField(self.__hostname, 1, 0, (1, 0, 0, 0))
        self.__contentGrid.setField(self.__primaryDNS, 1, 1, (1, 0, 0, 0))
        self.__contentGrid.setField(self.__secondaryDNS, 1, 2, (1, 0, 0, 0))
        self.__contentGrid.setField(self.__searchList, 1, 3, (1, 0, 0, 0))

        self.__buttonsBar = ButtonBar(self.__screen, [(OK.localize(),"ok"),
            (BACK.localize(), "back"), (SKIP.localize(), "skip")])

        self.__grid = GridForm(self.__screen, DNSSETUP_CONFIG_DNS.localize(), 1, 2)
        self.__grid.add(self.__contentGrid, 0, 0, (0,0,0,1))
        self.__grid.add(self.__buttonsBar, 0, 1)
    # __init__()

    def run(self):
        """
        Draws the screen

        @rtype: integer
        @returns: status of operation
        """
        result = self.__grid.run()
        self.__screen.popWindow()

        dnsData = {}
        dnsData['primary'] = self.__primaryDNS.value()
        dnsData['secondary'] = self.__secondaryDNS.value()
        dnsData['search'] = self.__searchList.value()
        dnsData['hostname'] = self.__hostname.value()

        return (self.__buttonsBar.buttonPressed(result), dnsData)
    # run()

# DNSSetup
