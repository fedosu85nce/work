# -*- coding: utf-8 -*-

#
# IMPORTS
#
from snack import *
from model.config import STR_VERSION

from viewer.__data__ import WELCOME_IBM_ZKVM
from viewer.__data__ import LICENSE_BUTTON_ACCEPT
from viewer.__data__ import LICENSE_BUTTON_DECLINE
from viewer.__data__ import OK
from viewer.__data__ import BACK


#
# CONSTANTS
#
ACCEPT_LABEL = 'accept'
DECLINE_LABEL = 'decline'
OK_LABEL = 'ok'
BACK_LABEL = 'back'


#
# CODE
#
class LicenseMainWindow(object):
    """
    Implements the license main window
    """
    def __init__(self, screen):
        """
        Constructor
        """
        self.__screen = screen
        self.__msg  = Textbox(70, 8, "", scroll = 1, wrap = 1)
        self.__acceptButton = ButtonBar(self.__screen, [(LICENSE_BUTTON_ACCEPT.localize(), ACCEPT_LABEL)])
        self.__declineButton = ButtonBar(self.__screen, [(LICENSE_BUTTON_DECLINE.localize(), DECLINE_LABEL)])
        self.__defaultButton = ButtonBar(self.__screen, [(OK.localize(), OK_LABEL), (BACK.localize(), BACK_LABEL)])

        self.__grid = GridForm(self.__screen, WELCOME_IBM_ZKVM.localize() % STR_VERSION, 1, 5)
        self.__grid.add(self.__msg, 0, 0)
    # __init__()

    def run(self, text, accept):
        """
        Displays the window to the user

        @type  text: basestr
        @param text: license to be displayed

        @type  accept: bool
        @param accept: the screen should display 'accept/decline' buttons
                       'back/next' are default

        @rtype: nothing
        @returns: nothing
        """
        if accept:
            self.__grid.add(self.__acceptButton, 0, 2)
            self.__grid.add(self.__declineButton, 0, 4)

        else:
            self.__grid.add(TextboxReflowed(70, '  '), 0, 1)
            self.__grid.add(self.__defaultButton, 0, 2)

        self.__msg.setText(text)
        self.__screen.refresh()
        result = self.__grid.run()
        self.__screen.popWindow()

        if accept and self.__acceptButton.buttonPressed(result) == ACCEPT_LABEL:
            return True

        elif not accept and self.__defaultButton.buttonPressed(result) == OK_LABEL:
            return True

        return False
    # run()

# LicenseMainWindow
