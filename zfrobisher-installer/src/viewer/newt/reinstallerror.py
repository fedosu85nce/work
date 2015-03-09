#!/usr/bin/python

#
# IMPORTS
#
from snack import *
from model.config import STR_VERSION
from viewer.__data__ import REINSTALL_ERROR_MSG
from viewer.__data__ import IBM_ZKVM
from viewer.__data__ import OK


#
# CONSTANTS
#

#
# CODE
#
class ReinstallError:
    """
    Screen shown when the reinstall process fail.
    """

    def __init__(self, screen):
        """
        Constructor.

        @type  screen: SnackScreen
        @param screen: SnackScreen instance

        @rtype: None
        @return: Nothing
        """
        self.__screen = screen
        self.__msg = REINSTALL_ERROR_MSG.localize()

        self.__msg = TextboxReflowed(40, self.__msg)
        self.__buttonsBar = ButtonBar(self.__screen, [(OK.localize(), "ok")])

        self.__grid = GridForm(self.__screen, IBM_ZKVM.localize() % STR_VERSION, 1, 2)
        self.__grid.add(self.__msg, 0, 0)
        self.__grid.add(self.__buttonsBar, 0, 1, (0,1,0,0))
    # __init__()

    def run(self):
        """
        Draws the screen

        @rtype: int
        @return: sucess status
        """
        self.__grid.run()

        return 0
    # run()

# ReinstallError
