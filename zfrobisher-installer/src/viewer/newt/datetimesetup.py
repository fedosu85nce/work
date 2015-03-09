#
# IMPORTS
#
import socket
import time

from snack import *


from viewer.__data__ import OK
from viewer.__data__ import BACK
from viewer.__data__ import DATE_LABEL
from viewer.__data__ import TIME_LABEL
from viewer.__data__ import DATE_TIME_SETUP
from viewer.__data__ import ERROR_DATETIME_FORMAT
from viewer.__data__ import ERROR_DATETIME_FORMAT_MSG

#
# CONSTANTS
#


#
# CODE
#
class DateTimeSetup:
    """
    Represents the Datetime configuration screen
    """

    def __init__(self, screen):
        """
        Constructor

        @type  screen: SnackScreen
        @param screen: SnackScreen instance
        """
        self.__screen = screen

        self.__date_label = Label(DATE_LABEL.localize())
        self.__time_label = Label(TIME_LABEL.localize())

        self.__list_year   = Listbox(1, scroll=0, width=4, returnExit=1)
        self.__list_month  = Listbox(1, scroll=0, width=2, returnExit=1)
        self.__list_day    = Listbox(1, scroll=0, width=2, returnExit=1)
        self.__list_hour   = Listbox(1, scroll=0, width=2, returnExit=1)
        self.__list_minute = Listbox(1, scroll=0, width=2, returnExit=1)
        self.__list_second = Listbox(1, scroll=0, width=2, returnExit=1)


        self.__contentGrid = Grid(6, 2)
        self.__contentGrid.setField(self.__date_label, 0, 0, anchorLeft=1)
        self.__contentGrid.setField(self.__list_year,  1, 0, anchorLeft=1)
        self.__contentGrid.setField(Label("/"),        2, 0, anchorLeft=1)
        self.__contentGrid.setField(self.__list_month,      3, 0, anchorLeft=1)
        self.__contentGrid.setField(Label("/"),        4, 0, anchorLeft=1)
        self.__contentGrid.setField(self.__list_day,        5, 0, anchorLeft=1)


        self.__contentGrid.setField(self.__time_label, 0, 1, (1, 0, 0, 0))
        self.__contentGrid.setField(self.__list_hour,       1, 1, anchorLeft=1)
        self.__contentGrid.setField(Label(":"),        2, 1, anchorLeft=1)
        self.__contentGrid.setField(self.__list_minute,     3, 1, anchorLeft=1)
        self.__contentGrid.setField(Label(":"),        4, 1, anchorLeft=1)
        self.__contentGrid.setField(self.__list_second,     5, 1, anchorLeft=1)

        self.__buttonsBar = ButtonBar(self.__screen, [(OK.localize(),"ok"),
            (BACK.localize(), "back")])

        self.__grid = GridForm(self.__screen, DATE_TIME_SETUP.localize(), 1, 2)
        self.__grid.add(self.__contentGrid, 0, 0, (0,0,0,1))
        self.__grid.add(self.__buttonsBar, 0, 1)
    # __init__()

    def run(self):
        """
        Draws the screen

        @rtype: integer
        @returns: status of operation
        """

        localtime = time.localtime()

        # populate listboxes
        for i in range(2014,2035):
            self.__list_year.append(str(i), str(i))

        if localtime.tm_year < 2014:
            self.__list_year.setCurrent("2014")
        else:
            self.__list_year.setCurrent(str(localtime.tm_year))

        for i in range(1,13):
            self.__list_month.append(str(i), str(i))

        self.__list_month.setCurrent(str(localtime.tm_mon))

        for i in range(1,32):
            self.__list_day.append(str(i), str(i))

        self.__list_day.setCurrent(str(localtime.tm_mday))

        for i in range(0,24):
            self.__list_hour.append(str(i), str(i))

        self.__list_hour.setCurrent(str(localtime.tm_hour))

        for i in range(0,60):
            self.__list_minute.append(str(i), str(i))

        self.__list_minute.setCurrent(str(localtime.tm_min))

        for i in range(0,60):
            self.__list_second.append(str(i), str(i))

        self.__list_second.setCurrent(str(localtime.tm_sec))

        result = self.__grid.run()
        self.__screen.popWindow()

        ntpData = [
                self.__list_year.current(),
                self.__list_month.current(),
                self.__list_day.current(),
                self.__list_hour.current(),
                self.__list_minute.current(),
                self.__list_second.current(),
                ]

        return (self.__buttonsBar.buttonPressed(result), ntpData)
    # run()

    def showErrorWrongFormat(self, str_date):
        """
        Displays an error about the datetime format

        @rtype: nothing
        @returns: nothing
        """
        ButtonChoiceWindow(self.__screen, ERROR_DATETIME_FORMAT.localize(),
                           ERROR_DATETIME_FORMAT_MSG.localize() % str_date,
                           buttons=[(OK.localize(), 'ok'), (BACK.localize(),
                               'back')],
                           width = 50)
    # showErrorLength()


# DateTimeSetup
