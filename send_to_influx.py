import argparse
import socket
import struct
import sys
import json
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError

MCAST_GRP = '224.1.1.1'
MCAST_PORT = 8087
# todo configurable port

class InfluxReceiver:
    def __init__(self):
        # todo config block
        self.host = '127.0.0.1'
        self.port = '8085'
        self.user = 'indigo'
        self.password = 'indigo'
        self.database = 'indigo'
        self.mcastport = str(MCAST_PORT)

        self.connection = None

    def connect(self):
        print(u'Starting socket')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.sock.bind(('', int(self.mcastport)))
        mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        print(u'Starting influx connection')

        self.connection = InfluxDBClient(
            host=self.host,
            port=int(self.port),
            username=self.user,
            password=self.password,
            database=self.database)

        # todo reset config - CLI flag? config dict? ALIENS?!
        #if self.pluginPrefs.get('reset', False):
        #    try:
        #        print(u'dropping old')
        #        self.connection.drop_database(self.database)
        #    except:
        #        pass

        print(u'Connecting...')
        self.connection.create_database(self.database)
        self.connection.switch_database(self.database)
        self.connection.create_retention_policy('two_year_policy', '730d', '1')
        print(u'Influx connection succeeded')

    def send(self, strwhat, measurement='device_changes'):
        what = json.loads(strwhat)[0]

        json_body=[
            {
                'measurement': what['measurement'],
                'tags' : what['tags'],
                'fields':  what['fields']
            }
        ]

        print(json.dumps(json_body).encode('utf-8'))

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
                    pass
                    #print('One of the columns just will not convert to its previous type. This means the database columns are just plain wrong.')
            except ValueError:
                print(u'Unable to force a field to the type in Influx - a partial record was still written')
            except Exception as e:
                print("Error while trying to write:")
                print(unicode(e))
        if retrylimit == 0 and unsent:
            print(u'Unable to force all fields to the types in Influx - a partial record was still written')

    def run(self):
        try:
            # Receive messages
            while True:
                data, addr = self.sock.recvfrom(10240)
                self.send(data)
                #if data == b'stop':
                #    print('Client wants me to stop.')
                #    break
                #else:
                #    print("From addr: '%s', msg: '%s'" % (addr[0], data))
        finally:
            # Close socket
            self.sock.close()
            print('Server stopped.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--multicastport', help='muticast port', default='8087')
    parser.add_argument('-s', '--server', help='influxdb host', default='127.0.0.1')
    parser.add_argument('-p', '--port', help='influxdb port', default='8085')
    parser.add_argument('-U', '--user', help='influxdb user', default='indigo')
    parser.add_argument('-P', '--password', help='influxdb password', default='indigo')
    parser.add_argument('-d', '--database', help='influxdb database', default='indigo')
    args, unknown = parser.parse_known_args()

    ir = InfluxReceiver()
    ir.host = args.server
    ir.port = int(args.port)
    ir.user = args.user
    ir.password = args.password
    ir.database = args.database
    ir.mcastport = args.multicastport

    ir.connect()
    ir.run()
