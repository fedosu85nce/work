#!/bin/sh


LFTP_CMDS="$*"
TEMP_SCRIPT=$(mktemp)


echo "lftprc: $LFTPRC"
echo "lftp commands: $LFTP_CMDS"


sed -e "s,@LFTP_CMDS@,$LFTP_CMDS\n,g" $LFTPRC > $TEMP_SCRIPT
lftp -f $TEMP_SCRIPT
rm -rf $TEMP_SCRIPT

exit 0
