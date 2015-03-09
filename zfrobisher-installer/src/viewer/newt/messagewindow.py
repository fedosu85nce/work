#
# IMPORTS
#
from snack import *
from model.config import STR_VERSION
from viewer.__data__ import  IBM_ZKVM


#
# CONSTANTS
#

#
# CODE
#
class MessageWindow:
    """
    Verify the hard disk selected is part od a LVM Volume Group
    """

    def __init__(self, screen):
        """
        Constructor

        @type  screen: SnackScreen
        @param screen: SnackScreen instance

        """
        self.__screen = screen
        self.__grid = GridForm(self.__screen, IBM_ZKVM.localize() % STR_VERSION, 1, 1)
    # __init__()

    def show(self, msg):
        """
        Displays a message

        @type  msg: str
        @param msg: message to be displayed

        @rtype:   nothing
        @returns: nothing
        """
        omsg = TextboxReflowed(30, msg)
        self.__grid.add(omsg, 0, 0)
        self.__grid.draw()
        self.__screen.refresh()
    # show()

    def popWindow(self):
        """
        Pop window from windows stack

        @rtype:   nothing
        @returns: nothing
        """
        self.__screen.popWindow()
    # popWindow()

# MessageWindow
