from pathlib import Path
import json

try:
    from .indigo import IndigoUnknownMessage, HvacFields, DimmerSwitchFields, SecurityFields, GenericFields, BinarySwitchFields, InfluxEvent, InfluxFields, InfluxTag
except ImportError:
    from indigo import IndigoUnknownMessage, HvacFields, DimmerSwitchFields, SecurityFields, GenericFields, BinarySwitchFields, InfluxEvent, InfluxFields, InfluxTag

try:
    from .influx_outbound import InfluxOutbound, make_unknown_message
except ImportError:
    from influx_outbound import InfluxOutbound, make_unknown_message


with Path("~/Resilio Sync/Sync/newelog.json").expanduser().open("r", encoding='utf-8') as logfile:
    for line in logfile:
        loaded = json.loads(line)
        if isinstance(loaded, list):
            for elt in loaded:
                msg = make_unknown_message(elt)
                out = InfluxOutbound(msg)
                if out.sendable():
                    print(out.json)
        if isinstance(loaded, dict):
            # debug printed, ignore
            continue
