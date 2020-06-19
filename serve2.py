import socket
import struct
import time
from concurrent.futures.thread import ThreadPoolExecutor
from typing import List

import json

from indigo_protobuf_betterproto.indigo import IndigoUnknownMessage, TranslatorStub
from indigo_protobuf_betterproto.indigo_influx_outbound import make_unknown_message, InfluxOutbound

MCAST_GRP = '224.1.1.1'
# This part is the number you put in the json broadcaster UI
MCAST_PORT = 8087
SERVER_IP_BINDING = "0.0.0.0"
SERVER_PORT = "60000"


def get_messages_from_msg(strwhat) -> List[IndigoUnknownMessage]:
    messages = [make_unknown_message(evt) for evt in json.loads(strwhat.decode('utf-8'))]
    return messages


class InfluxReceiver(TranslatorStub):
    """Just take messages off local multicast, cast them, and forward them on."""

    def Subscribe(self, request, context):  # -> InfluxUnknownMessage
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        print(f'Starting listening socket on port {str(request.multicast_port)}')
        sock.bind(('', int(request.multicast_port)))
        mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        try:
            # Receive "string containing JSON (which is a list of object)" messages
            while context.is_active():
                data, addr = sock.recvfrom(10240)
                if data == b'stop':
                    print('Client wants me to stop.')
                    return
                else:
                    messages = get_messages_from_msg(data)
                    for msg in messages:
                        print(msg)
                        yield msg

        finally:
            # Close socket
            sock.close()
            print('Server stopped.')

# server.py
import grpc
from indigo_protobuf import indigo_pb2_grpc


def serve():
    server = grpc.server(ThreadPoolExecutor(max_workers=1))
    indigo_pb2_grpc.add_TranslatorServicer_to_server(InfluxReceiver(), server)

    server_address = f'{SERVER_IP_BINDING}:{SERVER_PORT}'
    print(f"My server address {server_address}")
    server.add_insecure_port(server_address)
    server.start()
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        server.stop(0)


# cli.py
import click
# from server import serve


@click.command()
# @click.option("--print", "print_set", is_flag=True, help="Just print, don't send.")
def main():
    serve()


if __name__ == "__main__":
    main()
