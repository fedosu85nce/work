#
# IMPORTS
#
from snack import *
from viewer import Viewer
from newt.menu import Menu
from newt.selectharddisk import SelectHardDisk
from newt.addzfcp import AddzFCP
from newt.confirmation import Confirmation
from newt.checkharddisk import CheckHardDisk
from newt.installprogress import InstallProgress
from newt.rebootsystem import RebootSystem
from newt.entitlementerror import EntitlementError
from newt.confirmreinstall import ConfirmReinstall
from newt.reinstallerror import ReinstallError
from newt.upgradeprogress import UpgradeProgress
from newt.messagewindow import MessageWindow
from newt.rootchangepassword import RootChangePassword
from newt.adjusttimezone import AdjustTimezone
from newt.chooselanguage import ChooseLanguage
from newt.listnetworkifaces import ListNetworkifaces
from newt.networkconfig import NetworkConfig
from newt.dnssetup import DNSSetup
from newt.ntpsetup import NTPSetup
from newt.generaltoperror import GeneralTopError
from newt.datetimesetup import DateTimeSetup
from newt.installationsummary import InstallationSummary
from newt.firstscreen import FirstScreen
from newt.licensewindow import LicenseMainWindow
from newt.ifaceconfig import InterfaceConfig
from newt.partitioncfg.partition_interface import PartitionInterface

from __data__ import HELP_LINE

#
# CODE
#
class NewtViewer(Viewer):
    """
    Newt implementation for the installer interface
    """
    def __init__(self):
        """
        Constructs a complete viewer for installer

        @rtype:   nothing
        @returns: nothing
        """
        self.__screen = SnackScreen()
        self.__screen.pushHelpLine(HELP_LINE.localize())
    # __init__()

    def destructor(self):
        """
        Finishes newt screen
        """
        self.__screen.finish()
    # destructor()

    def getMenu(self):
        """
        Creates and returns a Menu screen object

        @rtype:   Menu
        @returns: screen object
        """
        return Menu(self.__screen)
    # getMenu()

    def getReinstallConfirmation(self, installed_disk=None):
        """
        Creates and returns a Reinstall Confirmation screen object.

        @type  installed_disk: String
        @param installed_disk: The disk where zKVM was installed

        @rtype: ConfirmReinstall
        @return: ConfirmReinstall screen instance
        """
        return ConfirmReinstall(self.__screen, installed_disk)
    # getReinstallConfirmation()

    def getReinstallError(self):
        """
        Creates and returns a Reinstall Error screen object.

        @rtype: ReinstallError
        @return: ReinstallError screen instance
        """
        return ReinstallError(self.__screen)
    # getReinstallError()

    def getDiskSelectionError(self):
        """
        Creates and return a Disk Selection screen object

        @rtype:   SelectHardDisk
        @returns: screen object
        """
        return SelectHardDisk(self.__screen)
    # getDiskSelectionError()

    def getDiskSelection(self, partitioner, lunset):
        """
        Creates and returns a Disk Selection screen object

        @type  storage: Blivet
        @param storage: Blivet instance

        @type  lunset: Set
        @param lunset: LUN set that user have specified

        @rtype:   SelectHardDisk
        @returns: screen object
        """
        window = SelectHardDisk(self.__screen)
        window.setDisks(partitioner, lunset)

        return window
    # getDiskSelection()

    def getPartitioning(self, partitioner):
        return PartitionInterface(self.__screen, partitioner)

    def getAddzFCP(self):
        """
        Creates and returns a AddzFCP screen object

        @rtype:   getAddzFCP
        @returns: screen object
        """
        return AddzFCP(self.__screen)
    # getAddzFCP()

    def getConfirmation(self, device, partitioner):
        """
        Creates and returns a Confirmation screen object

        @rtype:   Confirmation
        @returns: screen object
        """
        return Confirmation(self.__screen, device, partitioner)
    # getConfirmation()

    def getCheckHardDisk(self, diskSelected):
        """
        Creates and returns a Check Hard Disk screen object

        @type  diskSelected: str
        @param diskSelected: disk selected by user

        @rtype:   CheckHardDisk
        @returns: screen object
        """
        return CheckHardDisk(self.__screen, diskSelected)
    # getCheckHardDisk()

    def getInstallProgress(self):
        """
        Creates and returns a Install Progress screen object

        @rtype:   InstallProgress
        @returns: screen object
        """
        return InstallProgress(self.__screen)
    # getInstallProgress()

    def getRebootSystem(self):
        """
        Creates and returns a Reboot System screen object

        @rtype:   RebootSystem
        @returns: screen object
        """
        return RebootSystem(self.__screen)
    # getRebootSystem()

    def getEntitlementError(self):
        """
        Creates and returns a Entilement Error screen object

        @rtype:   EntitlementError
        @returns: screen object
        """
        return EntitlementError(self.__screen)
    # getEntitlementError()

    def getUpgradeProgressScreen(self):
        """
        Creates and returns a Upgrade Progress screen object

        @rtype:   UpgradeProgress
        @returns: screen object
        """
        return UpgradeProgress(self.__screen)
    # getUpgradeProgressScreen()

    def getMessageWindow(self):
        """
        Creates a message box

        @rtype:   message box
        @returns: screen object
        """
        return MessageWindow(self.__screen)
    # getMessageWindow()

    def getRootPasswdWindow(self):
        """
        Creates and returns the Root Change Password screen object

        @rtype:   RootChangePassword
        @returns: screen object
        """
        return RootChangePassword(self.__screen)
    # getRootPasswdWindow()

    def getTimezoneWindow(self):
        """
        Creates and returns the Adjust Timezone screen object

        @rtype:   AdjustTimezone
        @returns: screen object
        """
        return AdjustTimezone(self.__screen)
    # getTimezoneWindow()

    def getChooseLanguage(self):
        """
        Creates and returns the Choose Language screen object

        @rtype:   AdjustTimezone
        @returns: screen object
        """
        return ChooseLanguage(self.__screen)
    # getChooseLanguage()

    def getListNetwork(self):
        """
        Creates and returns the List of Network Interfaces screen object

        @rtype:   ListNetworkifaces
        @returns: screen object
        """
        return ListNetworkifaces(self.__screen)
    # getListNetwork()

    def getNetworkConfig(self, device, macaddr):
        """
        Creates and returns the network config screen

        @rtype:   ConfigNetwork
        @returns: screen object
        """
        return NetworkConfig(self.__screen, device, macaddr)
    # getNetworkConfig()

    def getIfaceConfig(self, address):
        """
        Creates and returns the interface config screen

        @rtype:   InterfaceConfig
        @returns: screen object
        """
        return InterfaceConfig(self.__screen, address)

    def getDnsSetup(self, data):
        """
        Creates and returns the dnssetup screen

        @rtype:   DnsSetup
        @returns: screen object
        """
        return DNSSetup(self.__screen, data)
    # getDnsSetup()

    def getNTPSetup(self):
        """
        Creates and returns the ntpsetup screen

        @rtype:   NTPSetup
        @returns: screen object
        """
        return NTPSetup(self.__screen)
    # getNTPSetup()

    def getGeneralTopError(self):
        """
        Creates and returns a General Top Error screen object

        @rtype:   GeneralTopError
        @returns: screen object
        """
        return GeneralTopError(self.__screen)
    # getGeneralTopError()

    def getDateTimeSetup(self):
        """
        Creates and returns the datetimesetup screen

        @rtype:   DateTimeSetup
        @returns: screen object
        """
        return DateTimeSetup(self.__screen)
    # getDateTimeSetup()

    def getSummary(self, device, data):
        """
        Creates and returns the summary screen

        @rtype:   Summary
        @returns: screen object
        """
        return InstallationSummary(self.__screen, device, data)
    # getSummary()

    def getFirstScreen(self):
        """
        Creates and returns the introdution screen

        @rtype:   FirstScreen
        @returns: screen object
        """
        return FirstScreen(self.__screen)
    # getSummary()

    def getLicenseWindow(self):
        """
        Creates and returns the license window screen

        @rtype:   license
        @returns: screen object
        """
        return LicenseMainWindow(self.__screen)
    # getLicenseWindow()

# NewtViewer
