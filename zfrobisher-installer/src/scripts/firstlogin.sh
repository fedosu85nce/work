#!/bin/bash

#----------------------------------------------------------------------
#Creates a persistent isolated virtual network (virbr1)
#----------------------------------------------------------------------
ls /etc/libvirt/qemu/networks/kop.xml >/dev/null 2>&1 || virtnet=1

if [ "$virtnet" ]; then
    virsh net-define /opt/ibm/zkvm-installer/modules/network/kop.xml >/dev/null 2>&1 && \
    virsh net-autostart kop >/dev/null 2>&1 && \
    virsh net-start kop >/dev/null 2>&1 && \
    echo "allow virbr1" >> /etc/qemu/bridge.conf
    #echo "allow virbr1" | tee -a /etc/qemu/bridge.conf
fi

#----------------------------------------------------------------------
# Delete script call on firstlogin
#----------------------------------------------------------------------
[ -e ${HOME}/.bash_profile ] && sed -i '/\/opt\/ibm\/zkvm-installer\/scripts\/firstlogin.sh/d' ${HOME}/.bash_profile
