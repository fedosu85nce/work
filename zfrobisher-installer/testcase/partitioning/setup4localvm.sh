#!/bin/bash
#-p path
mkdir -p /opt/ibm/zkvm-installer
cp -a ../../src/po/ /opt/ibm/zkvm-installer
cd /opt/ibm/zkvm-installer/po/en_US/LC_MESSAGES/
msgfmt zKVM.po
mv messages.mo zKVM.mo
