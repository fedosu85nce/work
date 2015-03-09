#!/usr/bin/python

#
# IMPORTS
#
import os
import sys

from yum import YumBase


#
# CONSTANTS
#


#
# CODE
#
def main(directory, version):
    """
    Update packages in directory and install all those available

    @type  directory: string
    @param directory: path to the directory which contains a copy of the whole system

    @type  version: string
    @param version: zKVM version used to update system

    @rtype: boolean
    @returns: True if the packages was successfully updated;
              False otherwise
    """
    os.chroot(directory)

    # update all packages
    yumBase = YumBase()

    # get all enabled repos
    enabledRepos = yumBase.repos.listEnabled()

    # disable all yum repos
    yumBase.repos.disableRepo('*')

    # enable only the zkvm repo
    yumBase.repos.enableRepo('zkvm-%s' % version)

    # update system
    yumBase.update()

    rc, msgs = yumBase.buildTransaction()
    if rc != 2:
        return False

    try:
        yumBase.processTransaction()
    except:
        return False

    # check if there is more than one kernel installed
    # if so, remove one
    availableKernels = yumBase.searchPackages(['name'], ['kernel'])
    installedKernels = 0

    for pkg in availableKernels:
        if pkg.repoid == 'installed' and pkg.name == 'kernel':
            installedKernels += 1

    if installedKernels != 1:
        yumBase.remove(name='kernel')

    # install new packages available in the repo
    pkgs = yumBase.doPackageLists().available
    for pkg in pkgs:
        yumBase.install(pkg)

    # build and process the YUM transaction
    rc, msgs = yumBase.buildTransaction()
    if rc != 2:
        return False

    try:
        yumBase.processTransaction()
    except:
        return False

    # re-enable the repos
    for repo in enabledRepos:
        repo.enable()

    return True
# main()

main(sys.argv[1], sys.argv[2])
