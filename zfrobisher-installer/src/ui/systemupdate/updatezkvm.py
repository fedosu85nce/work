#!/usr/bin/python

#
# IMPORTS
#
from snack import *
from ui.systemupdate.listharddisks import ListHardDisks
from ui.systemupdate.updateprogress import UpdateProgress


#
# CONSTANTS
#


#
# CODE
#
class UpdatezKVM:
    """
    Update zKVM system
    """

    def __init__(self, screen):
        """
        Constructor

        @type  screen: SnackScreen
        @param screen: SnackScreen instance
        """
        self.__screen = screen
    # __init__()

    def run(self):
        """
        Draws the each screen of the installation application

        @rtype: integer
        @returns: success status
        """
        app = [
            ListHardDisks,
            UpdateProgress,
          ]

        index = 0

        while index > -1 and index < len(app):
            window = app[index](self.__screen)
            rc = window.run()
            self.__screen.popWindow()

            if rc == -1:
                index -= 1
            else:
                index += 1

        if index == -1:
            return -1

        return 0
    # run()
# UpdatezKVM()
