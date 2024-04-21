#!/usr/bin/env python3

from jvs_reader import Buffer, BufferState
from process import process, serialize_response

import serial
import click

import sys
import enum
import threading
from struct import pack


lock = threading.Lock()


def proxy_thread(alls_port, cab_port):
    while True:
        c = cab_port.read(1)
        with lock:
            alls_port.write(c)
            alls_port.flush()

@click.command()
@click.argument("alls_port")
@click.argument("cab_port")
def main(alls_port: str, cab_port: str):
    alls_port = serial.Serial(alls_port, baudrate=115200)
    cab_port = serial.Serial(cab_port, baudrate=115200)
    thread = threading.Thread(target=proxy_thread, args=(alls_port, cab_port))
    thread.setDaemon(True)
    thread.start()

    buf = Buffer()

    while alls_port.is_open and cab_port.is_open:
        resp = process(alls_port, buf)
        if resp is True:
            cab_port.write(buf._raw_buffer)
            cab_port.flush()
        elif resp:
            resp = serialize_response(resp)
            with lock:
                alls_port.write(resp)
                alls_port.flush()


if __name__ == "__main__":
    main()
