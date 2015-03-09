#! /bin/sh

if [ "$CREATE_NETBOOT_TARBALL" = "false" ]; then
    echo "Skipping creation of netboot tarball..."
    exit 0
fi

# create packaging directory
mkdir -p ${BUILD_DIR}/package/wwwroot
mkdir -p ${BUILD_DIR}/package/wwwroot/kvmonp_netboot
mkdir -p ${BUILD_DIR}/package/wwwroot/kvmonp_packages

# copy frobisher packages
cp -a ${DVD_DIR}/packages/* ${BUILD_DIR}/package/wwwroot/kvmonp_packages

# copy boot and squashfs images
cp ${DVD_DIR}/ppc/ppc64/{initrd.img,vmlinuz} ${BUILD_DIR}/package/wwwroot/kvmonp_netboot
cp ${DVD_DIR}/LiveOS/squashfs.img ${BUILD_DIR}/package/wwwroot/kvmonp_netboot
cp ${OVERLAY_DIR}/package/petitboot.conf ${BUILD_DIR}/package

# create the package
tar -zcvf ${KOP_RELEASE}/ibm-powerkvm-netboot-${ISO_VERSION}-${ISO_BUILD}-ppc64-${ISO_MILESTONE}-${TIMESTAMP}.tar.gz \
    -C ${BUILD_DIR}/package .
