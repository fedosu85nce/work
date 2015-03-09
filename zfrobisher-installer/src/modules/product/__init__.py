#!/usr/bin/python

#
# IMPORTS
#
from ConfigParser import ConfigParser
import os
import re


def getProductVersion():
    """
    Try to get the version number of this product

    @rtype: basicStr
    @return: the basic string contains the version number
    if the number is None, return a string contains
    'Unknown Version'
    """
    product_version = 'Unknown Version'
    config = ConfigParser()
    config.read('/.buildstamp')
    try:
        product_version = config.get('Main', 'Version')
    except:
        pass
    return product_version
# getProductVersion


def getProductName():
    """
    Try to get the name of this product

    @rtype: basicStr
    @return: a string contains the name of the product.
             if the name of the product cannot been obtain
             return a contains 'Unknown Product'
    """
    product_name = 'Unknown Product'
    config = ConfigParser()
    config.read('/.buildstamp')
    try:
        product_name = config.get('Main', 'Product')
    except:
        pass
    return product_name
# getProductName


def refreshProductInfo(rootDir):
    """
    Write new product release information into disk files

    @rtype: Nothing
    @return: Nothing
    """
    version = getProductVersion()
    exp_env = "export version=%s && echo " % version
    base_release = 'IBM Hypervisor release ${version} \(Z\)'
    os_release_1st_line = 'NAME=\\"IBM Hypervisor\\"'
    os_release = \
        ['VERSION=\\"${version} \(Z\)\\"',
         'ID=\\"ibm_hypervisor\\"',
         'ID_LIKE=\\"rhel fedora\\"',
         'VERSION_ID=\\"${version}\\"',
         'PRETTY_NAME=\\"IBM Hypervisor ${version} \(Z\)\\"',
         'ANSI_COLOR=\\""1;34"\\"',
         'BUILD_ID=\\"${version}\\"',
         'CPE_NAME=\\"cpe:/o:ibm:ibm_hypervisor:${version%%-*}\\"']
    sys_release_cpe = \
        '\"cpe:/o:ibm:ibm_hypervisor:${version%%-*}\" |tr [A-Z] [a-z]'
    issue_1st_line = 'IBM Hypervisor release ${version} \(Z\)'
    issue = ['kernel \\\\r on an \\\\m']

    if isinstance(rootDir, basestring):
        os.system('%s %s > %s/etc/base-release' % (exp_env,
                                                   base_release,
                                                   rootDir))
        os.system('%s %s > %s/etc/os-release' % (exp_env,
                                                 os_release_1st_line,
                                                 rootDir))
        for ln in os_release:
            os.system('%s %s >> %s/etc/os-release' % (exp_env,
                                                      ln,
                                                      rootDir))
        os.system('%s %s > %s/etc/system-release-cpe' % (exp_env,
                                                         sys_release_cpe,
                                                         rootDir))
        os.system('%s %s > %s/etc/issue' % (exp_env,
                                            issue_1st_line,
                                            rootDir))
        for ln in issue:
            os.system('%s %s >> %s/etc/issue' % (exp_env,
                                                 ln,
                                                 rootDir))
        os.system('cp %s/etc/issue %s/etc/issue.net' % (rootDir,
                                                        rootDir))
# refreshProductInfo


def __get_release_version_from_os_release(rootDir):
    try:
        with open(rootDir + '/etc/os-release') as releasefile:
            lines = releasefile.readlines()
            version_def = re.compile(r'^VERSION\s*=\s*.+$')
            for line in lines:
                if version_def.match(line):
                    line = line.split('=')[1].strip('\n')
                    line = line.strip('"').split(' ')[0]
                    return line
    except Exception:
        return None
# __get_release_version_from_os_release


def __get_release_version_from_base_release(rootDir):
    try:
        with open(rootDir + '/etc/base-release') as releasefile:
            line = releasefile.readline()
            line = line.split(' ')[3]
            return line
    except Exception:
        return None
# __get_release_version_from_base_release


def __get_release_version_from_issue(rootDir):
    try:
        with open(rootDir + '/etc/issue') as releasefile:
            lines = releasefile.readlines()
            for line in lines:
                if line.startswith('IBM Hypervisor release'):
                    line = line.split(' ')[3]
                    return line
    except Exception:
        return None
# __get_release_version_from_issue


def getReleaseVersion(rootDir):
    """
    Find the version numver of the old installed system

    @rtype: basestring
    @returns: a string contains the version number of the
    installed system, None if error occurred
    """
    ret = __get_release_version_from_os_release(rootDir)
    if ret is None:
        ret = __get_release_version_from_base_release(rootDir)
    if ret is None:
        ret = __get_release_version_from_issue(rootDir)
    return ret
# getReleaseVersion 
