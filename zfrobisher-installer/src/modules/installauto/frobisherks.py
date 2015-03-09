#!/usr/bin/python

#
# IMPORTS
#
import pykickstart.commands as commands
from pykickstart.handlers.control import commandMap
from pykickstart.version import *
from pykickstart.parser import *
from pykickstart.base import *
from pykickstart.errors import *
from pykickstart.options import *

import gettext
_ = lambda x: gettext.ldgettext("pykickstart", x)


#
# CODE
#
class Partition(commands.partition.F18_Partition):

    def __init__(self, writePriority=130, *args, **kwargs):
        commands.partition.F18_Partition.__init__(self, writePriority, *args, **kwargs)
    # __init__()

    def parse(self, args):

        retval = commands.partition.F18_Partition.parse(self, args)

        if retval.mountpoint != "/" and retval.mountpoint != "/data":
            errorMsg = ("%s is not a valid mountpoint" % retval.mountpoint)
            raise KickstartValueError(formatErrorMsg(self.lineno, msg=errorMsg))
        if not retval.disk:
            errorMsg = ("Target disk not definned for %s. Please use --ondisk." % retval.mountpoint)
            raise KickstartParseError(formatErrorMsg(self.lineno, msg=errorMsg))
        return retval
    # parser()
# Partition


class Frobisher_Reinstall(KickstartCommand):
    removedKeywords = KickstartCommand.removedKeywords
    removedAttrs = KickstartCommand.removedAttrs

    def __init__(self, writePriority=0, *args, **kwargs):
        KickstartCommand.__init__(self, writePriority, *args, **kwargs)
        self.reinstall = kwargs.get("reinstall", None)
        self.op = self._getParser()
    # __init__()

    def __str__(self):
        retval = KickstartCommand.__str__(self)

        if self.reinstall is None:
            return retval

        if self.reinstall:
            retval += "# Reinstall existing installation\nreinstall\n"
        else:
            retval += "# Install OS instead of reinstall\ninstall\n"

        return retval
    # __str__()

    def _getParser(self):
        op = KSOptionParser()
        return op
    # _getParser()

    def parse(self, args):
        (opts, extra) = self.op.parse_args(args=args, lineno=self.lineno)

        if len(extra) > 0:
            raise KickstartValueError(formatErrorMsg(self.lineno, msg=_("Kickstart command %s does not take any arguments") % "reinstall"))

        if self.currentCmd == "reinstall":
            self.reinstall = True
        else:
            self.reinstall = False

        return self
    # parser()
# Frobisher_Reinstall

commandMap[DEVEL]["part"] = Partition
commandMap[DEVEL]["partition"] = Partition
commandMap[DEVEL]["reinstall"] = Frobisher_Reinstall

superclass = returnClassForVersion()


class FrobisherHandlers(superclass):
    def __init__(self, mapping={}):
        superclass.__init__(self, mapping=commandMap[DEVEL])
    # __init__()
# FrobisherHandlers


class FrobisherKS():

    def __init__(self):
        self.ksparser = KickstartParser(FrobisherHandlers())
        self.lang = ""
        self.rootPool = ""
        self.dataPool = ""
        self.tzMap = {
            "timezone": "",
            "isUTC": False,
            "nontp": False,
            "ntpservers": []
        }
        self.rootpw = {
            "password": "",
            "isCrypted": False,
        }
        self.upgrade = False
        self.resintall = False
        self.networks = []
        self.preScripts = []
        self.postScripts = []
    # __init__()

    def initDataStructures(self):
        self.lang = self.ksparser.handler.lang.lang
        for part in self.ksparser.handler.partition.partitions:
            if part.mountpoint == "/":
                self.rootPool = part
            else:
                self.dataPool = part
        self.tzMap["timezone"] = self.ksparser.handler.timezone.timezone
        self.tzMap["isUTC"] = self.ksparser.handler.timezone.isUtc
        self.tzMap["nontp"] = self.ksparser.handler.timezone.nontp
        self.tzMap["ntpservers"] = self.ksparser.handler.timezone.ntpservers
        self.rootpw["password"] = self.ksparser.handler.rootpw.password
        self.rootpw["isCrypted"] = self.ksparser.handler.rootpw.isCrypted
        self.upgrade = self.ksparser.handler.upgrade.upgrade
        self.reinstall = self.ksparser.handler.reinstall.reinstall
        if self.upgrade and self.reinstall:
            raise Exception("reinstall and upgrade are not valid commands when used together")
        self.networks = self.ksparser.handler.network.network
        for script in self.ksparser.handler.scripts:
            if script.type == constants.KS_SCRIPT_PRE:
                self.preScripts.append(script)
            else:
                self.postScripts.append(script)
    # initDataStructures()

    def readKickstartFromString(self, ks):
        self.ksparser.readKickstartFromString(ks)
        self.initDataStructures()
    # readKickstartFromString()
# FrobisherKS
