#!/bin/sh

ENVDIR=/var/lib/smt
ENVFILE=${ENVDIR}/subcore.save
DEFAULT_SUBCORE=1

restore() {

if [ ! -n ${SUBCORE} ]; then
    SUBCORE=${DEFAULT_SUBCORE}
fi
expr='^[0-9]+$'
if ! [[ ${SUBCORE} =~ $expr ]] ; then
    SUBCORE=${DEFAULT_SUBCORE}
fi

case $(uname -m) in
    ppc64)
        grep OPAL /proc/cpuinfo >/dev/null 2>&1 && opal=1

        if [ "$opal" ]; then
            /usr/sbin/ppc64_cpu --subcores-per-core=$SUBCORE >/dev/null 2>&1
            /usr/sbin/ppc64_cpu --smt=off >/dev/null 2>&1
        fi
        ;;
esac

}

save() {

case $(uname -m) in
    ppc64)
        grep OPAL /proc/cpuinfo >/dev/null 2>&1 && opal=1

        if [ "$opal" ]; then
            SAVED=$(/usr/sbin/ppc64_cpu --subcores-per-core |  cut -s -d: -f2 | tr -d "[:blank:]")
        fi
        ;;
esac

if [ ! -n ${SAVED} ]; then
    SAVED=${DEFAULT_SUBCORE}
fi
expr='^[0-9]+$'
if ! [[ ${SAVED} =~ $expr ]] ; then
    SAVED=${DEFAULT_SUBCORE}
fi

cat >  ${ENVFILE} << EOF
SUBCORE=${SAVED}
EOF

}

[ ! -d ${ENVDIR} ] && mkdir -p ${ENVDIR}
[ ! -f ${ENVFILE} ] && {
cat > ${ENVFILE} << EOF
SUBCORE=${DEFAULT_SUBCORE}
EOF
}

. ${ENVFILE}

if [ $# != 0 ]; then
    case $1 in
        start)
            restore
            ;;
        stop)
            save
            ;;
        *)
		     exit 1
		     ;;
    esac
fi

exit 0
