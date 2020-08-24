import socket
import struct
import time
from concurrent.futures.thread import ThreadPoolExecutor
from typing import List

import json

from indigo_protobuf.indigo_influx_pb2 import InfluxEvent
from indigo_protobuf.indigo_influx_pb2_grpc import InfluxTranslatorServicer
from indigo_protobuf.indigo_pb2 import IndigoUnknownMessage
from indigo_protobuf.indigo_pb2_grpc import TranslatorServicer
from indigo_protobuf.indigo_influx_outbound import make_unknown_message, InfluxOutbound

MCAST_GRP = '224.1.1.1'
# This part is the number you put in the json broadcaster UI
MCAST_PORT = 8087
SERVER_IP_BINDING = "0.0.0.0"
SERVER_PORT = "60000"


def get_messages_from_msg(strwhat) -> List[IndigoUnknownMessage]:
    messages = [make_unknown_message(evt) for evt in json.loads(strwhat.decode('utf-8'))]
    return messages


def get_influx_events(source_list: List[IndigoUnknownMessage]) -> List[InfluxEvent]:
    return_list = []
    for elt in map(InfluxOutbound, source_list):
        print(f"{elt.message.tags.name.value}")
        if elt.sendable():
            print(elt)
            print("sendable")
            togo = elt.event
            print(togo)
            return_list.append(togo)
    print("returning")
    return return_list
    # return [elt.event for elt in map(InfluxOutbound, source_list) if elt.sendable()]


class IndigoReceiver(TranslatorServicer):
    """Just take messages off local multicast, cast them, and forward them on."""

    def Subscribe(self, request, context):  # -> InfluxUnknownMessage
        print("Got a connection!")
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


class InfluxReceiver(InfluxTranslatorServicer):
    def InfluxSubscribe(self, request, context):  # -> InfluxEvent
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
                    messages: List[IndigoUnknownMessage] = get_messages_from_msg(data)
                    tosend: List[InfluxEvent] = get_influx_events(messages)
                    for msg in tosend:
                        print(msg)
                        yield msg

        finally:
            # Close socket
            sock.close()
            print('Server stopped.')

# server.py
import grpc
from indigo_protobuf import indigo_pb2_grpc
from indigo_protobuf import indigo_influx_pb2_grpc


def serve():
    server_address = f'{SERVER_IP_BINDING}:{SERVER_PORT}'
    print(f"My server address {server_address}")

    server = grpc.server(ThreadPoolExecutor(max_workers=8))
    indigo_pb2_grpc.add_TranslatorServicer_to_server(IndigoReceiver(), server)
    # indigo_influx_pb2_grpc.add_InfluxTranslatorServicer_to_server(InfluxReceiver(), server)

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
