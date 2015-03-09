#
# IMPORTS
#
from snack import *
from model.config import STR_VERSION

from viewer.__data__ import ARE_YOU_SURE_YOU_WANTO_TO
from viewer.__data__ import OK
from viewer.__data__ import IBM_ZKVM
from viewer.__data__ import BACK


#
# CONSTANTS
#


#
# CODE
#
class Summary:
    """
    Confirm the last option
    """

    def __init__(self, screen, device, data):
        """
        Constructor

        @type  screen: SnackScreen
        @param screen: SnackScreen instance
        """

        self.__screen = screen
        self.__device = device
        self.__data = data

        self.__textbox = Textbox(40, 10, "", scroll = 1)
        self.__buttonsBar = ButtonBar(self.__screen, [(OK.localize(), "ok"),
            (BACK.localize(), "back")])

        self.__grid = GridForm(self.__screen, IBM_ZKVM.localize() % STR_VERSION, 1, 3)
        self.__grid.add(self.__textbox, 0, 0)
        self.__grid.add(self.__buttonsBar, 0, 1)

    # __init__()

    def run(self):
        """
        Draws the screen

        @rtype: boolean
        @returns: sucess status
        """

        summary = ""

        self.__textbox.setText(summary)

        result = self.__grid.run()

        self.__screen.popWindow()

        rc = self.__buttonsBar.buttonPressed(result)

        return rc
    # run()

# SelectHardDisk
