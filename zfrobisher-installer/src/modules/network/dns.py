#!/usr/bin/python

#
# IMPORTS
#
from controller.zkvmerror import ZKVMError
from modules.scriptbase import ScriptBase

import os
import traceback
import logging

#
# CONSTANTS
#
CONFIG_FILE="/etc/resolv.conf"


#
# CODE
#
class DNS(ScriptBase):
    """
    Edit the DNS configuration on the system
    """

    def __init__(self):
        """
        Constructor
        """
        self.__configFile = self.__parseConfigFile()
        self.__logger = logging.getLogger(__name__)
    # __init__()

    def onPostInstall(self, data):
        """
        Handles the post install event

        @type  data: dict
        @param data: relevant arguments for that given event

        @rtype: None
        @returns: Nothing
        """
        try:
            mountDir = data['model'].get('mountDir')

            # no dns to be configured, return
            if not data['model'].get('dns'):
                return

            dns = data['model'].get('dns')

            # update resolv.conf
            resolv = mountDir + CONFIG_FILE
            fd = open(resolv, 'w')

            if dns['primary']:
                fd.write('nameserver %s\n' % dns['primary'])
                self.__logger.debug("Primary DNS: %s" % dns['primary'])

            if dns['secondary']:
                fd.write('nameserver %s\n' % dns['secondary'])
                self.__logger.debug("Secondary DNS: %s" % dns['secondary'])

            if dns['search']:
                fd.write('search %s\n' % dns['search'])
                self.__logger.debug("Search %s" % dns['search'])

            fd.close()

            # update hostname
            if dns['hostname']:
                os.popen('echo "%s" > %s/etc/hostname' % (dns['hostname'], mountDir))
                self.__logger.debug("Hostname: %s" % dns['hostname'])

        except Exception as e:
            self.__logger.critical("Failed DNS module!")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("POSTINSTALL", "DNS", "POST_MODULES")

    # onPostInstall()

    def __parseConfigFile(self):
        """
        Parse CONFIG_FILE and returns a dictionary with the data

        @rtype: dict
        @returns: dictionary with the configuration file content parsed
        """
        result = {}

        if not os.path.exists(CONFIG_FILE):
            return result

        fd = open(CONFIG_FILE)
        content = fd.readlines()
        fd.close()

        for line in content:
            if line.startswith(";") or line.startswith("#"):
                continue

            if line.strip() == '':
                continue

            key = line.split()[0].strip()
            value = line.split(key)[1].strip()

            if key == "nameserver":
                key = "primaryDNS"

                if key in result.keys():
                    key = "secondaryDNS"

            result[key] = value

        return result
    # __parseConfigFile()

    def write(self):
        """
        Write new CONFIG_FILE

        @rtype: None
        @returns: nothing
        """
        fd = open(CONFIG_FILE, "w")

        primaryDNS = self.__configFile.get("primaryDNS")
        secondaryDNS = self.__configFile.get("secondaryDNS")
        searchList = self.__configFile.get("search")

        if primaryDNS:
            fd.write("nameserver %s\n" % primaryDNS)

        if secondaryDNS:
            fd.write("nameserver %s\n" % secondaryDNS)

        if searchList:
            fd.write("search %s\n" % searchList)

        fd.close()
    # write()

    def setPrimaryDNS(self, value):
        """
        Sets the primary DNS IP address

        @type  value: string
        @param value: primary DNS IP address

        @rtype: None
        @returns: nothing
        """
        self.__configFile["primaryDNS"] = value
    # setPrimaryDNS()

    def getPrimaryDNS(self, default = ""):
        """
        Returns the primary DNS IP address

        @rtype: string
        @returns: primary DNS IP address
        """
        primaryDNS = self.__configFile.get("primaryDNS")

        if primaryDNS is not None:
            return primaryDNS

        return default
    # getPrimaryDNS()

    def setSecondaryDNS(self, value):
        """
        Sets the secondary DNS IP address

        @type  value: string
        @param value: secondary DNS IP address

        @rtype: None
        @returns: nothing
        """
        self.__configFile["secondaryDNS"] = value
    # setSecondaryDNS()

    def getSecondaryDNS(self, default = ""):
        """
        Returns the secondary DNS IP address

        @rtype: string
        @returns: secondary DNS IP address
        """
        secondaryDNS = self.__configFile.get("secondaryDNS")

        if secondaryDNS is not None:
            return secondaryDNS

        return default
    # getSecondaryDNS()

    def setSearchList(self, value):
        """
        Sets the search list

        @type  value: string
        @param value: search list

        @rtype: None
        @returns: nothing
        """
        self.__configFile["search"] = value
    # setSecondaryDNS()

    def getSearchList(self, default = ""):
        """
        Returns the search list

        @rtype: string
        @returns: search list
        """
        searchList = self.__configFile.get("search")

        if searchList is not None:
            return searchList

        return default
    # getSecondaryDNS()
#DNS
