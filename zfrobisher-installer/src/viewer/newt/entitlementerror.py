#!/usr/bin/python

#
# IMPORTS
#
from snack import *
from model.config import STR_VERSION
from viewer.__data__ import ENTITLE_ERROR_MSG
from viewer.__data__ import OK
from viewer.__data__ import REBOOT_MSG
from viewer.__data__ import IBM_ZKVM
from viewer.__data__ import INVALID_ENTITLEMENT


#
# CONSTANTS
#


#
# CODE
#
class EntitlementError:
    """
    Screen when hardware is not entitled
    """

    def __init__(self, screen):
        """
        Constructor

        @type  screen: SnackScreen
        @param screen: SnackScreen instance
        """
        self.__screen = screen
        self.__msg =  INVALID_ENTITLEMENT.localize() + REBOOT_MSG.localize()

        self.__msg = TextboxReflowed(40, self.__msg)
        self.__buttonsBar = ButtonBar(self.__screen, [(OK.localize(), "ok")])

        self.__grid = GridForm(self.__screen, IBM_ZKVM.localize() % STR_VERSION, 1, 2)
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

        return 0
    # run()
# EntitlementError
