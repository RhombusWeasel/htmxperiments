#!/usr/bin/python3

import json
from distutils.log import WARN
from datetime import datetime

col = {
    "red": "\033[38;5;208m",
    "yellow": "\033[38;5;226m",
    "pink": "\033[38;5;201m",
    "green": "\033[38;5;82m",
    "purple": "\033[38;5;129m",
    "orange": "\033[38;5;172m",
    "blue": "\033[38;5;27m",
    "white": "\033[38;5;15m",
    "reset": "\033[0m"
}

pipe = f"{col['purple']}|{col['white']}"


class Logger:

    DEBUG = 0
    INFO = 1
    DATA = 2
    WARN = 3
    ERROR = 4

    colors = [
        "\033[38;5;33m",
        "\033[38;5;15m",
        "\033[38;5;82m",
        "\033[38;5;172m",
        "\033[38;5;196m",
    ]

    def __init__(self, label, log_level=1):
        self.label = label
        self.log_level = log_level

    def timestamp(self):
        return datetime.now().strftime(f"{pipe}%Y-%m-%d{pipe}%H:%M:%S{pipe}")

    def log(self, msg, lvl):
        if lvl < self.log_level:
            return
        print(f"{self.timestamp()} {self.label:<12} {self.colors[lvl]}{msg}{col['reset']}")

    def debug(self, msg):
        self.log(msg, self.DEBUG)

    def info(self, msg):
        self.log(msg, self.INFO)

    def data(self, msg):
        self.log(msg, self.DATA)

    def warn(self, msg):
        self.log(msg, self.WARN)

    def error(self, msg):
        self.log(msg, self.ERROR)
    
    def json(self, msg):
        print(f"{self.timestamp()} {self.label:<12}{json.dumps(msg, indent=2, sort_keys=True)}")


if __name__ == "__main__":
    l = Logger('log-test', log_level=Logger.DEBUG)

    def test_levels(l):
        l.debug('Testing DEBUG text.')
        l.info('Testing INFO text')
        l.warn('Testing WARN text')
        l.error('Testing ERROR text')

    l.info('Beginning Logger Test. Level: DEBUG')
    test_levels(l)

    l.log_level = l.INFO
    l.info('Beginning Logger Test. Level: INFO')
    test_levels(l)

    l.log_level = l.WARN
    l.warn('Beginning Logger Test. Level: WARN')
    test_levels(l)

    l.log_level = l.ERROR
    l.error('Beginning Logger Test. Level: ERROR')
    test_levels(l)
