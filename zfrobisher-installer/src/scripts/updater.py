"""Updates the IBM zKVM system, given an update image or repository

This program should only be used, in case your system cannot directly access the Internet.
Otherwise, you should refer to the normal yum tools

Usage: ibm-update-system [OPTIONS] --iso-path=file
       ibm-update-system [OPTIONS] --url=repository

Options:

    -h
    --help
        Print this message and exit.

    -v
    --version
        Display version information and exit.

    -y
    --yes
        Assumes yes to answers

    -i
    --iso-path=
        Path to iso image containing updates

    -u
    --url=
        URL (http/ftp) to iso image containing updates

    -U
    --upgrade
        Upgrade between IBM zKVM releases

"""

import sys
import os
import getopt
import subprocess
import yum
import urllib
import urllib2
import shutil
from tempfile import mkdtemp
from yum import logging
from yum.rpmtrans import RPMBaseCallback
from yum.constants import TS_INSTALL_STATES, TS_REMOVE_STATES
from contextlib import contextmanager

__version__ = "1.4"
__appname__ = "ibm-update-system"

#
# CONSTANTS AND DEFINITIONS
#
FOLLOW_PROGRESS = {"operation": "",
                   "percent": "",
                   "package": ""
                   }
__defproduct = "ibm_zkvm"
__releasefile = '/etc/system-release'
__repofile = '/etc/yum/vars/ibmver'
__fprint_file = '.discinfo'
__full_iso_file = 'LiveOS/squashfs.img'
__gkey = 'file:///etc/pki/rpm-gpg/RPM-GPG-KEY-ibm_powerkvm'


def usage(code, msg=''):
    if code == 0:
        print >> sys.stderr, __doc__
    if msg:
        print >> sys.stderr, msg
    if code > 0:
        print >> sys.stderr, "Try '%s --help' for more information." % __appname__
    sys.exit(code)


def banner():
    sys.stdout.write("%s" % '='*int(len(__appname__) + len(__version__) + 1))
    sys.stdout.write("\n")
    sys.stdout.write("%s %s" % (__appname__, __version__))
    sys.stdout.write("\n")
    sys.stdout.write("%s" % '='*int(len(__appname__) + len(__version__) + 1))
    sys.stdout.write("\n")


def infoMsg(message):
    sys.stdout.write("%s\n" % message)


def getProductName():
    if os.path.isfile(__releasefile):
        with open(__releasefile, 'r') as f:
            line = f.readline()
            product = line.split('release')[0].strip().lower()
            msg = '\tProduct name: %s' % product
            infoMsg(msg)
            return product
    msg = '\tProduct name: %s' % __defproduct
    infoMsg(msg)
    return __defproduct


def getRepoVersion():
    if os.path.isfile(__repofile):
        with open(__repofile, 'r') as f:
            line = f.readline()
            version = line.rstrip('\n').strip()
            msg = '\tProduct base version: %s' % version
            infoMsg(msg)
            return version
    return None


def checkVersions(iso_path, upgrade):
    _result = {'action': None,
               'currentVer': None,
               'upgradeVer': None,
               }
    _filename = os.path.join(iso_path, __fprint_file)
    _msg = 'Invalid or inconsistent update image'
    if os.path.isfile(_filename):
        _pname = getProductName()
        _pversion = getRepoVersion()
        if _pversion is not None:
            with open(_filename, 'r') as _file:
                for line in _file:
                    sline = line.lower().rstrip('\n').strip()
                    if sline.startswith(_pname):
                        updver = sline.split(_pname)[1].strip()
                        msg = '\tUpdate base version: %s' % updver
                        infoMsg(msg)
                        # regular update
                        if updver.startswith(_pversion):
                            _result['action'] = 'update'
                            return _result
                        # release upgrade
                        elif upgrade:
                            _full_iso_filename = os.path.join(iso_path,
                                                              __full_iso_file)
                            if os.path.isfile(_full_iso_filename):
                                # upgrade from 2.1.0 to 2.1.1
                                if _pversion == '2.1.0' and updver == '2.1.1':
                                    _result['action'] = 'upgrade'
                                    _result['currentVer'] = _pversion
                                    _result['upgradeVer'] = updver
                                    return _result
                                    # _msg = ("Upgrades from %s to %s are not supported "
                                    #         "in this version (%s) of the %s tool. "
                                    #         "Please update your system to get this "
                                    #         "function enabled." % (_pversion, updver,
                                    #                                __version__, __appname__))
                                else:
                                    _msg = "Invalid upgrade from %s to %s" % (_pversion, updver)
                            else:
                                _msg = "System can not be upgraded using an \
update ISO. Upgrade operation is only allowed when using release ISO."
                            raise RuntimeError(_msg)
                _msg = 'Unknown or invalid update image version'
        else:
            _msg = 'Could not identify system base version'
    raise RuntimeError(_msg)


def findRepo(mntpoint):
    repo = os.path.join(mntpoint, 'repodata')
    if os.path.exists(repo):
        return mntpoint
    else:
        repo = os.path.join(mntpoint, 'packages/repodata')
        if os.path.exists(repo):
            return os.path.join(mntpoint, 'packages')
    raise RuntimeError('Could not find a valid update repository')


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hvyi:u:U',
                                   ['help', 'version', 'yes', 'iso-path=', 'url=', 'upgrade'])
    except getopt.error, msg:
        usage(1, msg)

    if not opts:
        usage(1, 'No options provided')

    if args:
        usage(1, 'Invalid extra argument(s) provided')

    repoURL = None
    assumeYes = False
    choosen = None
    upgrade = False

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage(0)
        elif opt in ('-v', '--version'):
            print >> sys.stderr, __appname__, __version__
            sys.exit(0)
        elif opt in ('-y', '--yes'):
            assumeYes = True
        elif opt in ('-i', '--iso-path'):
            if repoURL is not None:
                usage(1, 'Should select only one update source (either iso or URL)')
            if not arg:
                usage(1, 'Missing path to update ISO image')
            repoURL = arg
            choosen = "iso"
        elif opt in ('-u', '--url'):
            if repoURL is not None:
                usage(1, 'Should select only one update source (either iso or URL)')
            if not arg:
                usage(1, 'Missing URL to update image repository')
            repoURL = arg
            choosen = "url"
        elif opt in ('-U', '--upgrade'):
            upgrade = True
    if not repoURL:
        usage(1, 'Missing path or URL to update image')

    banner()
    if not os.getuid() == 0:
        infoMsg("Must have root privileges")
        sys.exit(1)

    _tmpdir = setup()
    _xitcode = 0
    _mnt = False

    try:
        _mntpoint = mountISO(repoURL, _tmpdir, choosen)
        _mnt = True
        infoMsg("Checking versions...")
        _checkVer = checkVersions(_mntpoint, upgrade)
        _repo = findRepo(_mntpoint)
        path = "file://" + _repo
        infoMsg("Checking available updates...")
        with pushd(_tmpdir):
            if _checkVer['action'] == 'update':
                update(path, assumeYes, _tmpdir)
            elif _checkVer['action'] == 'upgrade':
                doUpgrade(path, assumeYes, _tmpdir, _checkVer)
    except Exception as e:
        msg = 'Aborting... %s' % str(e)
        infoMsg(msg)
        _xitcode = 1

    if _mnt:
        umountISO(_tmpdir)

    cleanup(_tmpdir)
    sys.exit(_xitcode)


@contextmanager
def pushd(dir):
    _cwd = os.getcwd()
    os.chdir(dir)
    yield
    os.chdir(_cwd)


def downloadISO(iso, tmpdir):
    file_name = os.path.join(tmpdir, iso.split('/')[-1])
    infoMsg("Downloading the image: " + iso)

    def dlProgress(count, blockSize, totalSize):
        percent = int(count*blockSize*100/totalSize)
        sys.stdout.write("\r" + iso + "...%d%%" % percent)
        sys.stdout.flush()

    request = urllib2.Request(iso)
    try:
        urllib2.urlopen(request)
    except urllib2.HTTPError:
        infoMsg('The specified server returned an error reponse.')
        raise
    except urllib2.URLError:
        infoMsg('Could not connect to the server.')
        raise

    urllib.urlretrieve(iso, file_name, reporthook=dlProgress)
    sys.stdout.write("\n")
    sys.stdout.flush()
    return file_name


def mountISO(iso, tmpdir, choosen):
    mount_point = os.path.join(tmpdir, 'iso')
    os.makedirs(mount_point)

    if choosen == "url":
        iso = downloadISO(iso, tmpdir)

    infoMsg("Mounting image...")

    if not os.path.exists(iso):
        raise RuntimeError("File " + iso + " does not exist")

    cmd = "mount -o loop %s %s 2>/dev/null" % (iso, mount_point)

    if subprocess.call(cmd, shell=True) == 1:
        raise RuntimeError('Error mounting update image')

    return mount_point


def umountISO(tmpdir):

    mount_point = os.path.join(tmpdir, 'iso')
    cmd = "umount %s 2>/dev/null" % mount_point

    if subprocess.call(cmd, shell=True) == 1:
        raise RuntimeError('Error umounting update image')


def setup():
    _tempwrk = mkdtemp('', 'ibmupd-', '/tmp')
    return _tempwrk


def cleanup(tmpdir):

    shutil.rmtree(tmpdir)


def check_yes_or_no():
    input = None

    while input is None:
        input = raw_input("\nDo you want to proceed? (y/N) ")

        if input.lower() == "y" or input.lower() == "yes":
            input = True
        elif input.lower() == "n" or input.lower() == "no":
            input = False
        else:
            input = None

    return input


def doUpgrade(path, assumeYes, tmpdir, checkVer):
    # test upgrade befora proceed
    usrInput = update(path, assumeYes, tmpdir, True, True)

    if usrInput:
        # upgrade release from 2.1.0 to 2.1.1
        if checkVer['currentVer'] == '2.1.0' and checkVer['upgradeVer'] == '2.1.1':
            # instantiate yum object
            yb = yum.YumBase()

            # disable all repos
            yb.repos.disableRepo('*')

            basecache = os.path.join(tmpdir, 'yum')
            if not os.path.isdir(basecache):
                os.makedirs(basecache)

            # configure yum parameters
            yb.conf.gpgcheck = True
            yb.conf.assumeyes = True
            yb.conf.cache = 0
            yb.conf.basecachedir = basecache

            # create a temporary repo to point to zkvm packages
            newrepo = yum.yumRepo.YumRepository('zkvm')
            newrepo.name = 'zkvm'
            newrepo.baseurl = [path]
            newrepo.basecachedir = yb.conf.basecachedir
            newrepo.gpgcheck = True
            newrepo.gpgkey = __gkey
            yb.repos.add(newrepo)
            yb.repos.enableRepo(newrepo.id)
            yb.doRepoSetup(thisrepo=newrepo.id)

            try:
                yb.pkgSack
            except RuntimeError as e:
                raise RuntimeError('Error creating yum instance: %s' % e)

            ylg = yum.logging.getLogger("yum.verbose.YumBase")
            ylg.setLevel(logging.CRITICAL)

            # mark to zkvm2_1_1-release to update
            searchlist = ['name']
            args = ["zkvm2_1_1-release"]
            matching = yb.searchGenerator(searchlist, args)
            for (po, matched_value) in matching:
                if po.name == "zkvm2_1_1-release":
                    try:
                        yb.update(po)
                    except:
                        pass

            # build and process the batch transaction
            (rescode, restring) = yb.resolveDeps()
            if rescode == 1:
                errorMsg = "Error while resolving dependency."
                if len(restring) >= 1:
                    errorMsg = str(restring)
                raise Exception(errorMsg)
            rescode, restring = yb.buildTransaction()
            if rescode == 1:
                errorMsg = "Error while building transaction."
                if len(restring) >= 1:
                    errorMsg = str(restring)
                raise Exception(errorMsg)
            yb.processTransaction()

            ylg.setLevel(logging.DEBUG)

            # close yum instance
            yb.closeRpmDB()
            yb.close()

            # execute update
            update(path, True, tmpdir, False, False)
        else:
            raise Exception("Invalid upgrade from %s to %s" % (checkVer['currentVer'], checkVer['upgradeVer']))


def update(path, assumeYes, tmpdir, verboseMode=True, testMode=False):

    usrInput = False

    # instantiate yum object
    yb = yum.YumBase()

    # disable all repos
    yb.repos.disableRepo('*')

    basecache = os.path.join(tmpdir, 'yum')
    if not os.path.isdir(basecache):
        os.makedirs(basecache)

    # configure yum parameters
    yb.conf.gpgcheck = True
    yb.conf.assumeyes = True
    yb.conf.cache = 0
    yb.conf.basecachedir = basecache

    # create a temporary repo to point to zkvm packages
    newrepo = yum.yumRepo.YumRepository('zkvm')
    newrepo.name = 'zkvm'
    newrepo.baseurl = [path]
    newrepo.basecachedir = yb.conf.basecachedir
    newrepo.gpgcheck = True
    newrepo.gpgkey = __gkey
    yb.repos.add(newrepo)
    yb.repos.enableRepo(newrepo.id)
    yb.doRepoSetup(thisrepo=newrepo.id)

    try:
        yb.pkgSack
    except RuntimeError as e:
        raise RuntimeError('Error creating yum instance: %s' % e)

    ylg = yum.logging.getLogger("yum.verbose.YumBase")
    ylg.setLevel(logging.CRITICAL)

    # mark all packages to install
    yb.repos.populateSack()
    yb.pkgSack.buildIndexes()

    updateObj = yb.up

    updatePackages = yb.doPackageLists('updates')

    update_package_list = []

    for i in updatePackages:
        update_package_list.append(i)

    update_package_list.sort()

    if verboseMode:
        infoMsg('================================================================================')
        infoMsg('Packages')
        infoMsg('================================================================================')

    if update_package_list:
        if verboseMode:
            print 'Updating:'
            for i in update_package_list:
                print '  ' + str(i)

        # mark packages to update
        for i in updatePackages:
            try:
                yb.update(i)
            except:
                pass

    obsolete_package_list = updateObj.getObsoletesList()
    # mark obsoleting packages to update
    if obsolete_package_list:
        if verboseMode:
            print 'Obsoleting:'

        for pkg in obsolete_package_list:
            try:
                if verboseMode:
                    print '  ' + str(pkg[0])
                yb.update(name=pkg[0])
            except:
                pass

    # install new packages
    installed_pkgs = yb.doPackageLists().installed
    available_pkgs = yb.doPackageLists().available

    install_package_list = list(set(available_pkgs) - set(installed_pkgs) -
                                set(update_package_list))
    install_package_list = list(sorted(install_package_list))

    if install_package_list:
        if verboseMode:
            print 'Installing'
            for i in install_package_list:
                print '  ' + str(i)

        # mark packages to install
        for pkg in install_package_list:
            try:
                yb.install(pkg)
            except:
                pass

    # execute
    try:
        if install_package_list or \
           update_package_list or \
           obsolete_package_list:

            if verboseMode:
                print '================================================================================'
                if install_package_list:
                    print 'Install: ' + str(len(install_package_list)) + ' pkgs'

                if update_package_list:
                    print 'Update: ' + str(len(update_package_list)) + ' pkgs'

                if obsolete_package_list:
                    print 'Obsoleting: ' + str(len(obsolete_package_list)) + ' pkgs'

            if not assumeYes:
                usrInput = check_yes_or_no()
            else:
                usrInput = True

            if usrInput:
                (rescode, restring) = yb.resolveDeps()
                if rescode == 1:
                    errorMsg = "Error while resolving dependency."
                    if len(restring) >= 1:
                        errorMsg = str(restring)
                    raise Exception(errorMsg)
                rescode, restring = yb.buildTransaction()
                if rescode == 1:
                    errorMsg = "Error while building transaction."
                    if len(restring) >= 1:
                        errorMsg = str(restring)
                    raise Exception(errorMsg)
                if not testMode:
                    yb.processTransaction(
                        None,
                        None,
                        UpdateCallback())
                    print "\n"
        else:
            if verboseMode:
                print 'No package updates found.'

    # cannot upgrade: re-raise exception
    except Exception, e:
        raise

    ylg.setLevel(logging.DEBUG)

    # close yum instance
    yb.closeRpmDB()
    yb.close()

    return usrInput


class UpdateCallback(RPMBaseCallback):
    def __init__(self):
        """
        Constructor

        @type  callback: method
        @param callback: user callback
        """
        # call parent constructor
        RPMBaseCallback.__init__(self)

        # create start lock
        self.__startLock = {}
        self.__lastpackage = ""
    # __init__()

    def errorlog(self, msg):
        """
        Dummy method. Just ignores any error messages sent from the RPM
        installation process.

        @type  msg: basestring
        @param msg: RPM installation error messages

        @rtype: None
        @returns: nothing
        """
        pass
    # errorlog()

    def event(self, package, action, bytesProcessed, bytesTotal, currentProcess, totalProcess):
        """
        Handles installation progress

        @type  package: basestring
        @param package: A yum package object or simple string of a package name

        @type  action: int
        @param action: A yum.constant transaction set state or in the obscure
                      rpm repackage case it could be the string 'repackaging'

        @type  bytesProcessed: int
        @param bytesProcessed: Current number of bytes processed in the transaction
                           element being processed

        @type  bytesTotal: int
        @param bytesTotal: Total number of bytes in the transaction element being
                         processed

        @type  currentProcess: int
        @param currentProcess: number of processes completed in whole transaction

        @type  totalProcess: int
        @param totalProcess: total number of processes in the transaction.

        @rtype:   None
        @returns: Nothing
        """
        # action is install: get package name and save state
        if action in TS_INSTALL_STATES:
            packageSplited = package._remote_url().split('/')
            packageName = packageSplited[len(packageSplited) - 1]
            state = 'Processing'

        # state is uninstall: get package name and save state
        elif action in TS_REMOVE_STATES:
            packageName = package
            state = 'Cleanup'

        # other action: ignore
        else:
            return

        # calculate percentage
        percentage = (float(bytesProcessed) / float(bytesTotal)) * 100

        # create message
        message = FOLLOW_PROGRESS

        # lock not exists: operation is starting
        if self.__startLock.get(packageName) is None:
            message['operation'] = '%s-start' % state
            self.__startLock[packageName] = True

        # percentage is 100: operation finish
        elif percentage == 100:
            message['operation'] = '%s-finish' % state

        # operation is running
        else:
            message['operation'] = '%s' % state

        # fill message dict
        message['percent'] = percentage
        message['package'] = packageName

        try:
            # break line when package change
            if self.__lastpackage != packageName:
                self.__lastpackage = packageName
                sys.stdout.write('\n')

            sys.stdout.write("\r%s (%s) %d%% [%d/%d]" % (state, packageName, percentage, currentProcess, totalProcess))
            sys.stdout.flush()

        except:
            print percentage
            pass

    # event()

    def filelog(self, package, action):
        """
        Dummy method. Just ignores any log messages sent from the RPM
        installation process.

        @type  package: basestring
        @param package: package name

        @type  action: basestring
        @param action: RPM installation log message

        @rtype: None
        @returns: nothing
        """
        pass
    # filelog()

    def scriptout(self, package, msgs):
        """
        Dummy method. Just ignores any scriptlet output messages sent from the
        RPM installation process.

        @type  package: basestring
        @param package: package name

        @type  msgs: basestring
        @param msgs: RPM scriptlet output messages

        @rtype: None
        @returns: nothing
        """
        pass
    # scriptout()

# UpdateCallback()

if __name__ == '__main__':
    main()
