#!/bin/bash

# =====
# automatically switch to the directory where the script lives
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
pushd $DIR
# =====

if [ ! -e indigoenv ] ; then
    # we need pip
    which pip || sudo easy_install pip
    which virtualenv || sudo pip install virtualenv
    virtualenv -p /usr/bin/python indigoenv
    source indigoenv/bin/activate
    pip install influxdb
fi
[ -e indigoenv ] && source indigoenv/bin/activate

python send_to_influx.py

function undo_source_actions() {
    echo "Turning off virtualenv"
    deactivate
}

undo_source_actions

# =====
# return to the users calling dir
popd
# =====

