#
# IMPORTS
#
import os


#
# CONSTANTS
#
DEFAULT_DIR = '/opt/ibm/zkvm-installer/licenses/%s'
NON_IBM_LICENSE = 'non_ibm_license'
NOTICE = 'notices'
LICENSE = 'LA_%s'


#
# CODE
#

def getFileContent(filename, logger):
    """
    Returns the content of a text file

    @type  filename: basestr
    @param filename: file name

    @type  logger: Logging
    @param logger: logger object

    @rtype: basestr
    @returns: file content
    """
    text = ''
    try:
        file = open(DEFAULT_DIR % filename, 'r')
        text = file.read()
        file.close()

    except IOError:
        logger.debug('%s was not found' % filename)

    except:
        logger.critical('%s could not be read' % filename)

    finally:
        return text
# getFileContent()

def getIBMLicense(language, logger):
    """
    Returns the license text in the language selected. If the language
    does not exist it will be returned in english. Or an empty str if no
    license is find at all

    @type  language: basestr
    @param language: file name

    @type  logger: Logging
    @param logger: logger object

    @rtype: basestr
    @returns: file content
    """
    # hack to adjust a capitalized code
    if language == 'Ja_JP':
        language = 'ja'

    # try to get the license in the language passed
    license = getFileContent(LICENSE % language, logger)

    # if not found and the lang is in xx_XX format, try to
    # get the license in xx format
    if license == '' and len(language) > 2:
        license = getFileContent(LICENSE % language[:2], logger)

    # if not found anyway, get in english by default
    if license == '':
        license = getFileContent(LICENSE % 'en', logger)

    return license
# getIBMLicense()

def getNonIBMLicenseNotices(logger):
    """
    Returns the non IBM license text and notices appended. An empty string
    will be returned if no license is find

    @type  language: basestr
    @param language: file name

    @type  logger: Logging
    @param logger: logger object

    @rtype: basestr
    @returns: file content
    """
    license = [getFileContent(NON_IBM_LICENSE, logger),
               getFileContent(NOTICE, logger)]

    return '\n\n'.join(license)
# getNoticeNonIBMLicense()
