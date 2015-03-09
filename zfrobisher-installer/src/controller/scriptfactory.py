#
# IMPORTS
#
from scripthandler import ScriptHandler

from modules.installauto.installauto import InstallAuto
from modules.installauto.parsecustomizationks import ParseCustomizationKS
from modules.execscripts.execprescripts import ExecPreScripts
from modules.identifysystem.identifysystem import IdentifySystem
from modules.automounter.automounter import AutoMounter
from modules.network.networktopology import NetworkTopology
from modules.rootpassword.rootpassword import RootPassword
from modules.timezone.timezone import Timezone
from modules.network.netdevice import NetDevice
from modules.network.netsetup import NetSetup
from modules.execscripts.execpostscripts import ExecPostScripts
from modules.finalsetup.finalsetup import FinalSetup
from modules.selinuxrelabelfs.selinuxrelabelfs import SelinuxRelabelFS
from modules.automounter.autoumounter import AutoUmounter
from modules.network.dns import DNS
from modules.network.ntp import NTP

#
# CODE
#
class ScriptFactory(object):
    """
    Factory to creates and subscribes all scripts necessary to execute when
    event happens
    """

    def __new__(klass, *args, **kwargs):
        """
        Overwritten method to implement Factory design pattern, allowing to
        create specified objects according given parameters.

        @type  *args: tuple
        @param *args: given parameters to handle object

        @type  **kwargs: dict
        @param **kwargs: given parameters separated by keywords

        @rtype: ScriptHandler
        @returns: script handler with all scripts subscribed
        """
        # creates a scripthandler object
        klass.__handler = ScriptHandler()

        """
        Subscribe the scripts in the order that they will be executed
        (don't forget to import it) ie: klass.__handler.subscribe(MyScript())
        Keep the list below update in case of any change!
        Modules type and order:
        - Pre install modules:
            + InstallAuto
            + ParseCustomizationKS
            + NetworkTopology
            + NetDevice
            + ExecPreScripts
            + IdentifySystem
        - Post install modules:
            + AutoMounter *must* be the first post install modules
            + RootPassword
            + Timezone
            + NetSetup
            + DNS
            + ExecPostScripts
            + FinalSetup
            + SelinuxRelabelFS
            + AutoUmounter *must* be the last post install modules
        """

        klass.__handler.subscribe(InstallAuto())
        klass.__handler.subscribe(ParseCustomizationKS())
        klass.__handler.subscribe(NetworkTopology())
        klass.__handler.subscribe(NetDevice())
        klass.__handler.subscribe(ExecPreScripts())
        klass.__handler.subscribe(IdentifySystem())
        # AutoMounter *must* be the first post install modules
        klass.__handler.subscribe(AutoMounter())
        klass.__handler.subscribe(RootPassword())
        klass.__handler.subscribe(Timezone())
        klass.__handler.subscribe(NetSetup())
        klass.__handler.subscribe(DNS())
        klass.__handler.subscribe(NTP())
        klass.__handler.subscribe(ExecPostScripts())
        klass.__handler.subscribe(FinalSetup())
        klass.__handler.subscribe(SelinuxRelabelFS())
        # AutoUmounter *must* be the last post install modules
        klass.__handler.subscribe(AutoUmounter())

        return klass.__handler
    # __new__()

# ScriptFactory
