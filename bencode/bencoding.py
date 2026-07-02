import re
from collections import deque

STR_PATTERN = rb'\d+:\w+'


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
            string = chunks[self.bottom_index+sep+1:self.bottom_index+sep+int(len_str)+1]
            print(len_str, string, len(string))
            self.bottom_index += sep + int(len_str) + 1
            return string