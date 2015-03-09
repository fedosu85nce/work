#!/usr/bin/env sh


# settings
ME=$(basename $0)
WORKDIR=$(pwd)/scripts/announcements
TEMPLATES=


# display usage message
usage() {
    echo "Usage: $ME <options>

Options:
    --help            Show help
    --email           Generate email for announcement
    --email-updates   Generate email for updates announcement
    --wiki            Generate wiki code for Releases/<date>"
}


# read argv
while [ $# != 0 ]; do
    case "$1" in
        "--email")
            EMAIL=yes
            SHOW_CHANGES=yes
            SHOW_KNOWN_ISSUES=yes
            SHOW_FIXED_BUGS=yes
            SHOW_OPENED_BUGS=yes
            TEMPLATES="$TEMPLATES announcement-email.txt"
            shift
            ;;
        "--email-updates")
            EMAIL_UPDATES=yes
            TEMPLATES="$TEMPLATES announcement-email-updates.txt"
            shift
            ;;
        "--wiki")
            WIKI=yes
            TEMPLATES="$TEMPLATES wiki-releases.txt"
            shift
            ;;
        "--help")
            usage
            exit 0
            ;;
        *)
            echo "ERROR: No template specified"
            usage
            exit 255
            ;;
    esac
done


# setup vars
. $WORKDIR/config/vars


# create sed args with the list of vars to be replaced in the template
SEDARGS=
for VAR in $VARS; do
    SEDARGS="$SEDARGS $(eval echo \"-e \"s,@$VAR@,\$$VAR,g\"\")"
done


# replace vars and display content
for TEMPLATE in $TEMPLATES; do
    sed -r $SEDARGS $WORKDIR/templates/$TEMPLATE
done


# changes
if [ "$SHOW_CHANGES" = "yes" ]; then
    echo -e "\nChanges:\n"
    cat $WORKDIR/templates/changes.txt
fi


# known issues
if [ "$SHOW_KNOWN_ISSUES" = "yes" ]; then
    if [ "$WIKI" = "yes" ]; then
        echo -e "\n= Known issues =\n"
    else
        echo -e "\nKnown issues:\n"
    fi
    cat $WORKDIR/templates/known-issues.txt
fi


# fixed bugs
if [ "$SHOW_FIXED_BUGS" = "yes" ]; then
    echo -e "\nBugs fixed:\n"
    cat $WORKDIR/templates/bugs-fixed.txt
fi


# opened bugs
if [ "$SHOW_OPENED_BUGS" = "yes" ]; then
    echo -e "\nBugs opened:\n"
    cat $WORKDIR/templates/bugs-opened.txt
fi

#contact info
echo -e "\nFor any questions, please post a message to powerkvm@lists.linux.ibm.com\n"


exit
