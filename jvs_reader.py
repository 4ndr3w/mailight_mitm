import enum

SYNC_BYTE = 0xE0
ESCAPE_BYTE = 0xD0

class BufferState(enum.Enum):
    READ_PACKET_LEN = enum.auto()
    READ_PACKET_METADATA = enum.auto()
    NORMAL_READ = enum.auto()
    ESCAPE_READ = enum.auto()
    PACKET_READY = enum.auto()
    CHECKSUM_ERROR = enum.auto()

class Buffer:
    def __init__(self):
        self.reset()

    def reset(self) -> None:
        self._buffer = []
        self._raw_buffer = []
        self._pos = 0
        self._checksum = 0
        self._frame_len = 0

        self._state = BufferState.READ_PACKET_LEN

    def _next_pos(self) -> int:
        p = self._pos
        self._pos += 1
        return p

    def read_char(self, c: int) -> None:
        if self._state == BufferState.PACKET_READY:
            self._buffer = []
            self._raw_buffer = []

        self._raw_buffer.append(c)

        if c == SYNC_BYTE:
            if len(self._buffer) != 0 and self._state is not BufferState.PACKET_READY:
                print("Sync byte while reading packet")
                print(f"\tGot {len(self._buffer)} packets of {self._frame_len}")

            self._state = BufferState.READ_PACKET_METADATA
            self._src_id = None
            self._dst_id = None
            self._buffer = []
            return
 
        if self._state is BufferState.READ_PACKET_METADATA:
            if self._dst_id is None:
                self._dst_id = c
                self._checksum = c
            else:
                self._src_id = c
                self._checksum += c
                self._state = BufferState.READ_PACKET_LEN

        elif self._state is BufferState.READ_PACKET_LEN:
            # Command isn't in count
            self._frame_len = c + 1
            self._checksum += c
            self._pos = 0
            self._state = BufferState.NORMAL_READ
        elif self._state is BufferState.NORMAL_READ or self._state == BufferState.ESCAPE_READ:
            if c == ESCAPE_BYTE:
                self._state = BufferState.ESCAPE_READ
                return

            if self._state == BufferState.ESCAPE_READ:
                c += 1
                self._state = BufferState.NORMAL_READ

            pos = self._next_pos()
            self._buffer.append(c)
            if self._frame_len == self._pos:
                if self._checksum % 256 == c:
                    self._state = BufferState.PACKET_READY
                else:
                    print(f"Checksum was {self._checksum % 256} expected {c}")
                    self.reset()
            self._checksum += c

def validate(buffer):
    processor = Buffer()
    for b in buffer[:-1]:
        processor.read_char(b)
        assert processor._state != BufferState.PACKET_READY
    processor.read_char(buffer[-1])
    assert processor._state == BufferState.PACKET_READY
