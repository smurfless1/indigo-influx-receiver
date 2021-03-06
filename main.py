import argparse
import socket
import struct
import click
import json
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError

MCAST_GRP = '224.1.1.1'
# This part is the number you put in the json broadcaster UI
MCAST_PORT = 8086

class InfluxReceiver:
    def __init__(self):
        # Influx connection half
        self.host = '127.0.0.1'
        self.port = '8086'
        self.user = 'indigo'
        self.password = 'indigo'
        self.database = 'indigo'
        self.mcastport = str(MCAST_PORT)
        self.sock = None
        self.connection = None

    def connect(self):
        print(u'Starting socket on port' + str(self.port))
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.sock.bind(('', int(self.mcastport)))
        mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        print(u'Starting influx connection')
        print(self.host)

        self.connection = InfluxDBClient(
            host=self.host,
            port=int(self.port),
            username=self.user,
            password=self.password,
            database=self.database)

        print(u'Connecting...')
        self.connection.create_database(self.database)
        self.connection.switch_database(self.database)
        self.connection.create_retention_policy('two_year_policy', '730d', '1')
        print(u'Influx connection succeeded')

    def send(self, strwhat, measurement='device_changes'):
        what = json.loads(strwhat)[0]

        json_body = [
            {
                'measurement': what['measurement'],
                'tags': what['tags'],
                'fields': what['fields']
            }
        ]

        # print(json.dumps(json_body).encode('utf-8'))

        # don't like my types? ok, fine, what DO you want?
        retrylimit = 30
        unsent = True
        while unsent and retrylimit > 0:
            retrylimit -= 1
            try:
                self.connection.write_points(json_body)
                unsent = False
            except InfluxDBClientError as e:
                #print(str(e))
                field = json.loads(e.content)['error'].split('"')[1]
                #measurement = json.loads(e.content)['error'].split('"')[3]
                retry = json.loads(e.content)['error'].split('"')[4].split()[7]
                if retry == 'integer':
                    retry = 'int'
                if retry == 'string':
                    retry = 'str'
                # float is already float
                # now we know to try to force this field to this type forever more
                try:
                    newcode = '%s("%s")' % (retry, str(json_body[0]['fields'][field]))
                    #print(newcode)
                    json_body[0]['fields'][field] = eval(newcode)
                except ValueError:
                    print('One of the columns just will not convert to its previous type. This means the database columns are just plain wrong.')
            except ValueError:
                print(u'Unable to force a field to the type in Influx - a partial record was still written')
            except Exception as e:
                print("Error while trying to write:")
                print(e)
        if retrylimit == 0 and unsent:
            print(u'Unable to force all fields to the types in Influx - a partial record was still written')

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
                    print("From addr: '%s', msg: '%s'" % (addr[0], data))
        finally:
            # Close socket
            self.sock.close()
            print('Server stopped.')


@click.command()
@click.option("--influxdb-host", type=str, default="localhost", show_default=True, env="INHOST", help="The influxdb host to connect to.")
@click.option("--influxdb-port", type=int, default=8086, show_default=True, env="INPORT", help="The influxdb port to connect to.")
@click.option("--influxdb-user", type=int, default="indigo", show_default=True, env="INUSER", help="The influxdb user to connect as.")
@click.option("--influxdb-pass", type=str, default="indigo", show_default=True, env="INPASS", help="The influxdb password.")
@click.option("--influxdb-database", type=str, default="indigo", show_default=True, env="INDB", help="The influxdb database.")
@click.option("--multicastport", "-m", type=int, default=8087, show_default=True, env="MCPORT", help="The multicast port.")
def main(influxdb_host, influxdb_port, influxdb_user, influxdb_pass, influxdb_database, multicastport):
    ir = InfluxReceiver()
    ir.host = influxdb_host
    ir.port = influxdb_port
    ir.user = influxdb_user
    ir.password = influxdb_pass
    ir.database = influxdb_database
    ir.mcastport = multicastport

    ir.connect()
    ir.run()


if __name__ == "__main__":
    main()
