#!/bin/sh
set -e

RPMS="zkvm-installer"
ver="1.1.0"
rele="beta4.1"

# setup env
for pkg in $RPMS; do
    for dir in BUILD BUILDROOT RPMS SOURCES SRPMS; do
        dirpath="${WORKSPACE}/rpms/${pkg}/${dir}"
        if [ ! -d "${dirpath}" ]; then
            mkdir -vp "$dirpath"
        fi
    done
done

# polish code for zkvm-install rpm
tempdir=$(mktemp -d)
rootdir=${tempdir}/zkvm-installer
mkdir -p ${rootdir}/usr/bin
mkdir -p ${rootdir}/lib/systemd/system
mkdir -p ${rootdir}/usr/share/anaconda
mkdir -p ${rootdir}/opt/ibm/zkvm-installer
mkdir -p ${rootdir}/usr/sbin
cp -rv ./licenses ${rootdir}/opt/ibm/zkvm-installer/
cp -rv ./src/scripts/bin/* ${rootdir}/usr/bin
cp -rv ${OVERLAY_DIR}/zkvm-installer/* ${rootdir}
cp -rv ./src/* ${rootdir}/opt/ibm/zkvm-installer
cp -rv ./systemd/zkvm ${rootdir}/usr/sbin/
cp -rv ./systemd/*.service ${rootdir}/lib/systemd/system/
cp -rv ./systemd/*.target ${rootdir}/lib/systemd/system/
find ${rootdir}/opt/ibm/zkvm-installer -name yaboot.conf \
     -exec sed -i s@KOPLABEL@${KOP_LABEL}@ {} \;
tar cvzf ${WORKSPACE}/rpms/zkvm-installer/SOURCES/zkvm.tar.gz \
    -C ${tempdir} zkvm-installer
rm -rf ${tempdir}

# generate zkvm-installer
rpmbuild -ba \
         --target "${RPM_TARGET}" \
         --define "dist ${RPM_PKVM_DIST}" \
         --define "_builddir ${WORKSPACE}/rpms/zkvm-installer/BUILD" \
         --define "_buildrootdir ${WORKSPACE}/rpms/zkvm-installer/BUILDROOT" \
         --define "_rpmdir ${WORKSPACE}/rpms/zkvm-installer/RPMS" \
         --define "_sourcedir ${WORKSPACE}/rpms/zkvm-installer/SOURCES" \
         --define "_srcrpmdir ${WORKSPACE}/rpms/zkvm-installer/SRPMS" \
         --define "version ${ver}" \
         --define "release ${rele}" \
         --define "label IBM_zKVM" \
         rpms/zkvm-installer/SPECS/zkvm-installer.spec

# rpms dir
RPMS_DIR="RPMs"
rm -rfv "$RPMS_DIR"
mkdir -pv "$RPMS_DIR"


# archive built rpms in the right place
cp -v ${WORKSPACE}/rpms/zkvm-installer/RPMS/noarch/*.rpm $RPMS_DIR

echo "Success!"
exit 0
