#!/usr/bin/python

#
# IMPORTS
#
from snack import *
from model.config import STR_VERSION
from viewer.__data__ import REBOOT_MSG
from viewer.__data__ import IBM_ZKVM
from viewer.__data__ import REBOOT
from viewer.__data__ import INSTALLATION_COMPLETED


#
# CONSTANTS
#


#
# CODE
#
class RebootSystem:
    """
    Last screen for the installer application
    """

    def __init__(self, screen):
        """
        Constructor

        @type  screen: SnackScreen
        @param screen: SnackScreen instance
        """
        self.__screen = screen
        self.__msg = INSTALLATION_COMPLETED.localize() + REBOOT_MSG.localize()


        #self.__msg = TextboxReflowed(40, self.__msg)
        self.__buttonsBar = ButtonBar(self.__screen, [(REBOOT.localize(), "reboot")])

        self.__grid = GridForm(self.__screen, IBM_ZKVM.localize() % STR_VERSION, 1, 2)
        #self.__grid.add(self.__msg, 0, 0)
        self.__grid.add(self.__buttonsBar, 0, 1, (0,1,0,0))
    # __init__()

    def run(self, error = False):
        """
        Draws the screen

        @type error: boolean
        @param error: reboot due to error

        @rtype: integer
        @returns: sucess status
        """
        if error:
            self.__msg = REBOOT_MSG.localize()

        self.__msg = TextboxReflowed(40, self.__msg)
        self.__grid.add(self.__msg, 0, 0)
        self.__grid.run()

        return 0
    # run()
# RebootSystem
