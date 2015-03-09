#
# IMPORTS
#
from snack import *
from viewer.__data__ import HELP_LINE
from viewer.__data__ import ADDZFCP_MSG
from viewer.__data__ import OK
from viewer.__data__ import BACK
from viewer.__data__ import ADDZFCP_WINDOW_TITLE
from viewer.__data__ import DEVNO_LABEL
from viewer.__data__ import WWID_LABEL
from viewer.__data__ import LUNID_LABEL

#
# CONSTANTS
#

#
#CODE
#

class AddzFCP:
    """
    Get the scsi by parameters
    """
    def __init__(self, screen):
        """
        Constructor

        @type  screen: SnackScreen
        @param screen: SnackScreen instance
        """
        textboxWidth = 50
        self.__screen = screen
        self.__screen.pushHelpLine(HELP_LINE.localize())
        self.__msg = TextboxReflowed(textboxWidth, ADDZFCP_MSG.localize())
        devnoLabel = Label(DEVNO_LABEL.localize())
        wwidLabel = Label(WWID_LABEL.localize())
        lunidLabel = Label(LUNID_LABEL.localize())
        self.__devno = Entry(24,"")
        self.__wwid = Entry(24,"")
        self.__lunid = Entry(24,"")
        zfcpGrid = Grid(2,4)
        zfcpGrid.setField(devnoLabel, 0, 0, anchorLeft=1)
        zfcpGrid.setField(wwidLabel, 0, 1, anchorLeft=1)
        zfcpGrid.setField(lunidLabel, 0, 2, anchorLeft=1)
        zfcpGrid.setField(self.__devno, 1, 0, (1, 0, 0, 0))
        zfcpGrid.setField(self.__wwid, 1, 1, (1, 0, 0, 0))
        zfcpGrid.setField(self.__lunid, 1, 2, (1, 0, 0, 0))

        self.__buttonBar = ButtonBar(self.__screen, [(OK.localize(), "ok"), (BACK.localize(), "back")])

        self.__grid = GridForm(self.__screen, ADDZFCP_WINDOW_TITLE.localize(), 1, 3)

        self.__grid.add(self.__msg, 0, 0)
        self.__grid.add(zfcpGrid, 0, 1, (0, 1, 0, 1))
        self.__grid.add(self.__buttonBar, 0, 2)
    #__init__()

    def run(self):
        """
        Show sreen once
        @rtype: string
        @returns: status of operation
        """
        self.__grid.setCurrent(self.__devno)
        result = self.__grid.run()
        self.__screen.popWindow()
        return (self.__buttonBar.buttonPressed(result), self.__devno.value(), self.__wwid.value(),
                self.__lunid.value())
    # run()

    def showError(self, error):
        """
        Displays an error returned from addFCP

        @rtype: nothing
        @returns: nothing
        """
        ButtonChoiceWindow(self.__screen, ADDZFCP_WINDOW_TITLE.localize(),
                           error,
                           buttons=[(OK.localize(), 'ok')],
                           width=50)

#AddzFCP
