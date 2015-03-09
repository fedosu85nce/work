#
# IMPORTS
#
from snack import *
from model.config import STR_VERSION
from viewer.__data__ import LVM_ERROR_MSG
from viewer.__data__ import WARNING_MSG
from viewer.__data__ import IBM_ZKVM
from viewer.__data__ import INSTALLATION_ERROR
from viewer.__data__ import YES
from viewer.__data__ import NO


#
# CONSTANTS
#

#
# CODE
#
class CheckHardDisk:
    """
    Verify the hard disk selected is part od a LVM Volume Group
    """

    def __init__(self, screen, diskSelected):
        """
        Constructor

        @type  screen: SnackScreen
        @param screen: SnackScreen instance

        @type  diskSelected: str
        @param diskSelected: disk selected by user
        """
        self.__screen = screen
        self.__msg = TextboxReflowed(40,  WARNING_MSG.localize() % diskSelected)
        self.__buttonsBar = ButtonBar(self.__screen, [(YES.localize(), "yes"),
            (NO.localize(), "no")])

        self.__grid = GridForm(self.__screen, IBM_ZKVM.localize() % STR_VERSION, 1, 3)
        self.__grid.add(self.__msg, 0, 0)
        self.__grid.add(self.__buttonsBar, 0, 1, (0, 1, 0, 0))
    # __init__()

    def displayStandardError(self, diskSelected):
        """
        Displays an error message to the user if the LVM cannot be
        removed

        @type  diskSelected: str
        @param diskSelected: disk selected by user

        @rtype:   nothing
        @returns: nothing
        """
        ButtonChoiceWindow(self.__screen, INSTALLATION_ERROR.localize(),
                           LVM_ERROR_MSG % diskSelected, buttons=["OK"], width = 50)
    # displayStandardError()
    def run(self):
        """
        Draws the screen

        @rtype: integer
        @returns: sucess status
        """
        result = self.__grid.run()
        self.__screen.popWindow()
        return self.__buttonsBar.buttonPressed(result)
    # run()

# CheckHardDisk
