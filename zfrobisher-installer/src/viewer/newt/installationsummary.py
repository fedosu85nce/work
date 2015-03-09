#
# IMPORTS
#
from snack import *
from model.config import STR_VERSION
from viewer.__data__ import BACK
from viewer.__data__ import OK
from viewer.__data__ import IBM_ZKVM
from viewer.__data__ import INSTALLATION_SUMMARY
from viewer.__data__ import DEVICE
from viewer.__data__ import PASSWORD_IS_SET
from viewer.__data__ import NETWORK
from viewer.__data__ import IP_ADDRESS
from viewer.__data__ import TIMEZONE
from viewer.__data__ import DATE_TIME
from viewer.__data__ import NTP_SERVERS
from viewer.__data__ import NTP_DISABLED
from viewer.__data__ import GATEWAY
from viewer.__data__ import NETMASK
from viewer.__data__ import HOSTNAME
from viewer.__data__ import DHCP_IS_ENABLE
from viewer.__data__ import BRIDGE
from viewer.__data__ import SYSTEM_CLOCK_USES_UTC
from viewer.__data__ import YES
from viewer.__data__ import NO
from viewer.__data__ import DNSSETUP_HOSTNAME_LABEL
from viewer.__data__ import DNSSETUP_FST_DNS_LABEL
from viewer.__data__ import DNSSETUP_SND_DNS_LABEL
from viewer.__data__ import DNSSETUP_SEARCH_LABEL



#
# CONSTANTS
#


#
# CODE
#
class InstallationSummary(object):
    """
    Builds a screen to show a confirmation message before wipe root device and
    reinstall system.
    """

    def __init__(self, screen, selectedDisks, data):
        """
        Constructor.

        @type  screen: SnackScreen
        @param screen: SnackScreen instance

        @rtype: None
        @return: Nothing
        """
        self.__screen = screen
        self.__selectedDisks = selectedDisks
        self.__data = data

        self.__textbox = Textbox(40, 10, "", scroll = 1)
        self.__msg = TextboxReflowed(40, INSTALLATION_SUMMARY.localize())

        self.__buttonsBar = ButtonBar(self.__screen, [(OK.localize(), "ok"),
            (BACK.localize(), "back")])

        self.__grid = GridForm(self.__screen, IBM_ZKVM.localize() % STR_VERSION, 1, 3)
        self.__grid.add(self.__msg, 0, 0)
        self.__grid.add(self.__textbox, 0, 1)
        self.__grid.add(self.__buttonsBar, 0, 2)
    # __init__()

    def run(self):
        """
        Draws the screen

        @rtype: integer
        @returns: sucess status
        """

        networks = self.__data['model'].get('network')
        dtime = self.__data['model'].get('datetime')
        dns_list = self.__data['model'].get('dns')
        disk = self.__data['model'].get('disk')
        password = self.__data['model'].get('pass')
        timezone = self.__data['model'].get('tz')
        utc = self.__data['model'].get('isUTC')

        summary = '\n' + DEVICE.localize() + \
                  ','.join([temp.name for temp in self.__selectedDisks])

        summary += '\n\n' + PASSWORD_IS_SET.localize()

        if networks:
            summary += "\n\n" + NETWORK.localize()

            for network in networks:
                summary += "\n" + DEVICE.localize() +  network['device']

                if network['bootProto'] == 'dhcp':
                    summary += "\n" + DHCP_IS_ENABLE.localize()
                else:
                    if network['ip']:
                        summary += "\n" + IP_ADDRESS.localize() + network['ip']

                    if network['gateway']:
                        summary += "\n" + GATEWAY.localize() + network['gateway']

                    if network['netmask']:
                        summary += "\n" + NETMASK.localize() + network['netmask']

                    if network['hostname']:
                        summary += "\n" + HOSTNAME.localize() + network['hostname']

                summary += "\n" + BRIDGE.localize()
                summary += YES.localize() if network['bridge'] else NO.localize()


        if dns_list:
            summary += "\n\nDNS\n"

            if dns_list['hostname']:
                summary += DNSSETUP_HOSTNAME_LABEL.localize() + ": "
                summary += str(dns_list['hostname']) + "\n"

            if dns_list['primary']:
                summary += DNSSETUP_FST_DNS_LABEL.localize() + ": "
                summary += str(dns_list['primary']) + "\n"

            if dns_list['secondary']:
                summary += DNSSETUP_SND_DNS_LABEL.localize() + ": "
                summary += str(dns_list['secondary']) + "\n"

            if dns_list['search']:
                summary += DNSSETUP_SEARCH_LABEL.localize() + ": "
                summary += str(dns_list['search']) + "\n"


        summary += "\n" + TIMEZONE.localize() + timezone + "\n"

        summary += "\n" + SYSTEM_CLOCK_USES_UTC.localize()

        summary += YES.localize() if utc else NO.localize()

        summary += "\n\n" + DATE_TIME.localize() + str(dtime[0]) + "/" + str(dtime[1]) +\
                "/" + str(dtime[2]) + " " + str(dtime[3]) + ":" + str(dtime[4]) +\
                ":" + str(dtime[5])

        ntpservers = self.__data['model'].get('ntpservers')

        summary += "\n\n"

        if ntpservers:
            summary += NTP_SERVERS.localize() + "\n"
            for i in self.__data['model'].get('ntpservers'):
                summary += "* "+ i + "\n"
        else:
            summary += NTP_DISABLED.localize() + "\n"

        summary += "\n\n"

        self.__textbox.setText(summary)

        result = self.__grid.run()
        self.__screen.popWindow()

        return self.__buttonsBar.buttonPressed(result)
    # run()

# InstallationSummary
