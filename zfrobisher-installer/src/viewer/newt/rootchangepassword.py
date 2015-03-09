#
# IMPORTS
#
from snack import *
from model.config import STR_VERSION

from viewer.__data__ import OK
from viewer.__data__ import BACK
from viewer.__data__ import PASSWD_LABEL
from viewer.__data__ import PASSWD_CONFIRM_LABEL
from viewer.__data__ import PASSWD_WINDOW_TITLE
from viewer.__data__ import PASSWD_WINDOW_MSG
from viewer.__data__ import ERROR_PASSWD_LENGTH
from viewer.__data__ import ERROR_PASSWD_LENGTH_MSG
from viewer.__data__ import ERROR_PASSWD_MISMATCH
from viewer.__data__ import ERROR_PASSWD_MISMATCH_MSG


#
# CONSTANTS
#


#
# CODE
#
class RootChangePassword:
    """
    Represents the root change password screen
    """

    def __init__(self, screen):
        """
        Constructor

        @type  screen: SnackScreen
        @param screen: SnackScreen instance
        """
        self.__screen = screen

        msg = TextboxReflowed(40, PASSWD_WINDOW_MSG.localize())

        self.__buttonsBar = ButtonBar(self.__screen, [(OK.localize(), "ok"),
            (BACK.localize(), 'back')])

        self.__passwd = Entry(24, "", password=1)
        self.__passwdConfirm = Entry(24, "", password=1)

        passwdLabel = Label(PASSWD_LABEL.localize())
        passwdConfirmLabel = Label(PASSWD_CONFIRM_LABEL.localize())

        passwdGrid = Grid(2, 2)
        passwdGrid.setField(passwdLabel, 0, 0, anchorLeft=1)
        passwdGrid.setField(passwdConfirmLabel, 0, 1, anchorLeft=1)
        passwdGrid.setField(self.__passwd, 1, 0)
        passwdGrid.setField(self.__passwdConfirm, 1, 1)

        self.__grid = GridForm(self.__screen, PASSWD_WINDOW_TITLE.localize(), 1, 3)
        self.__grid.add(msg, 0, 0)
        self.__grid.add(passwdGrid, 0, 1, (0, 1, 0, 0))
        self.__grid.add(self.__buttonsBar, 0, 2, (0, 1, 0, 0))
    # __init__()

    def run(self):
        """
        Shows screen once

        @rtype: integer
        @returns: status of operation
        """
        self.__grid.setCurrent(self.__passwd)
        self.__screen.refresh()
        result = self.__grid.run()
        self.__screen.popWindow()

        return (self.__buttonsBar.buttonPressed(result), self.__passwd.value(), self.__passwdConfirm.value())

    # run()

    def showErrorLength(self):
        """
        Displays an error about the password length

        @rtype: nothing
        @returns: nothing
        """
        ButtonChoiceWindow(self.__screen, ERROR_PASSWD_LENGTH.localize(),
                           ERROR_PASSWD_LENGTH_MSG.localize(),
                           buttons=[(OK.localize(), 'ok')],
                           width=50)
    # showErrorLength()

    def showErrorMismatch(self):
        """
        Displays an error about the password mismatch

        @rtype: nothing
        @returns: nothing
        """
        ButtonChoiceWindow(self.__screen, ERROR_PASSWD_MISMATCH.localize(),
                           ERROR_PASSWD_MISMATCH_MSG.localize(),
                           buttons=[(OK.localize(), 'ok'), (BACK.localize(),
                               'back')],
                           width = 50)
    # showErrorLength()

# RootChangePassword
