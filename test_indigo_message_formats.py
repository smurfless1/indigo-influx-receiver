import json
import unittest

from main import load_event_list


class MyTestCase(unittest.TestCase):
    def test_light_on(self):
        msg = '[{"fields": {"lastChanged": 1592271163.0, "displayStateValRaw": "100.0", "name": "Up blue bath light", "brightness": ' \
              '100.0, "state.onOffState.num": 1.0, "state.brightnessLevel": 100.0, "id": 732172634.0, "state.brightnessLevel.num": 100.0, ' \
              '"brightness.num": 100.0, "displayStateImageSel": "201.0", "state.onOffState": true, "onState": true, "lastSuccessfulComm": ' \
              '1592271163.0, "displayStateValUi": "100", "onState.num": 1.0}, "tags": {"folder": "Bathrooms", "folderId": "11868456", ' \
              '"name": "Up blue bath light"}, "measurement": "device_changes"}] '
        for evt in load_event_list(msg):
            self.assertTrue(isinstance(evt.fields.last_changed, float))
            self.assertTrue(isinstance(evt.fields.last_successful_comm, float))
            self.assertTrue(isinstance(evt.fields.name, str))
            self.assertEqual("Up blue bath light", evt.fields.name)
            self.assertEqual(100.0, evt.fields.brightness)
            self.assertEqual(True, evt.fields.on_state)
            self.assertEqual(1.0, evt.fields.on_state_num)

    def test_light_off(self):
        msg = '[{"fields": {"lastChanged": 1592271012.0, "displayStateValRaw": "0.0", "name": "Master vanity", "brightness": 0.0, ' \
              '"state.onOffState.num": 0.0, "state.brightnessLevel": 0.0, "id": 947891327.0, "state.brightnessLevel.num": 0.0, ' \
              '"brightness.num": 0.0, "displayStateImageSel": "200.0", "state.onOffState": false, "onState": false, "lastSuccessfulComm": ' \
              '1592271012.0, "displayStateValUi": "0", "onState.num": 0.0}, "tags": {"folder": "Bathrooms", "folderId": "11868456", ' \
              '"name": "Master vanity"}, "measurement": "device_changes"}] '
        for evt in load_event_list(msg):
            self.assertEqual("Master vanity", evt.fields.name)
            self.assertEqual(0.0, evt.fields.brightness)
            self.assertEqual(False, evt.fields.on_state)
            self.assertEqual(0.0, evt.fields.on_state_num)
            self.assertEqual("device_changes", evt.measurement)

    def test_hvac_on(self):
        msg = '[{"fields": {"name": "Downstairs thermostat", "lastChanged": 1592261009.0, "state.hvacCoolerIsOn": true, ' \
              '"state.hvacCoolerIsOn.num": 1.0, "displayStateImageSel": "505.0", "coolIsOn.num": 1.0, "lastSuccessfulComm": 1592261009.0, ' \
              '"coolIsOn": true, "id": 1782566639.0}, "tags": {"folder": "Thermostats", "folderId": "965844786", "name": "Downstairs ' \
              'thermostat"}, "measurement": "thermostat_changes"}] '

        for evt in load_event_list(msg):
            self.assertEqual("Downstairs thermostat", evt.fields.name)
            self.assertEqual(None, evt.fields.brightness)
            self.assertEqual(True, evt.fields.cool_is_on)
            self.assertEqual(1.0, evt.fields.cool_is_on_num)
            self.assertEqual("thermostat_changes", evt.measurement)

    def test_hvac_humidity_change(self):
        msg = '[{"fields": {"name": "Upstairs thermostat", "lastChanged": 1592271000.0, "state.humidityInputsAll": "43", ' \
              '"state.humidityInputsAll.num": 43.0, "state.humidityInput1": 43.0, "lastSuccessfulComm": 1592271000.0, "id": 635537221.0}, ' \
              '"tags": {"folder": "Thermostats", "folderId": "965844786", "name": "Upstairs thermostat"}, "measurement": ' \
              '"thermostat_changes"}] '
        for evt in load_event_list(msg):
            self.assertEqual("Upstairs thermostat", evt.fields.name)
            self.assertEqual(None, evt.fields.cool_is_on)
            self.assertEqual(43.0, evt.fields.state_humidity_input1)
            self.assertEqual("thermostat_changes", evt.measurement)

    def test_hvac_heat_point_change(self):
        msg = '[{"fields": {"heatSetpoint": 43.0, "state.setpointHeat": 43.0, "lastChanged": 1592260868.0, "lastSuccessfulComm": ' \
              '1592260868.0, "id": 635537221.0, "name": "Upstairs thermostat"}, "tags": {"folder": "Thermostats", "folderId": ' \
              '"965844786", "name": "Upstairs thermostat"}, "measurement": "thermostat_changes"}] '
        for evt in load_event_list(msg):
            self.assertEqual("Upstairs thermostat", evt.fields.name)
            self.assertEqual(43.0, evt.fields.heat_setpoint)
            self.assertEqual("thermostat_changes", evt.measurement)

    def test_hvac_cool_point_change(self):
        msg = '[{"fields": {"state.setpointCool": 69.0, "name": "Upstairs thermostat", "lastChanged": 1592260869.0, "coolSetpoint": 69.0, ' \
              '"lastSuccessfulComm": 1592260869.0, "id": 635537221.0}, "tags": {"folder": "Thermostats", "folderId": "965844786", ' \
              '"name": "Upstairs thermostat"}, "measurement": "thermostat_changes"}] '
        for evt in load_event_list(msg):
            self.assertEqual("Upstairs thermostat", evt.fields.name)
            self.assertEqual(69.0, evt.fields.cool_setpoint)
            self.assertEqual("thermostat_changes", evt.measurement)

    def test_hvac_temp_change(self):
        msg = '[{"fields": {"dehumidifierIsOn.num": 0.0, "supportsCoolSetpoint.num": 1.0, "state.hvacOperationModeIsOff": false, ' \
              '"state.hvacHeaterIsOn": false, "pluginId": "", "lastSuccessfulComm": 1592317471.0, "protocol": "1.0", "state.hvacFanIsOn": ' \
              'false, "errorState": "", "state.hvacDehumidifierIsOn.num": 0.0, "state.humidityInputsAll": "42", ' \
              '"state.hvacOperationMode.ui": "auto on", "state.hvacFanModeIsAlwaysOn": false, "hvacMode": 3.0, ' \
              '"state.hvacCoolerIsOn.num": 1.0, "state.hvacOperationMode.num": 3.0, "temperatureSensorCount.num": 1.0, ' \
              '"state.hvacOperationModeIsHeat": false, "state.setpointHeat": 68.0, "state.hvacOperationModeIsOff.num": 0.0, ' \
              '"name": "Upstairs thermostat", "state.temperatureInput1": 75.0, "humidifierIsOn.num": 0.0, "state.hvacFanModeIsAuto": ' \
              'true, "supportsAllOff.num": 0.0, "enabled.num": 1.0, "fanIsOn.num": 0.0, "state.hvacOperationModeIsProgramHeat": false, ' \
              '"configured": true, "state.hvacOperationModeIsHeat.num": 0.0, "remoteDisplay.num": 1.0, "buttonGroupCount.num": 5.0, ' \
              '"coolIsOn.num": 1.0, "state.hvacOperationModeIsProgramCool": false, "displayStateValUi": "75", "hvacMode.num": 3.0, ' \
              '"coolSetpoint": 75.0, "state.hvacDehumidifierIsOn": false, "state.hvacOperationModeIsProgramAuto": false, "version": 13.0, ' \
              '"displayStateId": "temperatureInputsAll", "fanMode.num": 0.0, "state.hvacFanMode": 0.0, "supportsHvacFanMode": true, ' \
              '"supportsAllLightsOnOff.num": 0.0, "humiditySensorCount.num": 1.0, "address": "29.58.C2", "id.num": 635537221.0, ' \
              '"supportsCoolSetpoint": true, "state.hvacFanMode.num": 0.0, "lastChanged": 1592317471.0, "version.num": 13.0, ' \
              '"displayStateImageSel": "505.0", "state.hvacFanModeIsAuto.num": 1.0, "displayStateValRaw": "75", "fanIsOn": false, ' \
              '"humiditySensorCount": 1.0, "state.humidityInputsAll.num": 42.0, "state.temperatureInputsAll": "75", "subModel": "", ' \
              '"supportsAllOff": false, "state.hvacOperationModeIsProgramAuto.num": 0.0, "state.hvacOperationMode": 3.0, ' \
              '"temperatureSensorCount": 1.0, "supportsStatusRequest": true, "supportsHeatSetpoint.num": 1.0, "supportsHvacFanMode.num": ' \
              '1.0, "state.hvacFanModeIsAlwaysOn.num": 0.0, "heatIsOn.num": 0.0, "folderId": 965844786.0, "supportsHeatSetpoint": true, ' \
              '"humidifierIsOn": false, "supportsStatusRequest.num": 1.0, "enabled": true, "state.hvacFanMode.ui": "auto on", ' \
              '"remoteDisplay": true, "supportsAllLightsOnOff": false, "state.hvacHumidifierIsOn.num": 0.0, ' \
              '"state.hvacOperationModeIsCool.num": 0.0, "state.hvacHumidifierIsOn": false, "state.hvacOperationModeIsProgramCool.num": ' \
              '0.0, "heatIsOn": false, "state.hvacOperationModeIsCool": false, "buttonGroupCount": 5.0, "id": 635537221.0, ' \
              '"state.hvacOperationModeIsAuto": true, "state.setpointCool": 75.0, "deviceTypeId": "", "configured.num": 1.0, ' \
              '"dehumidifierIsOn": false, "state.hvacOperationModeIsAuto.num": 1.0, "folderId.num": 965844786.0, ' \
              '"supportsHvacOperationMode": true, "state.hvacHeaterIsOn.num": 0.0, "description": "", "state.temperatureInputsAll.num": ' \
              '75.0, "supportsHvacOperationMode.num": 1.0, "state.hvacOperationModeIsProgramHeat.num": 0.0, "coolIsOn": true, ' \
              '"heatSetpoint": 68.0, "fanMode": 0.0, "state.hvacCoolerIsOn": true, "state.humidityInput1": 42.0, "state.hvacFanIsOn.num": ' \
              '0.0, "model": "Thermostat (2441TH)"}, "tags": {"folder": "Thermostats", "folderId": "965844786", "name": "Upstairs ' \
              'thermostat"}, "measurement": "thermostat_changes"}] '
        for evt in load_event_list(msg):
            self.assertEqual(78.0, evt.fields.state_temperature_input1)
            self.assertEqual("thermostat_changes", evt.measurement)

    def test_irrigation_change(self):
        msg ='[{"fields": {"lastSuccessfulComm": 1592271087.0, "id": 1414136842.0, "name": "Irrigation", "lastChanged": 1592271087.0}, ' \
             '"tags": {"folderId": "0", "name": "Irrigation"}, "measurement": "device_changes"}] '
        pass  # yeah whatever


if __name__ == '__main__':
    unittest.main()
