#
# IMPORTS
#
import socket

from snack import *

from viewer.__data__ import OK
from viewer.__data__ import BACK
from viewer.__data__ import NTPSETUP_CONFIG_NTP
from viewer.__data__ import NTPSETUP_SERVER_1
from viewer.__data__ import NTPSETUP_SERVER_2
from viewer.__data__ import NTPSETUP_SERVER_3
from viewer.__data__ import NTPSETUP_SERVER_4
from viewer.__data__ import ENABLE_LABEL

#
# CONSTANTS
#


#
# CODE
#
class NTPSetup:
    """
    Represents the NTP configuration screen
    """

    def __init__(self, screen):
        """
        Constructor

        @type  screen: SnackScreen
        @param screen: SnackScreen instance
        """
        self.__screen = screen

        self.__enablelabel = Label(ENABLE_LABEL.localize())
        self.__ntp_server_1_label = Label(NTPSETUP_SERVER_1.localize())
        self.__ntp_server_2_label = Label(NTPSETUP_SERVER_2.localize())
        self.__ntp_server_3_label = Label(NTPSETUP_SERVER_3.localize())
        self.__ntp_server_4_label = Label(NTPSETUP_SERVER_4.localize())

        self.__enablentp = Checkbox("")

        self.__localserverhost_1 = ""
        self.__localserverhost_2 = ""
        self.__localserverhost_3 = ""
        self.__localserverhost_4 = ""

        self.__server_1 = Entry(35, "")
        self.__server_2 = Entry(35, "")
        self.__server_3 = Entry(35, "")
        self.__server_4 = Entry(35, "")

        self.useDynamicCheckBox()

        self.__contentGrid = Grid(3, 6)

        self.__contentGrid.setField(self.__enablelabel, 0, 0, anchorLeft=1)
        self.__contentGrid.setField(self.__enablentp, 1, 0, (1, 0, 0, 0))
        self.__enablentp.setCallback(self.useDynamicCheckBox)

        self.__contentGrid.setField(self.__ntp_server_1_label, 1, 1, anchorLeft=1)
        self.__contentGrid.setField(self.__ntp_server_2_label, 1, 2, anchorLeft=1)
        self.__contentGrid.setField(self.__ntp_server_3_label, 1, 3, anchorLeft=1)
        self.__contentGrid.setField(self.__ntp_server_4_label, 1, 4, anchorLeft=1)

        self.__contentGrid.setField(self.__server_1, 2, 1, (1, 0, 0, 0))
        self.__contentGrid.setField(self.__server_2, 2, 2, (1, 0, 0, 0))
        self.__contentGrid.setField(self.__server_3, 2, 3, (1, 0, 0, 0))
        self.__contentGrid.setField(self.__server_4, 2, 4, (1, 0, 0, 0))

        self.__buttonsBar = ButtonBar(self.__screen, [(OK.localize(),"ok"),
            (BACK.localize(), "back")])

        self.__grid = GridForm(self.__screen, NTPSETUP_CONFIG_NTP.localize(), 1, 2)
        self.__grid.add(self.__contentGrid, 0, 0, (0,0,0,1))
        self.__grid.add(self.__buttonsBar, 0, 1)
    # __init__()

    def loadNTPHostList(self, load = True):
        if load:
            self.__server_1.set(self.__localserverhost_1)
            self.__server_2.set(self.__localserverhost_2)
            self.__server_3.set(self.__localserverhost_3)
            self.__server_4.set(self.__localserverhost_4)
        else:
            if not self.__localserverhost_1 and \
                    not self.__localserverhost_2 and \
                    not self.__localserverhost_3 and \
                    not self.__localserverhost_4:
                self.__localserverhost_1 = "0.pool.ntp.org"
                self.__localserverhost_2 = "1.pool.ntp.org"
                self.__localserverhost_3 = "2.pool.ntp.org"
                self.__localserverhost_4 = "3.pool.ntp.org"

            else:
                #save values to be restored later
                self.__localserverhost_1 = self.__server_1.value()
                self.__localserverhost_2 = self.__server_2.value()
                self.__localserverhost_3 = self.__server_3.value()
                self.__localserverhost_4 = self.__server_4.value()

            self.__server_1.set("")
            self.__server_2.set("")
            self.__server_3.set("")
            self.__server_4.set("")

    def useDynamicCheckBox(self):
        """
        Handles the enable check box

        @rtype: None
        @returns: nothing
        """
        if self.__enablentp.selected():
            state=FLAGS_RESET
        else:
            state=FLAGS_SET

        self.loadNTPHostList(self.__enablentp.selected())

        for i in self.__server_1, self.__server_2, self.__server_3, self.__server_4:
            i.setFlags(FLAG_DISABLED, state)
    # useDynamicCheckBox()

    def run(self):
        """
        Draws the screen

        @rtype: integer
        @returns: status of operation
        """
        result = self.__grid.run()
        self.__screen.popWindow()

        if self.__enablentp.selected():
            ntpData = [
                    self.__server_1.value(),
                    self.__server_2.value(),
                    self.__server_3.value(),
                    self.__server_4.value()
                    ]
        else:
            ntpData = []

        return (self.__buttonsBar.buttonPressed(result), ntpData)
    # run()

# NTPSetup
