# -*- coding: utf-8 -*-
"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app
"""

from setuptools import setup

APP = ['send_to_influx.py']
APP_NAME = "Indigo Influx Receiver"
DATA_FILES = []

OPTIONS = {
    'argv_emulation': True,
    # 'iconfile': 'app.icns',
    'plist': {
        'CFBundleName': APP_NAME,
        'CFBundleDisplayName': APP_NAME,
        'CFBundleGetInfoString': "Send Indigo data to InfluxDB",
        'CFBundleIdentifier': "com.smurfless.indigoinflux1",
        'CFBundleVersion': "0.1.0",
        'CFBundleShortVersionString': "0.1.0",
        'NSHumanReadableCopyright': u"Copyright 2018, Dave Brown, All Rights Reserved"
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)

