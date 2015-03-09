#
# IMPORTS
#
from snack import *
from model.config import STR_VERSION

from viewer.__data__ import SELECT_ONE_OF_THE_OPTIONS_BELOW
from viewer.__data__ import WELCOME_IBM_ZKVM
from viewer.__data__ import HELP_LINE
from viewer.__data__ import BACK
from viewer.__data__ import OK

#
# CONSTANTS
#


#
# CODE
#
class Menu:
    """
    Welcome page for the installer application
    """

    def __init__(self, screen):
        """
        Constructor

        @type  screen: SnackScreen
        @param screen: SnackScreen instance
        """
        self.__screen = screen

        self.__msg = TextboxReflowed(40,
                SELECT_ONE_OF_THE_OPTIONS_BELOW.localize())
        self.__list = Listbox(5, returnExit=0)

        self.__buttonsBar = ButtonBar(self.__screen, [(OK.localize(), "ok"),
            (BACK.localize(), "back")])

        self.__grid = GridForm(self.__screen, WELCOME_IBM_ZKVM.localize() % STR_VERSION, 1, 3)
        self.__grid.add(self.__msg, 0, 0)
        self.__grid.add(self.__list, 0, 1, (0,1,0,0))
        self.__grid.add(self.__buttonsBar, 0, 2, (0,1,0,0))


        self.__screen.pushHelpLine(HELP_LINE.localize())
    # __init__()

    def run(self):
        """
        Draws the screen

        @rtype: integer
        @returns: sucess status
        """
        # run the list and show the window
        result = self.__grid.run()
        self.__screen.popWindow()

        rc = self.__buttonsBar.buttonPressed(result)

        # return the content to the controller
        return (rc, self.__list.current())
    # run()

    def setMenuOptions(self, options):
        """
        Configures which options will be displayed on KoP menu install.

        @type  options: list
        @param options: list with tuples ('text', optionKey)

        @rtype: None
        @return: Nothing
        """
        # invalid given parameter: abort
        if not isinstance(options, list):
            return

        # add options to screen list
        for opt in options:
            self.__list.append(opt[0], opt[1])

    # setMenuOptions()

# Menu
