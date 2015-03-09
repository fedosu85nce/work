#
# IMPORTS
#
from snack import *
from model.config import STR_VERSION
from viewer.__data__ import LVM_ERROR_MSG
from viewer.__data__ import WARNING_MSG
from viewer.__data__ import YES
from viewer.__data__ import NO
from viewer.__data__ import IBM_ZKVM
from viewer.__data__ import REINSTALL_DISK_MSG


#
# CONSTANTS
#


#
# CODE
#
class ConfirmReinstall(object):
    """
    Builds a screen to show a confirmation message before wipe root device and
    reinstall system.
    """

    def __init__(self, screen, installed_disk=None):
        """
        Constructor.

        @type  screen: SnackScreen
        @param screen: SnackScreen instance
        @type  installed_disk: String
        @param installed_disk: The disk where zKVM was installed

        @rtype: None
        @return: Nothing
        """
        if installed_disk != None:
            reinstall_disk_msg = REINSTALL_DISK_MSG.localize() % installed_disk
        else:
            reinstall_disk_msg = ""

        self.__screen = screen
        self.__msg = TextboxReflowed(60, reinstall_disk_msg + WARNING_MSG.localize())
        self.__buttonsBar = ButtonBar(self.__screen, [(NO.localize(), "no"),
            (YES.localize(), "yes")])

        self.__grid = GridForm(self.__screen, IBM_ZKVM.localize() % STR_VERSION, 1, 3)
        self.__grid.add(self.__msg, 0, 0)
        self.__grid.add(self.__buttonsBar, 0, 1, (0, 1, 0, 0))
    # __init__()

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

# ConfirmReinstall
