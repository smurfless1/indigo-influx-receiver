import datetime
from typing import Optional, List

import arrow

import betterproto
from dateutil import tz

from indigo_protobuf_betterproto.indigo import IndigoUnknownMessage, HvacFields, DimmerSwitchFields, SecurityFields, GenericFields, \
    BinarySwitchFields
from indigo_protobuf_betterproto.indigo_influx import InfluxEvent, InfluxFields, InfluxTag


FULL_ON = 100.0
FULL_OFF = 0.0


def make_unknown_message(elt: dict) -> IndigoUnknownMessage:
    msg = IndigoUnknownMessage().from_dict(value=elt)
    if msg.measurement == "thermostat_changes":
        msg.hvac = HvacFields().from_dict(elt["fields"])
        msg.time = arrow.get(msg.hvac.last_successful_comm).datetime
    elif msg.measurement == "device_changes":
        if "displayStateId" not in elt["fields"].keys():
            msg.generic = GenericFields().from_dict(elt["fields"])
            msg.time = arrow.get(msg.generic.last_successful_comm).datetime
            # print("Did not find displayStateId in:")
            # print(elt["fields"].keys())
            # print("Using generic update fields.")
        elif elt["fields"]["displayStateId"] == "onOffState":
            msg.binary = BinarySwitchFields().from_dict(elt["fields"])
            msg.time = arrow.get(msg.binary.last_successful_comm).datetime
        elif elt["fields"]["displayStateId"] == "brightnessLevel":
            msg.dimmer = DimmerSwitchFields().from_dict(elt["fields"])
            msg.time = arrow.get(msg.dimmer.last_successful_comm).datetime
        elif elt["fields"]["displayStateId"] == "state":
            msg.security = SecurityFields().from_dict(elt["fields"])
            msg.time = arrow.get(msg.security.last_successful_comm).datetime

    # thou shalt have a TIME!
    if msg.time is None:
        msg.time = arrow.get().datetime

    return msg


class InfluxOutbound:
    def __init__(self, msg: IndigoUnknownMessage):
        self.message: IndigoUnknownMessage = msg
        self.name, self.val = betterproto.which_one_of(self.message, "fields")

    @property
    def time(self) -> datetime.datetime:
        return arrow.get(getattr(self.val, "last_successful_comm")).replace(tzinfo=tz.tzlocal()).datetime

    @property
    def fields(self) -> dict:
        if self.val is None:
            return {}
        return self.val.to_dict()

    @property
    def on(self) -> Optional[float]:
        if self.name == "" or self.name == "generic":
            return None
        elif self.name == "binary" and self.val.on_state:
            return True
        elif self.name == "dimmer" and self.val.brightness != 0.0:
            return True
        elif self.name == "hvac" and (self.val.cool_is_on or self.val.heat_is_on):
            return True
        elif self.name == "security":  # and self.val.state_state_tripped:
            return None
        else:
            return False

    @property
    def brightness(self) -> Optional[float]:
        if self.name == "" or self.name == "generic":
            return None
        elif self.name == "binary" and self.val.on_state:
            return FULL_ON
        elif self.name == "dimmer":
            return self.val.brightness
        elif self.name == "hvac" and (self.val.cool_is_on or self.val.heat_is_on):
            return FULL_ON
        elif self.name == "security": #  and self.val.state_state_tripped:
            return None
        else:
            return FULL_OFF

    @property
    def cool(self) -> Optional[float]:
        return self.val.cool_setpoint if self.name == "hvac" else None

    @property
    def heat(self) -> Optional[float]:
        return self.val.heat_setpoint if self.name == "hvac" else None

    @property
    def temperature(self) -> Optional[float]:
        return self.val.state_temperature_input1 if self.name == "hvac" else None

    @property
    def humidity(self) -> Optional[float]:
        return self.val.state_humidity_input1 if self.name == "hvac" else None

    @property
    def influx_values(self) -> List:
        return [self.on, self.brightness, self.cool, self.heat, self.humidity, self.temperature]

    @property
    def event(self) -> InfluxEvent:
        return InfluxEvent(
            measurement=self.message.measurement,
            time=self.time,
            tags=InfluxTag(name=self.message.tags.name, folder=self.message.tags.folder),
            fields=InfluxFields(on=self.on, brightness=self.brightness, cool_setpoint=self.cool, heat_setpoint=self.heat,
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
            not hasattr(self.val, "last_successful_comm"),
            all([v is None for v in self.influx_values]),
        ]
        return False if any(failcauses) else True
