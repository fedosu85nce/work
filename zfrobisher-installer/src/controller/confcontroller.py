#
# IMPORTS
#
from viewer.newtviewer import NewtViewer
from modules.timezone.timezone import Timezone

import crypt
import datetime
import logging


#
# CONSTANTS
#
LOG_FILE_NAME = "/var/log/kopconfig.log"
LOG_FORMATTER = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


#
# CODE
#
class ConfController(object):
    """
    Orchestrates the installer
    """

    def __init__(self, model, viewer, data):
        """
        Constructs the controller

        rtype:   nothing
        returns: nothing
        """
        # create logger
        logging.basicConfig(filename=LOG_FILE_NAME,
                            level=logging.DEBUG,
                            format=LOG_FORMATTER)
        self.__logger = logging.getLogger(__name__)
        self.__logger.setLevel(logging.DEBUG)

        self.__model = model
        self.__viewer = viewer
        self.__data = data
    # __init__()

    def wizard(self, diskSelected, partitioner):
        """
        Runs the config in wizard mode

        @rtype: nothing
        @returns: nothing
        """
        index = 1
        while True:
            if index == 1:
                res = self.rootPasswordChange()
                if res == 'back':
                    return res
                else:
                    index = 2

            if index == 2:
                res = self.setTimezone()
                if res == 'back':
                    index = 1
                else:
                    index = 3

            if index == 3:
                res = self.ntpSetup()
                if res == 'back':
                    index = 2
                else:
                    index = 4

            if index == 4:
                res = self.dateTimeSetup()
                if res == 'back':
                    index = 3
                elif res == 4:
                    continue
                else:
                    index = 5

            if index == 5:
                res = self.InterfaceSetup()
                if res == 'back':
                    index = 4
                elif res == 'edit':
                    index = 6
                else:
                    index = res

            if index == 6:
                res = self.dnsSetup()
                if res == 'back':
                    index = 5
                else:
                    index = 7

            if index == 7:
                res = self.Summary(diskSelected, self.__data)
                if res == 'back':
                    index = 6
                else:
                    index = 8

            if index == 8:
                keep_going = self.__viewer.getConfirmation(diskSelected, partitioner).run()
                if not keep_going:
                    index = 7
                else:
                    # Write partition changes to disk
                    partitioner.submitChanges()
                    break

    # wizard()

    def menu(self):
        """
        Runs the config in menu of choices mode

        @rtype: nothing
        @returns: nothing
        """
        pass
    # menu()

    def rootPasswordChange(self):
        """
        Handles the Root Change Password screen

        @rtype:   nothing
        @returns: nothing
        """
        self.__logger.info('Root Password Change screen')

        while True:

            # call the root password screen
            viewer = self.__viewer.getRootPasswdWindow()
            res, passwd, confirm = viewer.run()

            if res == 'back':
                return res

            # check password length
            if len(passwd) < 6:
                viewer.showErrorLength()
                continue

            # check password confirmation
            elif passwd != confirm:
                viewer.showErrorMismatch()
                continue

            # hash passwd for shadow file (sha512)
            hashPasswd = crypt.crypt(passwd, '$6$')
            self.__data['model'].insert('pass', hashPasswd)
            self.__data['model'].insert('isCrypted', True)

            self.__logger.info('Root password changed successfuly')
            return
    # rootPasswordChange()

    def setTimezone(self):
        """
        Handles the timezone screen

        @rtype: nothing
        @returns: nothing
        """
        self.__logger.info('Adjust Timezone screen')

        # get timezone module
        timezone = Timezone()

        # call the window passing a list with all timezones available
        viewer = self.__viewer.getTimezoneWindow()
        res, zone, utc = viewer.run(timezone.getEntries())

        if res == "back":
            return res

        # setup the selected timezone/utc
        if res == 'ok':
            self.__data['model'].insert('tz', zone)
            self.__data['model'].insert('isUTC', utc)
            self.__logger.info('Timezone: %s, UTC: %s' % (zone, str(utc)))
    # setTimezone()

    def InterfaceSetup(self):
        """
        Handles the list of network ifaces to be configured

        @rtype: nothing
        @returns: nothing
        """
        self.__logger.info('listNetworkIfaces screen')

        # call the window
        viewer = self.__viewer.getListNetwork()
        res, eth, macaddr = viewer.run()

        if res == "back":
            return res

        while True:
            # Proceed to next screen after  network configuration
            if res == 'next' or not eth:
                self.__logger.info('Network configuration go to NEXT screen')
                return 6

            if macaddr is None:
                # active the selected  network interface
                self.interfaceConfig(eth)
                return 5
            else:
                # configure the network for the selected iface
                res = self.networkConfig(eth, macaddr)
            if res == "back" or res == "ok":
                return 5
            else:
                return res

    def interfaceConfig(self, address):
        """
        Configures the unactived interfaces selected

        @type: basestr
        @param: interface bus ID to be configured

        @rtype: nothing
        @returns: nothing
        """
        self.__logger.info('ConfigInterface Screen')

        retry_values = None
        while True:
            viewer = self.__viewer.getIfaceConfig(address)
            try:
                if retry_values and retry_values['retry_p']:
                    viewer.setPortNumberDefault(retry_values['retry_p'])
                if retry_values and retry_values['retry_n']:
                    viewer.setPortNameDefault(retry_values['retry_n'])
            except:
                # just ignore it and use the default values...
                pass

            res, iface, macaddr, retry_values = viewer.run()
            if res == "back":
                return res
            if res == "ok":
                return self.networkConfig(iface, macaddr)
            if res == "retry":
                continue

    # interfaceConfig

    def networkConfig(self, iface, macaddr):
        """
        Configures the network interface selected

        @type: basestr
        @param: net iface to be configured

        @rtype: nothing
        @returns: nothing
        """
        self.__logger.info('configNetwork screen')

        while True:
            # call the window
            viewer = self.__viewer.getNetworkConfig(iface, macaddr)
            res, networkData = viewer.run()

            if res == "back":
                return res

            if res == 'ok':

                data = []

                # append the network data in the list if
                # there is already another device to be
                # configured
                if self.__data['model'].get('network'):
                    data = self.__data['model'].get('network')
                    # ensure only one entry per NIC on network list
                    for i in data:
                        if i.get('device') == networkData.get('device'):
                            data.remove(i)
                data.append(networkData)
                self.__data['model'].insert('network', data)
                self.__logger.info(str(data))

                return res
    # networkConfig()

    def dnsSetup(self):
        """
        Configures the DNS

        @rtype: nothing
        @returns: nothing
        """
        self.__logger.info('dnsSetup screen')

        # call the window
        viewer = self.__viewer.getDnsSetup(self.__data)
        res, dnsData = viewer.run()
        if res == 'back':
            return res

        # store the dns data
        if res == 'ok':
            self.__data['model'].insert('dns', dnsData)
            self.__logger.info(str(dnsData))
        else:
            self.__data['model'].insert('dns', [])
        return res
    # dnsSetup()

    def ntpSetup(self):
        """
        Configures the NTP

        @rtype: nothing
        @returns: nothing
        """
        self.__logger.info('NTPsetup screen')

        # call the window
        viewer = self.__viewer.getNTPSetup()
        res, ntpData = viewer.run()
        if res == 'back':
            return res

        # store the dns data
        if res == 'ok':
            self.__data['model'].insert('ntpservers', ntpData)
            self.__logger.info("NTP server list: %s" % str(ntpData))
            return res
    # NTPSetup()

    def dateTimeSetup(self):
        """
        Configures the Date time

        @rtype: nothing
        @returns: nothing
        """
        self.__logger.info('DateTime screen')

        # call the window
        viewer = self.__viewer.getDateTimeSetup()
        res, rdata = viewer.run()
        if res == 'back':
            return res

        date_str = rdata[0] + "/" + rdata[1] + "/" + rdata[2] + " " + rdata[3] + \
            ":" + rdata[4] + ":" + rdata[5]

        self.__logger.info('Date inputed: %s' % date_str)
        try:
            datetime.datetime.strptime(date_str, "%Y/%m/%d %H:%M:%S")
        except:
            viewer.showErrorWrongFormat(date_str)
            #stay
            return 4

        # store the dns data
        if res != 'back':
            self.__data['model'].insert('datetime', rdata)
            return res
    # datetimesetup()

    def Summary(self, device, data):
        """
        Show summary of the installation

        @rtype: nothing
        @returns: nothing
        """
        self.__logger.info('Summary')

        # call the window
        viewer = self.__viewer.getSummary(device, data)
        res = viewer.run()

        return res
    # datetimesetup()

# ConfController
