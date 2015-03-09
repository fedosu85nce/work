#
# IMPORTS
#
from snack import *
from math import floor
from model.config import STR_VERSION
from viewer.__data__ import SELECT_DEVICE_TO_INSTALL
from viewer.__data__ import OK
from viewer.__data__ import BACK
from viewer.__data__ import IBM_ZKVM
from viewer.__data__ import ERROR_DISK_SIZE
from viewer.__data__ import ERROR_DISK_SIZE_MSG
from viewer.__data__ import ERROR_NO_DISK_SELECTED
from viewer.__data__ import ERROR_NO_DISK_SELECTED_MSG
from viewer.__data__ import HELP_LINE
from viewer.__data__ import SELECT_HELP_LINE
from viewer.__data__ import SELECT_TITLE
from viewer.__data__ import SELECT_ID
from viewer.__data__ import SELECT_MULTIPATH
from viewer.__data__ import SELECT_SIZE
from viewer.__data__ import SELECT_NAME
from viewer.__data__ import SELECT_FILESYSTEM
from viewer.__data__ import SELECT_VGRAID
from viewer.__data__ import SELECT_ADD_ZFCP

#
# CONSTANTS
#

#
# CODE
#
class SelectHardDisk:
    """
    Show all hard disks found in the system
    """

    def __init__(self, screen):
        """
        Constructor

        @type  screen: SnackScreen
        @param screen: SnackScreen instance
        """
        self.__screen = screen
        self.__screen.pushHelpLine(SELECT_HELP_LINE.localize())
        self.__msg = TextboxReflowed(40, SELECT_DEVICE_TO_INSTALL.localize())
        self.__list = CheckboxTree(5, scroll=1)
        self.__buttonsBar = ButtonBar(self.__screen, [(SELECT_ADD_ZFCP.localize(), "addzFCP"), (OK.localize(), "ok"),
            (BACK.localize(), "back")])

        self.__grid = GridForm(self.__screen, IBM_ZKVM.localize() % STR_VERSION, 1, 3)
        self.__grid.add(self.__msg, 0, 0)
        self.__grid.add(self.__list, 0, 1, (0, 1, 0, 1))
        self.__grid.add(self.__buttonsBar, 0, 2)
        self.__grid.addHotKey('F3')
    # __init__()

    def setDisks(self, partitioner, lunset):
        """
        Sets a list with all disks found in this system

        @type  storage: Partitioner
        @param storage: Partitioner instance

        @type  lunset: Set
        @param lunset: LUN set that user have specified

        @rtype:   nothing
        @returns: nothing
        """
        self.__disks = partitioner.disks
        self.__lunset = lunset
    # setDisks()

    def run(self):
        """
        Draws the screen

        @rtype: integer
        @returns: sucess status
        """
        # add all disks found into the viewer

        for disk in self.__disks:
            # don't display the zfcp device such as /dev/sda
            if disk.type == 'zfcp':
                continue
            # We need to loop through the multipath device to find the matching one
            if disk.type == 'dm-multipath':
                found = False
                if self.__lunset:
                    for dev in disk.parents:
                        if dev.fcp_lun in self.__lunset:
                            found = True
                if found == False:
                    continue
            self.__list.append(disk.name +' - ' + disk.path + ' - ' +
                    str(int(disk.size)/1024) + 'G', disk)

        # main loop to handle hotkey for disk detailed information
        rc = ''
        while rc not in ['addzFCP', 'back', 'ok']:
            result = self.__grid.run()
            rc = self.__buttonsBar.buttonPressed(result)

            # handle hotkey to display detailed disk information to
            # the user
            if result == 'F3':
                diskDetails = None
                current = self.__list.getCurrent()

                for disk in self.__diskData:
                    name = disk['name'] if not disk['mpath_master'] \
                           else disk['mpath_master']

                    if name == current:
                        diskDetails = disk
                        break

                self.__showDiskInformation(diskDetails, str(desc[2]) + 'G', current)
                continue

        self.__screen.pushHelpLine(HELP_LINE.localize())
        self.__screen.popWindow()
        if rc == "back":
            return None

        if rc == "addzFCP":
            return "addzFCP"

        #If the list is empty or no disk selected, show an error message
        if self.__list.item2key == {} or self.__list.getSelection() == []:
            self.showErrorNoDisk()
            return []

        return self.__list.getSelection()
    # run()

    def __belongsToVG(self, partition, default):
        """
        Checks if partition belongs to a LVM and returns its VG name

        @type partition: str
        @param partition: partition name

        @type default: arbitrary
        @param default: value to return case no VG found

        @rtype: str
        @returns: VG name or default
        """
        # no lvm data: return default
        if not self.__lvmData or not 'vgs' in self.__lvmData:
            return default

        # return the VG name for the given partition
        for vg, details in self.__lvmData['vgs'].iteritems():
            for partitions in details['pvsToLvs']:
                if partition in partitions:
                    return vg

        # nothing found: return default
        return default
    # __belongsToVG()

    def __belongsToRaidArray(self, partition, default):
        """
        Checks if partition belongs to a Raid array and return MD name

        @type partition: str
        @param partition: partition name

        @type default: arbitrary
        @param default: value to return case no VG found

        @rtype: str
        @returns: MD name or default
        """
        # no raid information: return default
        if not self.__raidData:
            return default

        # return MD name for the give partition
        for md, details in self.__raidData.iteritems():
            for dev in details['devices']:
                if partition in dev:
                    return md

        # nothing foud: return default
        return default
    # __belongsToRaidArray()

    def __sizeFormater(self, num):
        """
        Formats numeric sizes

        @type num: int
        @param num: value

        @rtype: str
        @returns: formated size
        """
        for m in ['B', 'KiB', 'MiB', 'GiB']:
            if num < 1024.0:
                return '%3.0f %s' % (floor(num), m)

            num /= 1024.0

        return '%3.0f %s' % (floor(num), 'TiB')
    # __sizeFormater()

    def __formatPartitioningLayout(self, diskData, size):
        """
        Formats the data about partitioning layout to be displayed
        in the disk selection screen

        @rtype:   dict
        @returns: partitoning layout
        """
        # format multipath slaves to be displayed
        mpathSlaves = 'No' if not diskData['mpath_slaves'] \
                       else ', '.join(diskData['mpath_slaves'])
        # data format
        table = []
        table.append('{:15s} {:55s}'.format(SELECT_ID.localize(), diskData['id'].split('/')[-1]))
        table.append('{:15s} {:35s}'.format(SELECT_SIZE.localize() + ':', size))
        table.append('{:15s} {:55s}\n'.format(SELECT_MULTIPATH.localize(), mpathSlaves))
        table.append('{:15s} {:10s} {:15s} {:30s}'.format(SELECT_NAME.localize(), SELECT_SIZE.localize(), SELECT_FILESYSTEM.localize(), SELECT_VGRAID.localize()))
        for partition in diskData['parts']:

            extraInfo = ''
            number = str(partition['nr'])
            name = diskData['name'] if not diskData['mpath_master'] else diskData['mpath_master']
            partname = '%s%s' % (name, number)
            if number == '0':
                partname = '-'

            # retrieve lvm/raid for the given partition
            if partition['fs'] == 'raid':
                extraInfo = self.__belongsToRaidArray(partname, None)

            elif partition['fs'] == 'lvm':
                extraInfo = self.__belongsToVG(partname, None)

            size = self.__sizeFormater(partition['size'] * diskData['sectorSize'])

            table.append('{:15s} {:10s} {:15s} {:30s}'.format(
                partname,
                size,
                partition['fs'],
                extraInfo))

        return table
    # __formatPartitioningLayout()

    def __showDiskInformation(self, diskData, size, name):
        """
        Displays detailed information about the selected disk

        @type: str
        @param: disk selected

        @rtype: nothing
        @returns: nothing
        """
        layout = self.__formatPartitioningLayout(diskData, size)

        ButtonChoiceWindow(self.__screen, "%s - %s" % (SELECT_TITLE.localize(), name),
                           '\n'.join(layout),
                           buttons=[(OK.localize(), 'ok')],
                           width=70)
    # __showDiskInformation()

    def showErrorDiskSize(self):
        """
        Displays an error about the disk size

        @rtype: nothing
        @returns: nothing
        """
        ButtonChoiceWindow(self.__screen, ERROR_DISK_SIZE.localize(),
                           ERROR_DISK_SIZE_MSG.localize(),
                           buttons=[(OK.localize(), 'ok')],
                           width=50)
    # showErrorLength()
    def showErrorNoDisk(self):
        """
        Displays an error when no disk selected

        @rtype: nothing
        @returns: nothing
        """
        ButtonChoiceWindow(self.__screen, ERROR_NO_DISK_SELECTED.localize(),
                           ERROR_NO_DISK_SELECTED_MSG.localize(),
                           buttons=[(OK.localize(), 'ok')],
                           width=50)
    # showErrorLength()

# SelectHardDisk
