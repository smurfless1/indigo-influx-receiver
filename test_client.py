import grpc

from indigo_protobuf import indigo_pb2_grpc, indigo_pb2

channel = grpc.insecure_channel('192.168.1.85:60000')
stub = indigo_pb2_grpc.TranslatorStub(channel)

try:
    for msg in stub.Subscribe(indigo_pb2.SubscribeArgs(multicast_port=8087)):
        print(msg)
except KeyboardInterrupt:
    print("Heard you, closing up now.")
    channel.close()