echo "Setting up this virtualenv"
# http://python-guide-pt-br.readthedocs.io/en/latest/dev/virtualenvs/

if [ ! -e indigoenv ] ; then 
    virtualenv -p /usr/bin/python indigoenv
    source indigoenv/bin/activate
    pip install influxdb py2app
fi
[ -e indigoenv ] && source indigoenv/bin/activate

export INHOST=nfs.smurfless.com 

function undo_source_actions() {
    echo "Turning off virtualenv"
    deactivate
}

function mkclean() {
rm -rf build dist
}

function mktest() {
mkclean
python setup.py py2app -A
}

function mkrelease() {
mkclean
python setup.py py2app
zip -r Indigo\ Influx\ Receiver.zip dist/Indigo\ Influx\ Receiver.app
}

function runtest() {
./dist/Indigo\ Influx\ Receiver.app/Contents/MacOS/Indigo\ Influx\ Receiver
}

