# indigo-influx-receiver

Script to receive device changes from the json broadcaster Indigo plugin and send them to influxdb

Exercise for the reader: use pip to install influxdb over python 2.7ish, then launch.

Args:
* -m multicast port, read this from the Indigo JSON Broadcaster plugin configuration. Default 8087
* -s influxdb server host IP address, default 127.0.0.1
* -p influxdb port, default 8085
* -U influxdb user, default indigo
* -P influxdb password, default indigo
* -d influxdb database, default indigo

# Optional Suggestions

* Use homebrew and virtualenv to isolate this environment so we don't conflict with anything else.
* Use the included launchd example plist to handle running and stopping the script. Edit for correct absolute paths before starting, unless your name is dbrown too.

