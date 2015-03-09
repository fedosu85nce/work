#!/usr/bin/python

#
# IMPORTS
#
from controller.zkvmerror import ZKVMError
from modules.installauto.frobisherks import FrobisherKS
from modules.i18n.i18n import setLanguageKS
from modules.network.network import Network
from modules.scriptbase import ScriptBase
from model.disk import mount, umount
from model.config import KICKSTART_FILE
from subprocess import Popen, PIPE

import crypt
import logging
import os
import pprint
import re
import shutil
import traceback
import urllib

#
# CONSTANTS
#
CMD_FILE = '/proc/cmdline'
DEFAULT_KICKSTART_FILE = '/opt/ibm/zkvm-installer/kickstart/manufacture.ks'
REPO_PATH = 'file:///media/packages/'
ROOT_PASS = '$6$CN6lwYuX$CRY7I4gNcygJeMytuDPsZW7ODUyoE5e3HDztHznxnSK5d8hNGe3MjLo6JTAUMfzcSpsIcwvhJ1euKDVEXk.8n1'
TIME_ZONE = 'America/New_York'
LANG = 'en_US'


#
# CODE
#
class InstallAuto(ScriptBase):
    """
    Parser data required for auto installation.
    """

    def __init__(self):
        """
        Contructor
        """
        self.__data = {}
        self.__resetData()
        self.__kickstartFile = ''
        self.__logger = logging.getLogger(__name__)
    # __init()__

    def __resetData(self):
        """
        Reset data to default values.

        @rtype   : nothing
        @returns : nothing
        """
        self.__data = {
            'action': None,
            'repo': REPO_PATH,
            'lang': LANG,
            'disk': None,
            'datapoll': None,
            'pass': ROOT_PASS,
            'isCrypted': True,
            'tz': TIME_ZONE,
            'isUTC': False,
            'network': [],
            'preScripts': [],
            'postScripts': [],
            'mountDir': None,
            'isKickstart': False,
            'ntpservers': [],
        }
    # __resetData()

    def __downloadHttpFile(self):
        """
        Download config file for auto install via HTTP.

        @rtype  : nothing
        @returns: nothing
        """
        try:
            urllib.urlretrieve(self.__kickstartFile, KICKSTART_FILE)
            self.__kickstartFile = KICKSTART_FILE
        except Exception as e:
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("PREINSTALL", "INSTALLAUTO", "DOWNLOAD_HTTP")
    # __downloadHttpFile()

    def __downloadTftpFile(self):
        """
        Download config file for auto install via TFTP.

        @rtype  : nothing
        @returns: nothing
        """
        tftpServer = self.__kickstartFile[7:].split('/')[0]
        serverLen = len(tftpServer)
        tftpFile = self.__kickstartFile[7+serverLen+1:]
        proc = Popen(['tftp', tftpServer, '-c', 'get', tftpFile, KICKSTART_FILE], stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()
        if proc.returncode != 0:
            self.__logger.critical("Failed to download (TFTP) install auto file(%s) (exit code = %s):" % (self.__kickstartFile, proc.returncode))
            self.__logger.critical("%s" % err)
            raise ZKVMError("PREINSTALL", "INSTALLAUTO", "DOWNLOAD_TFTP")
        self.__kickstartFile = KICKSTART_FILE
    # __downloadTftpFile()

    def __downloadNfsFile(self):
        """
        Download config file for auto install via NFS.

        @rtype  : nothing
        @returns: nothing
        """
        try:
            nfsFile = self.__kickstartFile.split('/')[-1]
            nfsSections = self.__kickstartFile.split(':')
            if len(nfsSections) == 4:
                nfsDir = self.__kickstartFile.split(':')[3][:-len(nfsFile)]
                nfsOpts = self.__kickstartFile.split(':')[1]
                nfsServer = self.__kickstartFile.split(':')[2]
            else:
                nfsDir = self.__kickstartFile.split(':')[2][:-len(nfsFile)]
                nfsServer = self.__kickstartFile.split(':')[1]
                nfsOpts = ""
            if nfsOpts != "":
                nfsMount = "-o " + nfsOpts + " " + nfsServer + ":" + nfsDir
            else:
                nfsMount = nfsServer + ":" + nfsDir
            nfsMount = mount(nfsMount)
            nfsFile = os.path.join(nfsMount, nfsFile)
            shutil.copy(nfsFile, KICKSTART_FILE)
            umount(nfsMount)
            self.__kickstartFile = KICKSTART_FILE
        except Exception as e:
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("PREINSTALL", "INSTALLAUTO", "DOWNLOAD_NFS")
    # __downloadNfsFile()

    def __parserFile(self):
        """
        Parser config auto install file.

        @type  data: string
        @param data: if 'default', uses manufactory mode

        @rtype  : nothing
        @returns: nothing
        """
        # reset any previous data
        self.__resetData()

        try:
            self.__data['isKickstart'] = True
            if self.__kickstartFile == 'default':
                self.__kickstartFile = DEFAULT_KICKSTART_FILE
            else:
                # download install auto file if needed
                if self.__kickstartFile.startswith('http') or self.__kickstartFile.startswith('ftp'):
                    self.__downloadHttpFile()
                if self.__kickstartFile.startswith('tftp'):
                    self.__downloadTftpFile()
                if self.__kickstartFile.startswith('nfs'):
                    self.__downloadNfsFile()

            # check if kickstart is not empty
            if os.stat(self.__kickstartFile).st_size == 0:
                self.__logger.critical("Empty kickstart file: %s" % self.__kickstartFile)
                raise ZKVMError("PREINSTALL", "INSTALLAUTO", "PARSER_FILE")

            # parser the file and fill the dictionary
            with open(self.__kickstartFile) as fd:
                data = fd.read()
            fparser = FrobisherKS()
            fparser.readKickstartFromString(data)
            self.__logger.debug("Kickstart file => BEGIN")
            self.__logger.debug("Kickstart content:")
            for line in data.split("\n"):
                # hide password in case of not encrypted
                if line.lstrip(" ").startswith("rootpw"):
                    line = re.sub(' +', ' ', line.lstrip(" "))
                    if len(line.split(" ")) == 2:
                        line = "rootpw XXXXX"
                self.__logger.debug("%s" % line)
            self.__logger.debug("Kickstart file => END")

            if fparser.upgrade:
                self.__data['action'] = 'upgrade'
            elif fparser.reinstall:
                self.__data['action'] = 'reinstall'
            else:
                self.__data['action'] = 'install'
            if fparser.lang:
                self.__data['lang'] = fparser.lang
            # set language
            self.__logger.debug("Language to be set by kickstart: %s" % self.__data.get('lang'))
            langSet = setLanguageKS(self.__data.get('lang'))
            self.__logger.debug("Language effectively set: %s" % langSet)

            if fparser.rootPool:
                if len(fparser.rootPool.disk.split("=")) >= 1:
                    self.__data['disk'] = fparser.rootPool.disk
                else:
                    self.__logger.critical("No disk entry in kickstart file!")
                    raise ZKVMError("PREINSTALL", "INSTALLAUTO", "NO_DISK_KS")
            if fparser.dataPool:
                self.__data['dataPool'] = fparser.dataPool.disk
            if fparser.rootpw["password"]:
                if fparser.rootpw["isCrypted"]:
                    self.__logger.debug("Using encrypted password!")
                    self.__data['pass'] = fparser.rootpw["password"]
                else:
                    # hash passwd for shadow file (sha512)
                    self.__logger.debug("Encrypting password...")
                    self.__data['pass'] = crypt.crypt(fparser.rootpw["password"], '$6$')
                # Note tha even 'isCrypted' is set to false, starting at this
                # poin # password provided in kickstart will be encrypted for
                # the sake of security
                self.__data['isCrypted'] = fparser.rootpw["isCrypted"]
            if fparser.tzMap["timezone"]:
                self.__data['tz'] = fparser.tzMap["timezone"]
                self.__data['isUTC'] = fparser.tzMap["isUTC"]
                self.__data['nontp'] = fparser.tzMap["nontp"]
                self.__data['ntpservers'] = fparser.tzMap["ntpservers"]
            if fparser.networks:
                for net in fparser.networks:
                    info = {}
                    info['bootProto'] = net.bootProto
                    info['device'] = net.device
                    info['ip'] = net.ip
                    info['netmask'] = net.netmask
                    info['gateway'] = net.gateway
                    info['nameserve'] = net.nameserver
                    info['hostname'] = net.hostname
                    info['nodefroute'] = net.nodefroute
                    info['bridge'] = False
                    info['onboot'] = net.onboot
                    self.__data['network'].append(info)
            if fparser.preScripts:
                for script in fparser.preScripts:
                    info = {}
                    info['script'] = script.script
                    info['interp'] = script.interp
                    info['inChroot'] = script.inChroot
                    info['errorOnFail'] = script.errorOnFail
                    self.__data['preScripts'].append(info)
            if fparser.postScripts:
                for script in fparser.postScripts:
                    info = {}
                    info['script'] = script.script
                    info['interp'] = script.interp
                    info['inChroot'] = script.inChroot
                    info['errorOnFail'] = script.errorOnFail
                    self.__data['postScripts'].append(info)
        except ZKVMError:
            raise
        except Exception as e:
            self.__logger.critical("Could not parse install automation file.")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("PREINSTALL", "INSTALLAUTO", "PARSER_FILE")
    # __parserFile()

    def onPreInstall(self, data):
        """
        Handles the post install event

        @type  data: dict
        @param data: relevant arguments for that given event

        @rtype  : nothing
        @returns: nothing
        """
        try:

            self.__logger.info("Executing InstallAuto module (EVT_PRE_INSTALL).")
            # work on bootline command file.
            with open(CMD_FILE) as fd:
                # parser and store bootline command
                cmdLine = fd.read().rstrip().split()
            self.__logger.debug("Bootline:")
            for line in pprint.pformat(cmdLine).split('\n'):
                self.__logger.debug(line)

            # liveDVD parser
            for i in cmdLine:
                if i == "root=live:LABEL=ZKVM_LIVECD":
                    self.__logger.debug("Boot from liveDVD, trying to start network...")
                    Network.startLiveDVDNetwork()
                    break

            # kickstart parser
            for i in cmdLine:
                if i.startswith('kvmp.inst.auto='):
                    self.__kickstartFile = i[i.find('=')+1:]
                    self.__logger.debug("Kickstart file from bootline: %s" % self.__kickstartFile)
                    self.__parserFile()
                    break

            self.__logger.debug("Data Structure:")
            for line in pprint.pformat(self.__data).split('\n'):
                self.__logger.debug(line)
            for key, value in self.__data.iteritems():
                data['model'].insert(key, value)
        except ZKVMError:
            self.__logger.critical("Failed InstallAuto module")
            raise
        except Exception as e:
            self.__logger.critical("Failed InstallAuto module")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("PREINSTALL", "INSTALLAUTO", "PRE_MODULES")
    # onPreInstall()

# InstallAuto
