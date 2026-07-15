import re
from collections import deque

STR_PATTERN = rb'\d+:'


class Decoder:
    def __init__(self, val: bytes):
        self.val = val
        self.bottom_index = 0

    def decode(self):
        result = self._dechunk(self.val)
        return result

    def _dechunk(self, chunks: bytes):
        match = re.match(STR_PATTERN, chunks[self.bottom_index:])
        token = None
        if not match:
            token = chunks[self.bottom_index:self.bottom_index+1]
            self.bottom_index += 1
        if token == b'i':
            end = chunks[self.bottom_index:].find(b'e')
            num = chunks[self.bottom_index:self.bottom_index+end]
            self.bottom_index += end + 1
            return int(num)
        elif token == b'd':
            dct = {}
            while chunks[self.bottom_index:self.bottom_index+1] != b'e':
                key = self._dechunk(chunks)
                value = self._dechunk(chunks)
                dct[key] = value
            self.bottom_index += 1
            return dct
        elif token == b'l':
            lst = []
            while chunks[self.bottom_index:self.bottom_index+1] != b'e':
                val = self._dechunk(chunks)
                lst.append(val)
            self.bottom_index += 1
            return lst
        elif match:
            sep = chunks[self.bottom_index:].find(b':')
            len_str = chunks[self.bottom_index:self.bottom_index+sep]
            string = chunks[self.bottom_index+sep +
                            1:self.bottom_index+sep+int(len_str)+1]
            self.bottom_index += sep + int(len_str) + 1
            return string


class Encoder:

    def __init__(self, val):
        self.val = val

    def encode(self):
        result = self.in_depth(self.val)
        return result

    def in_depth(self, val):
        match val:
            case int():
                num = str(val)
                return b'i' + num.encode() + b'e'
            case bytes():
                length = str(len(val))
                return length.encode() + b':' + val
            case list():
                lst = b''
                reverse = val[::-1]
                while reverse:
                    item = self.in_depth(reverse.pop())
                    lst += item
                lst = b'l' + lst + b'e'
                return lst
            case dict():
                dct = b''
                for key, value in sorted(val.items()):
                    key_encode = self.in_depth(key)
                    value_encode = self.in_depth(value)
                    dct += key_encode + value_encode
                dct = b'd' + dct + b'e'
                return dct