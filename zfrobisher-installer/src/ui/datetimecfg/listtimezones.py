#!/usr/bin/python

#
# IMPORTS
#
from snack import *
from modules.timezone.timezone import Timezone


#
# CONSTANTS
#


#
# CODE
#
class ListTimezones:
    """
    List all the timezones
    """

    def __init__(self, screen):
        """
        Constructor

        @type  screen: SnackScreen
        @param screen: SnackScreen instance
        """
        self.__timezone = Timezone()

        self.__screen = screen
        self.__msg = TextboxReflowed(40, "Select the timezone for the system")
        self.__list = Listbox(5, scroll=1, returnExit=1)
        self.__utc = Checkbox("System clock uses UTC", isOn=0)
        self.__buttonsBar = ButtonBar(self.__screen, [("OK", "ok"),
                                                      ("Back", "back")])

        self.__grid = GridForm(self.__screen, "Timezone Selection", 1, 4)
        self.__grid.add(self.__msg, 0, 0)
        self.__grid.add(self.__list, 0, 1, (0, 1, 0, 0))
        self.__grid.add(self.__utc, 0, 2, (0, 1, 0, 0), anchorLeft=1)
        self.__grid.add(self.__buttonsBar, 0, 3, (0, 1, 0, 0))
    # __init__()

    def __show(self):
        """
        Shows screen once

        @rtype: integer
        @returns: status of operation
        """
        result = self.__grid.run()
        self.__screen.popWindow()
        rc = self.__buttonsBar.buttonPressed(result)

        if rc == "ok":
            self.__timezone.setTimezone(self.__list.current())
            self.__timezone.writeConfig()
            self.__timezone.setUTC(self.__utc.selected())

            return 0

        if rc == "back":
            return -1
    # __show()

    def run(self):
        """
        Draws the screen

        @rtype: integer
        @returns: status of operation
        """
        for zone in self.__timezone.getEntries():
            self.__list.append(zone, zone)

        return self.__show()
    # run()
# ListTimezones
