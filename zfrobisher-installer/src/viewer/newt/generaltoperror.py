#!/usr/bin/python

#
# IMPORTS
#
from snack import *
from model.config import STR_VERSION
from model.config import IBMZKVM_TARBALL_ERROR_LOG
from viewer.__data__ import OK
from viewer.__data__ import IBM_ZKVM
from viewer.__data__ import ZKVM_ERROR_MSG
from viewer.__data__ import ZKVM_LOG_MSG
from viewer.__data__ import IBMZKVMERROR_ERROR
from viewer.__data__ import IBMZKVMERROR_UNKNOWN


#
# CONSTANTS
#


#
# CODE
#
class GeneralTopError:
    """
    Screen when hardware is not entitled
    """

    def __init__(self, screen):
        """
        Constructor

        @type  screen: SnackScreen
        @param screen: SnackScreen instance
        """
        self.__screen = screen
        self.__title = IBM_ZKVM.localize() % STR_VERSION

        self.__msg = ZKVM_ERROR_MSG.localize() % IBMZKVMERROR_ERROR.localize()
        self.__errorMsg = IBMZKVMERROR_UNKNOWN.localize()
        self.__logMsg = ZKVM_LOG_MSG.localize() % IBMZKVM_TARBALL_ERROR_LOG
    # __init__()

    def run(self, code = []):
        """
        Displays an error when there is any error during installation

        @type code: str
        @param code: error code

        @rtype: nothing
        @returns: nothing
        """
        if len(code) == 2:
            msg = ZKVM_ERROR_MSG.localize() % code[0]
            errorMsg = code[1]
        else:
            msg = self.__msg
            errorMsg = self.__errorMsg

        table = []
        table.append(msg)
        table.append(errorMsg)
        table.append(self.__logMsg)

        ButtonChoiceWindow(self.__screen, self.__title,
                '\n'.join(table),
                buttons=[(OK.localize(), 'ok')],
                width = 50)
    # run()

# GeneralTopError
