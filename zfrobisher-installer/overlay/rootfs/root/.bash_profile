# tmux settings
TMUX="/bin/tmux"
START="-u -f /etc/tmux-pkvm.conf start"
ATTACH="-u attach -t pkvm"
FBTERM="/usr/bin/fbterm -s 14 --"

# correct locale for languages
/usr/bin/localedef -i en_US -f UTF-8 en_US.UTF-8 && export LC_ALL=en_US.UTF-8 && export LANG=en_US.UTF-8

# Obtain current terminal
CURR_TTY=$(tty)


# On /dev/hvc0, start the installer under tmux and attach a tmux
# session to it.
if expr match "${CURR_TTY}" ".*hvc0.*" >/dev/null 2>&1; then
    $TMUX $START
    sleep 5
    $TMUX $ATTACH
fi


# List of terminals to display the installer
for tty in hvc1 tty1; do
    if expr match "${CURR_TTY}" ".*${tty}.*" >/dev/null 2>&1; then
        sleep 10
        $FBTERM $TMUX $ATTACH
    fi
done


# For remaining terminals, e.g. /dev/ttyN and /dev/pts/N, just let it
# open a root shell...
