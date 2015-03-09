#!/bin/bash
for i in src/po/*; do
    po_file=$i/LC_MESSAGES/zKVM.po
    [ -f $po_file ] && ./scripts/msgfmt.py $po_file

    # fix for japanese files
    if [ $i == "src/po/Ja_JP" ]; then
        ln -s "Ja_JP" "src/po/ja_JP"
    fi
done
