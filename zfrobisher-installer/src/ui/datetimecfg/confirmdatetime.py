#!/usr/bin/python

#
# IMPORTS
#
import os

from datetime import datetime
from snack import *


#
# CONSTANTS
#


#
# CODE
#
class ConfirmDateTime:
    """
    Screen to configure date and time
    """

    def __init__(self, screen):
        """
        Constructor

        @type  screen: SnackScreen
        @param screen: SnackScreen instance
        """
        self.__screen = screen

        self.__date = Entry(11, "")
        self.__time = Entry(9, "")

        self.__dateLabel = Label("Date [MM/DD/YYYY]")
        self.__timeLabel = Label("Time [HH:MM:ss]")

        self.__msg = TextboxReflowed(40, "Confirm the system date and time")
        self.__buttonsBar = ButtonBar(self.__screen,(("OK","ok"),("Back","back")))

        self.__contentGrid = Grid(2, 2)
        self.__contentGrid.setField(self.__dateLabel, 0, 0, anchorLeft=1)
        self.__contentGrid.setField(self.__timeLabel, 0, 1, anchorLeft=1)
        self.__contentGrid.setField(self.__date, 1, 0, (1, 0, 0, 0), anchorLeft=1)
        self.__contentGrid.setField(self.__time, 1, 1, (1, 0, 0, 0), anchorLeft=1)
    # __init__()

    def __show(self):
        """
        Shows screen once

        @rtype: integer
        @returns: status of operation
        """
        self.__grid = GridForm(self.__screen, "Date and Time", 1, 3)
        self.__grid.add(self.__msg, 0, 0, (0, 0, 0, 1))
        self.__grid.add(self.__contentGrid, 0, 1, (0, 0, 0, 1))
        self.__grid.add(self.__buttonsBar, 0, 2, (0, 0, 0, 1))

        result = self.__grid.run()
        self.__screen.popWindow()
        rc = self.__buttonsBar.buttonPressed(result)

        if rc == "back":
            return -1

        date = self.__date.value().split("/")
        time = self.__time.value().split(":")

        if len(date) < 3 or len(time) < 3:
            ButtonChoiceWindow(self.__screen, "Invalid date and time values",
                               "You need to entry valid values for date and time", buttons=["OK"],
                               width = 50)
            return 1

        try:
            month = int(date[0])
            day = int(date[1])
            year = int(date[2])

            hour = int(time[0])
            minute = int(time[1])
            secs = int(time[2])

            datetime(year, month, day, hour, minute, secs)

            os.popen("date +%%D%%T -s \"%02d/%02d/%s %02d:%02d:%02d\" &>/dev/null" % (month, day, year, hour, minute, secs))
            with open('/etc/adjtime') as fd:
                lines = fd.readlines()

            if lines[2].startswith('UTC'):
                utcDateTime = datetime.utcnow()
                os.popen("hwclock --set --date=\"%s/%s/%s %s:%s:%s\"" % (utcDateTime.month, utcDateTime.day, utcDateTime.year,
                                                                             utcDateTime.hour, utcDateTime.minute, utcDateTime.second))
            else:
                os.popen("hwclock -w")
            return 0
        except:
            ButtonChoiceWindow(self.__screen, "Invalid date and time values",
                               "You need to entry valid values for date and time", buttons=["OK"],
                               width = 50)
            return 1

    # __show()

    def run(self):
        """
        Draws the screen

        @rtype: integer
        @returns: status of operation
        """
        now = datetime.now()

        date = "%02d/%02d/%02d" % (now.month, now.day, now.year)
        self.__date.set(date)

        time = "%02d:%02d:%02d" % (now.hour, now.minute, now.second)
        self.__time.set(time)

        rc = self.__show()

        while rc == 1:
            rc = self.__show()

        return rc
    # run()
# ConfirmDateTime
