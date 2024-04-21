import sys
import enum
from struct import pack

from jvs_reader import Buffer, BufferState

SYNC_BYTE = 0xE0
ESCAPE_BYTE = 0xD0

board_id = b"15070-04"

def serialize_response(response):
    send_buffer = [SYNC_BYTE]
    checksum = 0
    for b in response:
        checksum += b
        if b == SYNC_BYTE or b == ESCAPE_BYTE:
            send_buffer.append(0xD0)
            send_buffer.append(b - 1)
        else:
            send_buffer.append(b)
    send_buffer.append(checksum % 256)
    return send_buffer

def make_response(dst, src, status, cmd, report, size = 0):
    size += 3
    return pack("BBBBBB", dst, src, size, status, cmd, report)

def make_request(dst, src, cmd, size = 0):
    size += 1
    return pack("BBBB", dst, src, size, cmd)

def make_ack(my_id, command):
    return make_response(1, my_id, 1, command, 1)

class LEDCommandType(enum.Enum):
    Reset = 16
    SetLED = 0x31
    SetMultiLED = 0x32
    SetMultiLEDFade = 51
    SetDc = 63
    UpdateDc = 59

    SetFet = 57
    Commit = 60
    GetBoardInfoCommand = 240
    GetProtocolVersionCommand = 243
    GetBoardStatusCommand = 241
    EepromWrite = 123
    EepromRead = 124
    SetTimeout = 17

def process(f, buf: Buffer):
    c = f.read(1)
    if len(c) == 0:
        sys.exit(1)
    buf.read_char(ord(c))
    if buf._state == BufferState.PACKET_READY:
        command = buf._buffer[0]
        if command == LEDCommandType.GetBoardInfoCommand.value:
            print("GetBoardInfoCommand")
            msg = board_id + pack("BB", 255, 1)
            buf = make_response(1, buf._dst_id, 1, command, 1, len(msg))
            buf += msg
            return buf
        return True
    return False
