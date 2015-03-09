from snack import *
import sys
#sys.path - A list of string that specifies the search path for modules
#pwd - /usr/shared/00code/zfrobisher-installer/testcase/partitioning
#sys.path.insert(0, "/usr/shared/00code/zfrobisher-installer/src/")
#sys.path.insert(1, "/usr/shared/00code/zfrobisher-installer/src/viewer/newt/partitioncfg/")
sys.path.insert(0, "../../src/")                          #path for viewer.__data__
sys.path.insert(1, "../../src/viewer/newt/partitioncfg/") #path for find partition_interface module 

from partition_interface import *
try:
    screen = SnackScreen()
    partitioner = Partitioner()
    partitionInterface = PartitionInterface(screen, partitioner)
    '''Entry for partitioning

            :runOn VM   - means could not configure three default partition /boot, swap, /(root)
            			  use this option, we can test on local vm
                   LPAR - means run on LPAR
    '''
    # select disk by changing the slice of the disks, [)
    result = partitionInterface.run(partitioner.disks[2:3], 0, runOn = "VM")
finally:
    screen.finish()