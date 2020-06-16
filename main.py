from datetime import datetime
import socket
import struct
import click
import json
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS, WriteApi
from indigo import InfluxEvent

from influx_connection_state import Influx20ConnectionState

MCAST_GRP = '224.1.1.1'
# This part is the number you put in the json broadcaster UI
MCAST_PORT = 8087


class InfluxReceiver:
    def __init__(self, token: str, org: str, bucket: str, host: str, print_set: bool = False, multicastport: int = MCAST_PORT):
        # Influx connection half
        client = InfluxDBClient(url=host, token=token)
        write_api: WriteApi = client.write_api(write_options=SYNCHRONOUS)
        self.state = Influx20ConnectionState(api=write_api, token=token, org=org, bucket=bucket, host=host)
        self.mcastport = multicastport
        self.sock = None
        self.connection = None
        self.pretend = print_set

    def connect(self):
        print(u'Starting listening socket on port' + str(self.mcastport))
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.sock.bind(('', int(self.mcastport)))
        mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    def send(self, strwhat):
        oldjson = json.loads(strwhat.decode('utf-8'))[0]
        for key in oldjson["fields"].keys():
            key: str
            newkey = key.replace(".", "_")
            if key != newkey:
                oldjson["fields"][newkey] = oldjson["fields"][key]
                del oldjson["fields"][key]
        if "time" not in oldjson:
            oldjson["time"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        ie = InfluxEvent().from_dict(oldjson)
        if ie.fields.on and not ie.fields.brightness:
            ie.fields.brightness = 100.0
        if ie.fields.on is not None and ie.fields.on is False and not ie.fields.brightness:
            ie.fields.brightness = 0.0
        newjson = ie.to_dict()
        print(ie.to_json())
        if len(newjson["fields"].keys()) < 1:
            return

        if not self.pretend:
            self.state.api.write(self.state.bucket, self.state.org, [newjson], time_precision="s")

    def run(self):
        try:
            # Receive messages
            while True:
                data, addr = self.sock.recvfrom(10240)
                self.send(data)
                if data == b'stop':
                    print('Client wants me to stop.')
                    break
                else:
                    # print("From addr: '%s', msg: '%s'" % (addr[0], data))
                    pass
        finally:
            # Close socket
            self.sock.close()
            print('Server stopped.')


@click.command()
@click.option("--token", type=str, envvar="INFLUX_TOKEN", required=True)
@click.option("--org", type=str, envvar="INFLUX_ORG", required=True)
@click.option("--bucket", type=str, envvar="INFLUX_BUCKET", required=True)
@click.option("--host", type=str, envvar="INFLUX_HOST", required=True)
@click.option("--print", "print_set", is_flag=True, help="Just print, don't send.")
@click.option("--multicastport", "-m", type=int, default=8087, show_default=True, envvar="MCPORT", help="The multicast port.")
def main(**kwargs):
    ir = InfluxReceiver(**kwargs)

    ir.connect()
    ir.run()


if __name__ == "__main__":
    main()
