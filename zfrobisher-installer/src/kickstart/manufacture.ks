%pre
#!/usr/bin/env sh

set -e
#set -x

#----------------------------------------------------------------------
# Functions
#----------------------------------------------------------------------
mpathDisable() {
    echo "Disabling multipath..."
    systemctl stop multipathd.service
    multipath -F
    _multipath='disable'
    echo "...DONE"
}

#----------------------------------------------------------------------
# Select devices to be usned in IPR-RAID 10
#----------------------------------------------------------------------
# get first adapter
echo "Getting first adapter:"
_adapter=$(iprconfig -c show-ioas | awk '$NF ~ /Operational/ {print $1; exit}')
echo ${_adapter}

# get first 2 devices from the first adapter
echo "Getting first 2 devices:"
_devices=$(iprconfig -c query-raid-create ${_adapter} | awk '$NF ~ /Active/ {c++; if (c==1 || c==2){print $1}}')
echo ${_devices}

#----------------------------------------------------------------------
# Cleanup devices before create IPR-RAID 10
#----------------------------------------------------------------------
# check mulitpath
echo "Checking multipath..."
if multipath -l >/dev/null 2>&1; then
    echo "...multipath USED"
    _multipath='enable'
    for i in ${_devices}; do
        if [ "${i:0:2}" = 'sg' ]; then
            echo "Invalid device format: ${_devices}"
            exit 1
        fi
        _mpath=$(multipath -l | awk -v dev="$i" '$1 ~ /mpath/ {mpath_temp=$1; getline; getline; getline ;if ( $4 ~ dev ){print mpath_temp; exit} else{getline; getline; if ( $3 ~ dev ){print mpath_temp;exit}}}')
        _devs="${_devs} ${_mpath}"
    done
else
    echo "...multipath NOT USED"
    mpathDisable
    _devs="${_devices}"
fi

echo "Devices consider for cleanup:"
echo "${_devs}"

# get physical volumes and volume groups
for i in ${_devs}; do
    _pvTemp=$(pvs | awk -v dev="$i" '$1 ~ dev {print $1}')
    _pv="${_pv} ${_pvTemp}"
    _vgTemp=$(pvs | awk -v dev="$i" '$1 ~ dev {print $2}')
    _vg="${_vg} ${_vgTemp}"
done
echo "Getting physical volumes:"
echo "${_pv}"
echo "Getting volume groups:"
echo "${_vg}"

# get logical volumes
echo "Getting logical volumes:"
for i in $_vg; do
    _lvTemp=$(lvs | awk -v dev=$i '$2 ~ dev {print $1}')
    _lv="${_lv} ${_lvTemp}"
done
echo "${_lv}"

# delete LVM
echo "Deleting LVM..."
echo "Deleting logical volumes from volume groups: ${_vg}"
for i in ${_vg}; do
    lvremove --force $i
done
echo "Deleting volume groups: ${_vg}"
for i in ${_vg}; do
    vgremove --force $i
done
echo "Deleting physical volumes: ${_pv}"
for i in ${_pv}; do
    pvremove --force --yes $i
done
echo "...DONE"

sleep 5
echo "Stopping all LVM volume groups"
vgchange -an
echo "...DONE"

#----------------------------------------------------------------------
# Create IPR-RAID 10
#----------------------------------------------------------------------
# Disable multipath
[ "${_multipath}" = 'enable' ] && mpathDisable

# format devices for raid
echo "Formatting devices for raid..."
iprconfig -c format-for-raid ${_devices}
echo
echo "...DONE"

# get first 2 devices from the first adapter
# (name may be change from sdX to sgX after format)
echo "Getting first 2 devices:"
_devices=$(iprconfig -c query-raid-create ${_adapter} | awk '$NF ~ /Active/ {c++; if (c==1 || c==2){print $1}}')
echo ${_devices}

# create raid 10
echo "Creating raid 10..."
iprconfig -c raid-create -z -r 10 ${_devices}
echo
echo "...DONE"

# get array
echo "Getting array:"
_array=$(iprconfig -c show-alt-config | awk '$4 ~ /IPR-10/ && $NF ~ /Optimized/ {print $1;exit}')
echo ${_array}

# get resource name
echo "Getting resource name:"
_dev=$(iprconfig -c show-details ${_array}  | awk '/^Resource Name/ {print $NF}')
echo ${_dev}

if [ "${_multipath}" = 'disable' ]; then
    # enable multipath
    echo "Enabling multipath..."
    systemctl start multipathd.service
    echo "...DONE"
fi

echo "Activating all existing LVM volume groups"
vgchange -ay
echo "...DONE"

# get multipath raid
echo "Getting multipath raid:"
_mpath=$(multipath -l | awk -v dev="${_dev##*/}" '$5 ~ /,IPR-10/ {mpath_temp=$1; getline; getline; getline ;if ( $4 ~ dev ){print mpath_temp; exit} else{getline; getline; if ( $3 ~ dev ){print mpath_temp;exit}}}')
echo "${_mpath}"

# create symlink label
echo "Creating symlink label:"
_label="/dev/disk/by-label/IBMIPR10"
ln -sf "/dev/mapper/${_mpath}" ${_label}
ls -la ${_label}

exit 0
%end
partition / --ondisk=LABEL=IBMIPR10
%post
date  +"%Y%m%d-%H%M%S" > /opt/ibm/zkvm-installer/postFile.$(date +"%Y%m%d-%H%M%S")
echo "manufacture.ks" >> /opt/ibm/zkvm-installer/postFile.$(date +"%Y%m%d-%H%M%S")
%end
