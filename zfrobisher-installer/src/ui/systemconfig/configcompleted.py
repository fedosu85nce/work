#!/usr/bin/python

#
# IMPORTS
#
from snack import *


#
# CONSTANTS
#


#
# CODE
#
class ConfigCompleted:
    """
    Last screen for the configuration application
    """

    def __init__(self, screen):
        """
        Constructor

        @type  screen: SnackScreen
        @param screen: SnackScreen instance
        """
        self.__screen = screen

        self.__msg = TextboxReflowed(40, "The system configuration is completed. Exit from the configuration tool and log into the system.")
        self.__buttonsBar = ButtonBar(self.__screen, [("Exit", "exit")])

        self.__grid = GridForm(self.__screen, "IBM zKVM", 1, 2)
        self.__grid.add(self.__msg, 0, 0)
        self.__grid.add(self.__buttonsBar, 0, 1, (0,1,0,0))
    # __init__()

    def run(self):
        """
        Draws the screen

        @rtype: integer
        @returns: sucess status
        """
        self.__grid.run()
        self.__screen.finish()

        return 'exit'
    # run()
# ConfigCompleted
