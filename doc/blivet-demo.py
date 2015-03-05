import blivet

b=blivet.Blivet()
b.reset()

#initialize disk
dasdb=b.devicetree.getDeviceByName("dasdb")
b.recursiveRemove(dasdb)
b.initializeDisk(dasdb)

#create new PV
part=b.newPartition(size=8000,parents=[dasdb])
b.createDevice(part)
fmt=blivet.formats.getFormat("lvmpv",lable="pv1")
b.formatDevice(part,fmt)
blivet.partitioning.doPartitioning(b)
b.doIt()

# create new VG
a=b.pvs
request=b.newVG(parents=a)
b.createDevice(request)
b.doIt()
#request=b.newVG(parents=a[2:])

#create new LV
a=b.vgs
request=b.newLV(size=2500,name="lv1",parents=a)
b.createDevice(request)
fmt=blivet.formats.getFormat("ext4",lable="test1",mountpoint="/home/test1")
b.formatDevice(request,fmt)
blivet.partitioning.doPartitioning(b)
b.doIt()
#request=b.newLV(size=2500,name="Lv2",parents=a[1:])

fmt.mount()

#discover scsi devices
#[anaconda root@ltczhp11 ~]# udevadm info -a -p /sys/class/scsi_generic/sg0
a=b.zfcp
a.addFCP("0.0.5080","0x500507630300c52a","0x4013401300000000")
b.devicetree.populate()
