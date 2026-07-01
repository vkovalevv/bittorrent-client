import re
from collections import deque

STR_PATTERN = rb'\d+:\w+'


class Decoder:
    def __init__(self, val: bytes):
        self.val = val

    def decode(self):
        result, _ = self._dechunk(self.val)
        return result

    def _dechunk(self, chunks: bytes):
        match = re.match(STR_PATTERN, chunks)
        token = None
        if not match: 
            token = chunks[:1]
            chunks = chunks[1:] 
        if token == b'i':
            end = chunks.find(b'e')
            num = chunks[:end]
            chunks = chunks[end+1:]
            return (int(num.decode()), chunks)
        elif token == b'd':
            dct = {}
            while chunks[:1] != b'e':
                key, chunks = self._dechunk(chunks)
                value, chunks = self._dechunk(chunks)
                dct[key] = value
            chunks = chunks[1:]
            return (dct, chunks)
        elif token == b'l':
            lst = []
            while chunks[:1] != b'e':
                print(chunks)
                val, chunks = self._dechunk(chunks)
                lst.append(val)
            chunks = chunks[1:]
            return (lst, chunks)
        elif match:
            try:
                sep = chunks.find(b':')
                len_str = chunks[:sep]
                string = chunks[sep+1:sep+int(len_str)+1]
                chunks = chunks[sep+int(len_str)+1:]
                if int(len_str) != len(string):
                    raise ValueError('Incorrect value!')
            except ValueError as e:
                print(e)
            return (string.decode(), chunks)
        else:
            print(token)
            raise ValueError(f'Incorrect value!:{token}')
