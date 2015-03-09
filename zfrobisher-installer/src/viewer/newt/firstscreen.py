#
# IMPORTS
#
from snack import *
from model.config import GA_VERSION


#
# CONSTANTS
#

#
# CODE
#
class FirstScreen:
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
        self.__grid = GridForm(self.__screen, "IBM zKVM", 1, 1)
    # __init__()

    def show(self):
        """
        Displays a message

        @type  msg: str
        @param msg: message to be displayed

        @rtype:   nothing
        @returns: nothing
        """
        omsg = TextboxReflowed(30, "IBM zKVM %s..." % GA_VERSION)
        self.__grid.add(omsg, 0, 0)
        self.__grid.draw()
        self.__screen.refresh()
    # show()

# FirstScreen
