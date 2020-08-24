import datetime
from typing import Optional, List

import arrow

from google.protobuf.timestamp_pb2 import Timestamp
from dateutil import tz
from google.protobuf import json_format

from indigo_protobuf.indigo_pb2 import IndigoUnknownMessage, HvacFields, DimmerSwitchFields, SecurityFields, GenericFields, \
    BinarySwitchFields
from indigo_protobuf.indigo_influx_pb2 import InfluxEvent, InfluxFields, InfluxTag


FULL_ON = 100.0
FULL_OFF = 0.0


def make_unknown_message(elt: dict) -> IndigoUnknownMessage:
    msg = json_format.ParseDict(elt, IndigoUnknownMessage(), ignore_unknown_fields=True)
    if msg.measurement.value == "thermostat_changes":
        msg.hvac.CopyFrom(json_format.ParseDict(elt["fields"], HvacFields(), ignore_unknown_fields=True))
        msg.time.FromDatetime(dt=arrow.get(msg.hvac.lastSuccessfulComm.value).datetime)
    elif msg.measurement.value == "device_changes":
        if "displayStateId" not in elt["fields"].keys():
            msg.generic.CopyFrom(json_format.ParseDict(elt["fields"], GenericFields(), ignore_unknown_fields=True))
            msg.time.FromDatetime(dt=arrow.get(msg.generic.lastSuccessfulComm.value).datetime)
            # print("Did not find displayStateId in:")
            # print(elt["fields"].keys())
            # print("Using generic update fields.")
        elif elt["fields"]["displayStateId"] == "onOffState":
            msg.binary.CopyFrom(json_format.ParseDict(elt["fields"], BinarySwitchFields(), ignore_unknown_fields=True))
            msg.time.FromDatetime(dt=arrow.get(msg.binary.lastSuccessfulComm.value).datetime)
        elif elt["fields"]["displayStateId"] == "brightnessLevel":
            msg.dimmer.CopyFrom(json_format.ParseDict(elt["fields"], DimmerSwitchFields(), ignore_unknown_fields=True))
            msg.time.FromDatetime(dt=arrow.get(msg.dimmer.lastSuccessfulComm.value).datetime)
        elif elt["fields"]["displayStateId"] == "state":
            msg.security.CopyFrom(json_format.ParseDict(elt["fields"], SecurityFields(), ignore_unknown_fields=True))
            msg.time.FromDatetime(dt=arrow.get(msg.security.lastSuccessfulComm.value).datetime)
    else:
        print(f"what is this? {elt}")

    # thou shalt have a TIME!
    if msg.time is None:
        msg.time = Timestamp().FromDatetime(dt=arrow.get().datetime)

    return msg


class InfluxOutbound:
    def __init__(self, msg: IndigoUnknownMessage):
        self.message: IndigoUnknownMessage = msg
        self.name = msg.WhichOneof("fields")
        self.val = None
        if not self.name or self.name == "":
            return
        try:
            self.val = getattr(msg, self.name)
        except (TypeError, AttributeError):
            return

    @property
    def time(self) -> datetime.datetime:
        return arrow.get(getattr(self.val, "lastSuccessfulComm")).replace(tzinfo=tz.tzlocal()).datetime

    @property
    def fields(self) -> dict:
        if self.val is None:
            return {}
        return self.val.to_dict()

    @property
    def on(self) -> Optional[float]:
        if self.name == "" or self.name == "generic":
            return None
        elif self.name == "binary" and self.val.onState.value:
            return True
        elif self.name == "dimmer" and self.val.brightness.value != 0.0:
            return True
        elif self.name == "hvac" and (self.val.coolIsOn.value or self.val.heatIsOn.value):
            return True
        elif self.name == "security":  # and self.val.state_state_tripped:
            return None
        else:
            return False

    @property
    def brightness(self) -> Optional[float]:
        if self.name == "" or self.name == "generic":
            return None
        elif self.name == "binary" and self.val.onState.value:
            return FULL_ON
        elif self.name == "dimmer":
            return self.val.brightness.value
        elif self.name == "hvac" and (self.val.coolIsOn.value or self.val.heatIsOn.value):
            return FULL_ON
        elif self.name == "security": #  and self.val.state_state_tripped:
            return None
        else:
            return FULL_OFF

    @property
    def cool(self) -> Optional[float]:
        return self.val.coolSetpoint.value if self.name == "hvac" else None

    @property
    def heat(self) -> Optional[float]:
        return self.val.heatSetpoint.value if self.name == "hvac" else None

    @property
    def temperature(self) -> Optional[float]:
        return self.val.state_temperatureInput1.value if self.name == "hvac" else None

    @property
    def humidity(self) -> Optional[float]:
        return self.val.state_humidityInput1.value if self.name == "hvac" else None

    @property
    def influx_values(self) -> List:
        return [self.on, self.brightness, self.cool, self.heat, self.humidity, self.temperature]

    @property
    def event(self) -> InfluxEvent:
        return InfluxEvent(
            measurement=self.message.measurement.value,
            time=self.time,
            tags=InfluxTag(name=self.message.tags.name.value, folder=self.message.tags.folder.value),
            fields=InfluxFields(on=self.on, brightness=self.brightness, coolSetpoint=self.cool, heatSetpoint=self.heat,
                                humidity=self.humidity, temperature=self.temperature)
        )

    @property
    def json(self) -> str:
        return self.event.to_json()

    def sendable(self) -> bool:
        # todo what constitutes a field you don't want to count against your quota?
        failcauses = [
            self.name == "generic",
            self.val is None,
            not hasattr(self.val, "lastSuccessfulComm"),
            all([v is None for v in self.influx_values]),
        ]
        return False if any(failcauses) else True
