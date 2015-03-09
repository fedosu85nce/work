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
class Confirmation:
    """
    Confirm the last option
    """

    def __init__(self, screen, selectedDisks, partitioner):
        """
        Constructor

        @type  screen: SnackScreen
        @param screen: SnackScreen instance
        """

        self.__screen = screen
        self.__selectedDisks = selectedDisks
        self.__partitioner = partitioner

        disks = ','.join([temp.name for temp in self.__selectedDisks])
        pvs = self.__partitioner.getDelPvs()
        vgs = self.__partitioner.getDelVgs()

        self.__msg = TextboxReflowed(60, ARE_YOU_SURE_YOU_WANTO_TO.localize() % (disks, pvs, vgs))
        self.__buttonsBar = ButtonBar(self.__screen, [(OK.localize(), "ok"),
            (BACK.localize(), "back")])

        self.__grid = GridForm(self.__screen, IBM_ZKVM.localize() % STR_VERSION, 1, 3)
        self.__grid.add(self.__msg, 0, 1)
        self.__grid.add(self.__buttonsBar, 0, 2)

    # __init__()

    def run(self):
        """
        Draws the screen

        @rtype: boolean
        @returns: sucess status
        """

        result = self.__grid.run()
        self.__screen.popWindow()

        rc = self.__buttonsBar.buttonPressed(result)

        return rc == "ok"
    # run()

# SelectHardDisk
