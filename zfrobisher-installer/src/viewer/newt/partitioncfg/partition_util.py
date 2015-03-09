#
# IMPORTS
#
import re
import locale
import sys

from blivet.size import Size
#
# CONSTANTS
#
SIZE_UNITS_DEFAULT = "M"                 # Default units when the user do no input units
SIZE_MIN_GRANULARITY = Size(spec="1 M")  # The smallest granularity for storage size

MPS_IN_SYS = ["/dev", "/proc", "/run", "/sys"]
MP_FLAG_INUSE = 0
MP_FLAG_NONE = 1
MP_FLAG_INSYS = 2
MP_FLAG_ERR_FORMAT = 3
MP_FLAG_CORRECT = 10
#
# CODE
#


def strToSize(inputSize, lowerBound=SIZE_MIN_GRANULARITY, units=SIZE_UNITS_DEFAULT):
    '''format inputSize to Size from blivet.size

        :inputSize  - string
        :lowerBound
        :units
    '''
    if not inputSize:
        return None

    text = inputSize.decode("utf-8").strip()

    # A string ending with digit, dot or commoa without the unit information
    if re.search(r'[\d.%s]$' % locale.nl_langinfo(locale.RADIXCHAR), text):
        text += units

    try:
        size = Size(spec=text)
    except ValueError:
        return None

    # set as the smallest granularity
    if size is None:
        return None
    if lowerBound is not None and size < lowerBound:
        return lowerBound

    # print size
    return size


def validateMountpoint(mountpoint, existMps=[]):
    # ["/boot", "swap", '/'] is default mp in zfrobisher

    if mountpoint is None:
        return MP_FLAG_NONE
    if mountpoint in existMps:
        return MP_FLAG_INUSE
    if mountpoint in MPS_IN_SYS:
        return MP_FLAG_INSYS
    if ((len(mountpoint) > 1 and mountpoint.endswith("/")) or  # does not end with '/' unless mp is '/'
          (not mountpoint.startswith("/")) or                    # start with '/' except for swap
          (" " in mountpoint) or                                 # does not contain space
          (re.search(r'/\.*/', mountpoint)) or                   # does not contain pairs of '/' enclosing zero or more '.', //, ./../
          (re.search(r'/\.+$', mountpoint))):                    # does not end with '/' followed by one or more '.'
        return MP_FLAG_ERR_FORMAT

    return MP_FLAG_CORRECT