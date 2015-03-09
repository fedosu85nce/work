#
# IMPORTS
#
from snack import *

from viewer.__data__ import OK
from viewer.__data__ import BACK
from viewer.__data__ import TIMEZONE_LABEL
from viewer.__data__ import TIMEZONE_SELECTION_LABEL
from viewer.__data__ import TIMEZONE_UTC_CHECKBOX_LABEL
from viewer.__data__ import NTPSETUP_CONFIG_NTP
from viewer.__data__ import NTPSETUP_SERVER_1
from viewer.__data__ import NTPSETUP_SERVER_2
from viewer.__data__ import NTPSETUP_SERVER_3
from viewer.__data__ import NTPSETUP_SERVER_4


#
# CONSTANTS
#


#
# CODE
#
class AdjustTimezone:
    """
    Represents the timezone screen
    """

    def __init__(self, screen):
        """
        Constructor

        @type  screen: SnackScreen
        @param screen: SnackScreen instance
        """
        self.__screen = screen
        self.__msg = TextboxReflowed(40, TIMEZONE_LABEL.localize())
        self.__list = Listbox(5, scroll=1, returnExit=1)
        self.__utc = Checkbox(TIMEZONE_UTC_CHECKBOX_LABEL.localize(), isOn=0)
        self.__buttonsBar = ButtonBar(self.__screen, [(OK.localize(), "ok"),
            (BACK.localize(), "back")])

        self.__grid = GridForm(self.__screen,
                TIMEZONE_SELECTION_LABEL.localize(), 1, 4)
        self.__grid.add(self.__msg, 0, 0)
        self.__grid.add(self.__list, 0, 1, (0, 1, 0, 0))
        self.__grid.add(self.__utc, 0, 2, (0, 1, 0, 0), anchorLeft=1)
        self.__grid.add(self.__buttonsBar, 0, 3, (0, 1, 0, 0))
    # __init__()

    def run(self, tzentries):
        """
        Draws the screen

        @type  tzentries: list
        @param tzentries: list of timezone available

        @rtype: integer
        @returns: status of operation
        """
        for zone in tzentries:
            self.__list.append(zone, zone)

        result = self.__grid.run()
        self.__screen.popWindow()
        rc = self.__buttonsBar.buttonPressed(result)

        return (rc, self.__list.current(), self.__utc.selected())
    # run()

# AdjustTimezone
