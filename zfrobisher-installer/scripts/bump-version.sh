#!/bin/bash

# =====================================================================
# bump_version.sh
#  - creates or updates version.info file 
#  - apply changes on SPEC files, Makefile.config and src/model/config.py
# ======================================================================


#=======================
# Initialize variables
#=======================

VERSION_INFO="version.info"

PKVM_STREAM="none"
SERVICE_PACK=0
BUILD_NUMBER=0
RESPIN=0 
MILESTONE="none"
VENDOR="IBM"

assumeyes=0

PKVM_RELEASE_SPEC="rpms/pkvm_release/SPECS/pkvm2_1-release.spec"
PKVM_INSTALLER_SPEC="rpms/powerkvm-installer/SPECS/powerkvm-installer.spec"
PKVM_CONFIG_SPEC="rpms/ibm-powerkvm-config/SPECS/ibm-powerkvm-config.spec"
PKVM_LAYER_SPEC="rpms/ibm-powerkvm-layer/SPECS/ibm-powerkvm.layer.spec"

MODEL_CONFIG="src/model/config.py"

MAKEFILE_CONFIG="Makefile.config"


# =======================
# do_updateModelConfig
# =======================

function do_updateModelConfig() {

OCTAL_NUMBER=$(echo "obase=8; ibase=10; $BUILD_NUMBER" | bc )

STR_VERSION="GA_VERSION = \""

echo "Patch: $MODEL_CONFIG"
sed -i "s,GA_VERSION = [\"][[:alnum:]]*.[[:alnum:]]*.[[:alnum:]]*.[[:alnum:]]*[\"]$,GA_VERSION = \"$PKVM_STREAM.$SERVICE_PACK\", " $MODEL_CONFIG
sed -i "s,BUILD_NUMBER = 0[[:alnum:]]*$,BUILD_NUMBER = 0$OCTAL_NUMBER, " $MODEL_CONFIG
sed -i "s,RESPIN = [\"][[:alnum:]]*[\"]$,RESPIN = \"$RESPIN\", " $MODEL_CONFIG

}

# =======================
# do_updateMakefileConfig
# =======================

function do_updateMakefileConfig() {

echo "Patch: $MAKEFILE_CONFIG"
sed -i "s,export KOP_STREAM := [[:alnum:]]*.[[:alnum:]]*.[[:alnum:]]*$,export KOP_STREAM := $PKVM_STREAM, " $MAKEFILE_CONFIG
sed -i "s,export KOP_VERSION_LABEL := [[:alnum:]]*.[[:alnum:]]*$,export KOP_VERSION_LABEL := $SERVICE_PACK.$BUILD_NUMBER, " $MAKEFILE_CONFIG
sed -i "s,export ISO_BUILD := [[:alnum:]]*.[[:alnum:]]*$,export ISO_BUILD := $BUILD_NUMBER.$RESPIN, " $MAKEFILE_CONFIG
sed -i "s,export ISO_VERSION := [[:alnum:]]*.[[:alnum:]]*.[[:alnum:]]*.[[:alnum:]]*$,export ISO_VERSION := $PKVM_STREAM.$SERVICE_PACK, " $MAKEFILE_CONFIG
sed -i "s,export ISO_MILESTONE := [[:alnum:]]*$,export ISO_MILESTONE := $MILESTONE, " $MAKEFILE_CONFIG
}

# ================
# do_updateSpec $1=specfile 
# ================

function do_updateSpec() {

echo "Patch: $1"
sed -i "s,%define pkvm_version [[:alnum:]]*.[[:alnum:]]*.[[:alnum:]]*.[[:alnum:]]*$,%define pkvm_version $PKVM_STREAM.$SERVICE_PACK, " $1
sed -i "s,%define pkvm_release [[:alnum:]]*$,%define pkvm_release $BUILD_NUMBER, " $1
sed -i "s,%define pkvm_respin .[[:alnum:]]*$,%define pkvm_respin .$RESPIN, " $1
}

# ====================
# do_updateReleaseSpec $1=specfile 
# ====================

function do_updateReleaseSpec() {

echo "Patch: $1"
sed -i "s,%define pkvm_stream [[:alnum:]]*.[[:alnum:]]*.[[:alnum:]]*$,%define pkvm_stream $PKVM_STREAM, " $1
sed -i "s,%define service_stream [[:alnum:]]*$,%define service_stream $SERVICE_PACK, " $1
sed -i "s,%define pkvm_release [[:alnum:]]*$,%define pkvm_release $BUILD_NUMBER, " $1
sed -i "s,%define respin .[[:alnum:]]*$,%define respin .$RESPIN, " $1
sed -i "s,%define milestone [[:alnum:]]*$,%define milestone $MILESTONE, " $1
}

# ====================
# do_updateVersionInfo
# ====================

function do_updateVersionInfo() {

echo "PKVM_STREAM=$PKVM_STREAM" > "$VERSION_INFO"
echo "SERVICE_PACK=$SERVICE_PACK" >> "$VERSION_INFO"
echo "BUILD_NUMBER=$BUILD_NUMBER" >> "$VERSION_INFO"
echo "RESPIN=$RESPIN" >> "$VERSION_INFO"
echo "MILESTONE=$MILESTONE" >> "$VERSION_INFO"
echo "VENDOR=$VENDOR" >> "$VERSION_INFO"
}

# ==============
# do_updateAll 
# ==============

function do_updateAll() {

do_updateVersionInfo
do_updateMakefileConfig
do_updateModelConfig
do_updateReleaseSpec $PKVM_RELEASE_SPEC
do_updateSpec $PKVM_INSTALLER_SPEC
do_updateSpec $PKVM_CONFIG_SPEC
do_updateSpec $PKVM_LAYER_SPEC
}

# ===================
# do_getConfirmation
# ===================

function do_getConfirmation() {

echo "Confirm your settings"
echo "PKVM_STREAM = $PKVM_STREAM"
echo "SERVICE_PACK = $SERVICE_PACK" 
echo "BUILD_NUMBER = $BUILD_NUMBER" 
echo "RESPIN = $RESPIN" 
echo "MILESTONE = $MILESTONE" 
echo "VENDOR = $VENDOR"   


while true
do
  read -p "Do you wish to continue? (Yes/No)" 
  case $REPLY in
    YES|yes|Yes) return 0; break ;;
    no|NO|No)    return 1; break ;;
    *)           echo "Please enter only yes or no - you entered $REPLY"
  esac
done
}

# ================
# do_getValue()
# ================

function do_getValue() {

#find key $1 in the file $2 and get/return associated value
curValue=$(grep -Po "(?<=^"$1=").*" "$2" )
echo "$curValue"
}


# ====================
# do_readVersionInfo()
# ====================

function do_readVersionInfo() {

if [ -f "$VERSION_INFO" ]; then
  PKVM_STREAM=$(do_getValue "PKVM_STREAM" $VERSION_INFO); 
  SERVICE_PACK=$(do_getValue "SERVICE_PACK" $VERSION_INFO); 
  BUILD_NUMBER=$(do_getValue "BUILD_NUMBER" $VERSION_INFO); ((BUILD_NUMBER++)); 
  RESPIN=$(do_getValue "RESPIN" $VERSION_INFO); ((RESPIN++)); 
  MILESTONE=$(do_getValue "MILESTONE" $VERSION_INFO); 
  VENDOR=$(do_getValue "VENDOR" $VERSION_INFO);   
fi

}

#================
# do_usage
#================

function do_usage(){

echo "Usage: scripts/bump-version.sh [options]"
echo ""
echo "--usage: to display usage info"
echo "--assumeyes: assume yes for any question" 
echo "--stream: zKVM stream. Default=value at version.info"
echo "--service: Service Pack number. Default=value at version.info"
echo "--build: Build number. Default=if missing, the value at version.info will be incremented"
echo "--respin: Indicates a PKVM or MCP fix on current build. Default=if missing, the value at version.info will be incremented"
echo "--milestone: Product milestone. Default=value at version.info"
echo "--vendor: Vendor name. Default=IBM"
}


#================
# do_getOptions
#================

# get and parse command line options

function do_getOptions(){

# check each parameter

for i in "$@"
do
  case $i in
    -s=*|--stream=*)
    PKVM_STREAM="${i#*=}"
    shift
    ;;
    -p=*|--service=*)
    SERVICE_PACK="${i#*=}"
    shift
    ;;
    -b=*|--build=*)
    BUILD_NUMBER="${i#*=}"
    shift
    ;;
    -r=*|--respin=*)
    RESPIN="${i#*=}"
    shift
    ;;
    -m=*|--milestone=*)
    MILESTONE="${i#*=}"
    shift
    ;;
    -v=*|--vendor=*)
    VENDOR="${i#*=}"
    shift
    ;;
    -y|--assumeyes)
    assumeyes=1
    shift
    ;;
    --usage)
    do_usage
    if [ $# == 2 ]; then exit  # exit if only usage option was provided
    fi
    shift
    ;;
    *)				# unknown option
           
    shift
    ;;
  esac
done
}


#=============================================
#                     MAIN
# ============================================

# the script is supposed to be invoked with a list of options 
# or use the version.info file 

if test -z "$1"; then
  echo "No command-line arguments." ; 
  if [ ! -f "$VERSION_INFO" ]; then
    echo "$VERSION_INFO file is not available."
    echo "You should provide definitions. Use --usage for help."  
    exit
  else
    do_readVersionInfo
  fi
else
  if [ -f "$VERSION_INFO" ]; then do_readVersionInfo
  fi
  do_getOptions $@ $#
fi

if [ $assumeyes -eq 1 ]; then
  do_updateAll
elif [ $assumeyes -eq 0 ] && do_getConfirmation ; then
  do_updateAll
fi

echo " ==>  The end <== " ; exit


#RUN FROM BASE folder 
#./scripts/bump-version_NEW.sh --stream=2.1.0 --service=2 --build=20 --respin=0 --milestone=Service --vendor=IBM

# EXAMPLE TO TEST
# remove version.info file; check increment for build and respin; check spec files
#./scripts/bump-version_NEW.sh
#./scripts/bump-version_NEW.sh --usage
#./scripts/bump-version_NEW.sh --stream=2.1.0  (only one is enough; if file exists all values will be listed)


