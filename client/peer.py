import struct

# version 1.0 BitTorrent protocol
PROTOCOL = 'BitTorrent protocol'


class Handshake:
    def __init__(self, info_hash, peer_id):
        self.info_hash = info_hash
        self.peer_id = peer_id
        self.pstrlen = len(PROTOCOL)
        self.pstr = PROTOCOL.encode('utf-8')
        return
    
    def serialize(self) -> bytes:
        handshake_bytes = struct.pack('>b19s8x20s20s',
                                      self.pstrlen,
                                      self.pstr,
                                      self.info_hash,
                                      self.peer_id)
        return handshake_bytes

    @property
    def length(self):
        return 49 + self.pstrlen
    
#async def _handshake(self, handshake: Handshake):
