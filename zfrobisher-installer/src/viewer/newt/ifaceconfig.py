#
# IMPORTS
#
from modules.network.network import Network
from snack import Label, Entry, ButtonChoiceWindow
from snack import ButtonBar, GridForm, Grid
import re

from viewer.__data__ import OK
from viewer.__data__ import BACK
from viewer.__data__ import INTERFACE_DEVICE
from viewer.__data__ import ACTIVE_INTERFACE
from viewer.__data__ import PORT_NAME_LABEL
from viewer.__data__ import LAYER2_LABEL
from viewer.__data__ import PORT_NUMBER_LABEL
from viewer.__data__ import INVALID_PORT_NUMBER
from viewer.__data__ import INVALID_PORT_NAME
from viewer.__data__ import PORT_NAME_TOO_LONE
from viewer.__data__ import ONE_OR_MORE_FIELD_ERROR


#
# CONSTANTS
#

#
# CODE
#
class InterfaceConfig:
    """
    Represents the interface active screen
    """

    def __init__(self, screen, address):
        """
        Constructor

        @type  address: string
        @param address: interface bus address
        """

        self.__screen = screen
        self.__address = address
        self.__dev = Label(address)
        self.__devLabel = Label(INTERFACE_DEVICE.localize())
        self.__portName = Entry(9, "")
        self.__portNameLabel = Label(PORT_NAME_LABEL.localize())
        self.__layer2 = Label("1")
        self.__layer2Label = Label(LAYER2_LABEL.localize())
        self.__portNum = Entry(2, "")
        self.__portNumLabel = Label(PORT_NUMBER_LABEL.localize())
        self.__contentGrid = Grid(2, 4)
        self.__contentGrid.setField(self.__devLabel, 0, 0, anchorLeft=1)
        self.__contentGrid.setField(self.__portNameLabel, 0, 1, anchorLeft=1)
        self.__contentGrid.setField(self.__layer2Label, 0, 2, anchorLeft=1)
        self.__contentGrid.setField(self.__portNumLabel, 0, 3, anchorLeft=1)
        self.__contentGrid.setField(self.__dev, 1, 0, (1, 0, 0, 0))
        self.__contentGrid.setField(self.__portName, 1, 1, (1, 0, 0, 0))
        self.__contentGrid.setField(self.__layer2, 1, 2, (1, 0, 0, 0))
        self.__contentGrid.setField(self.__portNum, 1, 3, (1, 0, 0, 0))

        self.__buttonsBar = ButtonBar(self.__screen,
                                      [(OK.localize(),
                                       "ok"),
                                       (BACK.localize(),
                                       "back")])
        self.__grid = GridForm(self.__screen,
                               ACTIVE_INTERFACE.localize(),
                               1,
                               2)
        self.__grid.add(self.__contentGrid, 0, 0)
        self.__grid.add(self.__buttonsBar, 0, 1)
        self.__devName = ""
        self.__macAddr = ""
        self.setPortNumberDefault()
        self.setPortNameDefault()
    # __init__()

    def run(self):
        """
        Draws the screen
        """

        capital_check = re.compile('[0-9A-Z_]*$')

        result = self.__grid.run()
        self.__screen.popWindow()
        rc = self.__buttonsBar.buttonPressed(result)

        if rc == "ok":
            portNum = int(self.__portNum.value())
            portName = self.__portName.value()
            layer2 = True
            retry_values = {'retry_n': None, 'retry_p': None}
            # check the validity of the option
            if portNum not in [0, 1]:
                # TODO show an error dialog
                self.__showErrorMessage(INVALID_PORT_NUMBER.localize())
                retry_values['retry_n'] = self.__portName.value()
                return ("retry", None, None, retry_values)
            if len(portName) > 8:
                # TODO show an error dialog
                self.__showErrorMessage(PORT_NAME_TOO_LONE.localize())
                retry_values['retry_p'] = self.__portNum.value()
                return ("retry", None, None, retry_values)
            if re.match(capital_check, portName) is None:
                # TODO show an error dialog
                self.__showErrorMessage(INVALID_PORT_NAME.localize())
                retry_values['retry_p'] = self.__portNum.value()
                return ("retry", None, None, retry_values)
            # put options int the argument for znetconf
            argument, if_name, mac_addr =\
                Network.setInterfaceActived(self.__address,
                                            portName,
                                            portNum,
                                            layer2)
            self.__devName = if_name
            self.__macAddr = mac_addr

        return (rc, self.__devName, self.__macAddr, None)
    # run()

    def __showErrorMessage(self, message_str):
        ButtonChoiceWindow(self.__screen,
                           ONE_OR_MORE_FIELD_ERROR.localize(),
                           message_str,
                           buttons=[(OK.localize(), 'ok')],
                           width=50)
    # __showErrorMessage

    def setPortNumberDefault(self, port_num='0'):
        self.__portNum.set(port_num)
    # setPortNumberDefault

    def setPortNameDefault(self, port_name='OSAPORT'):
        self.__portName.set(port_name)
    # setPortNameDefault
