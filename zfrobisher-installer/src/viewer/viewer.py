#
# Code
#
class Viewer(object):
    """
    Base interface for KoP installer viewer
    """

    def getMenu(self):
        """
        Creates and returns a Menu screen object

        @rtype:   Menu
        @returns: screen object
        """
        raise NotImplementedError("getMenu not implemented")
    # getMenu()

    def getDiskSelection(self, disks, diskData, lvmData, raidData):
        """
        Creates and returns a Disk Selection screen object

        @type  disks: list
        @param disks: disks found in the system

        @type  diskData: dict
        @param diskData: detailed information about disks

        @type  lvmData: dict
        @param lvmData: lvm metadata

        @type  raidData: dict
        @param raidData: raid metadata
        
        @rtype:   SelectHardDisk
        @returns: screen object
        """
        raise NotImplementedError("getDiskSelection not implemented")
    # getDiskSelection()

    def getAddzFCP(self):
        """
        Creates and returns a AddzFCP screen object

        @rtype:   getAddzFCP
        @returns: screen object
        """
        raise NotImplementedError("getAddzFCP not implemented")
    # getAddzFCP()

    def getConfirmation(self, device, diskData, lvmData):
        """
        Creates and confirm the Confirmation screen object

        @rtype:   getConfirmation
        @returns: screen object
        """
        raise NotImplementedError("getConfirmation not implemented")
    # getDiskSelection()

    def getCheckHardDisk(self, diskSelected):
        """
        Creates and returns a Check Hard Disk screen object

        @type  diskSelected: str
        @param diskSelected: disk selected by user

        @rtype:   CheckHardDisk
        @returns: screen object
        """
        raise NotImplementedError("getCheckHardDisk not implemented")
    # getCheckHardDisk()

    def getInstallProgress(self):
        """
        Creates and returns a Install Progress screen object

        @rtype:   InstallProgress
        @returns: screen object
        """
        raise NotImplementedError("getInstallProgress not implemented")
    # getInstallProgress()

    def getEntitlementError(self):
        """
        Creates and returns a Entilement Error screen object

        @rtype:   EntitlementError
        @returns: screen object
        """
        raise NotImplementedError("getEntitlementError not implemented")
    # getEntitlementError()

    def getRebootSystem(self):
        """
        Creates and returns a Reboot System screen object

        @rtype:   RebootSystem
        @returns: screen object
        """
        raise NotImplementedError("getRebootSystem not implemented")
    # getRebootSystem()

    def getUpgradeProgressScreen(self):
        """
        Creates and returns a Upgrade Progress screen object

        @rtype:   UpgradeProgress
        @returns: screen object
        """
        raise NotImplementedError("getUpgradeProgressScreen not implemented")
    # getUpgradeProgressScreen()

    def getMessageWindow(self):
        """
        Gets a generic message box

        @rtype:   message window box
        @returns: screen object
        """
        raise NotImplementedError("MessageWindow not implemented")
    # getMessageWindow()

    def getRootPasswdWindow(self):
        """
        Creates and returns the Root Change Password screen object

        @rtype:   RootChangePassword
        @returns: screen object
        """
        raise NotImplementedError("RootChangePassword not implemented")
    # getRootPasswdWindow()

    def getTimezoneWindow(self):
        """
        Creates and returns the Adjust Timezone screen object

        @rtype:   AdjustTimezone
        @returns: screen object
        """
        raise NotImplementedError("getTimezoneWindow not implemented")
    # getTimezoneWindow()

    def getChooseLanguage(self):
        """
        Creates and returns the choose language screen object

        @rtype:   ChooseLanguage
        @returns: screen object
        """
        raise NotImplementedError("getChooseLanguage not implemented")
    # getChooseLanguage()

    def getListNetwork(self):
        """
        Creates and returns the List of Network Interfaces screen object

        @rtype:   ListNetworkifaces
        @returns: screen object
        """
        raise NotImplementedError("getListNetwork not implemented")
    # getListNetwork()

    def getNetworkConfig(self, device, macaddr):
        """
        Creates and returns the network config screen

        @rtype:   ConfigNetwork
        @returns: screen object
        """
        raise NotImplementedError("getNetworkConfig not implemented")
    # getNetworkConfig()

    def getDnsSetup(self):
        """
        Creates and returns the dnssetup screen

        @rtype:   DnsSetup
        @returns: screen object
        """
        raise NotImplementedError("getDnsSetup not implemented")
    # getDnsSetup()

    def getDateTimeSetup(self):
        """
        Creates and returns the datetime setup screen

        @rtype:   datetimesetup
        @returns: screen object
        """
        raise NotImplementedError("getDateTimeSetup not implemented")
    # getDateTimeSetup()

    def getSummary(self):
        """
        Creates and returns the summary screen

        @rtype:   summary
        @returns: screen object
        """
        raise NotImplementedError("getSummary not implemented")
    # getSummary()

    def getFirstScreen(self):
        """
        Creates and returns the first screen

        @rtype:   first
        @returns: screen object
        """
        raise NotImplementedError("getFirstScreen not implemented")
    # getFirstScreen()

    def getLicenseWindow(self):
        """
        Creates and returns the license window screen

        @rtype:   license
        @returns: screen object
        """
        raise NotImplementedError("getLicenseWindow not implemented")
    # getLicenseWindow()

    def getIfaceConfig(self, address):
        """
        Creates and returns the network interface configuration

        @rtype:   InterfaceConfig
        @returns: screen object
        """
        raise NotImplementedError("getIfaceConfig not implemented")
    # getIfaceConfig

# Viewer
