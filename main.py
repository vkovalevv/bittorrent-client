import asyncio
import hashlib
import httpx
import secrets
import socket
import struct

import urllib
from urllib.parse import urlencode

from bencode.bencoding import Decoder, Encoder


def decode_peer_list(peers: bytes):
    for i in range(0, len(peers), 6):
        ip = socket.inet_ntoa(peers[i:i+4])
        port = struct.unpack('>H', peers[i+4:i+6])[0]
        print(ip, port)


def generate_peer_id():
    prefix = b'-YT0011-'

    random_bytes = secrets.token_bytes(12)

    return prefix + random_bytes


def extract_data(file: str) -> tuple:
    torrent_data = None

    with open(file, 'rb') as f:
        f_data = f.read()
        torrent_data = Decoder(f_data).decode()

    return torrent_data


async def get(url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        decode_data = Decoder(response.read()).decode()
        decode_peer_list(decode_data[b'peers'])


async def main():
    data = extract_data(
        '/Users/vkovalev/Desktop/yandex/bittorrent/bencode/test.torrent')
    info = data[b'info']
    info_hash = hashlib.sha1(Encoder(info).encode()).digest()
    peer_id = generate_peer_id()
    query_data = {
        'info_hash': info_hash,
        'peer_id': peer_id,
        'port': 6881,
        'uploaded': 0,
        'downloaded': 0,
        'length': info[b'length'],
        'compact': 1
    }
    url = data[b'announce'].decode() + '?' + urlencode(query_data)
    await get(url)

asyncio.run(main())
