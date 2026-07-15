import asyncio
import hashlib
import httpx
import secrets
import socket
import struct

from urllib.parse import urlencode

from client.bencoding import Decoder, Encoder
from client.peer import Handshake


async def send_handshake(info_hash, peer_id, ip, port):
    try:
        print(f'Send handshake to: {ip}:{port}')
        handshake = Handshake(info_hash, peer_id)
        reader, writer = await asyncio.open_connection(ip, port)
        print(f'Open connection to: {ip}:{port}')
        writer.write(handshake.serialize())
        await writer.drain()

        buf = b''
        i = 0
        while len(buf) != handshake.length and i != 10:
            buf = await reader.readexactly(handshake.length)
            i += 1
        print(buf)
        return buf
    except Exception as e:
        print(f"fail with {ip}:{port} [{e}]")
    return


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


async def get_peers(url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        decode_data = Decoder(response.read()).decode()
        peer_list = []
        peers = decode_data[b'peers']
        print(decode_data)
        for i in range(0, len(peers), 6):
            ip = socket.inet_ntoa(peers[i:i+4])
            port = struct.unpack('>H', peers[i+4:i+6])[0]
            peer_list.append((ip, port))
    return peer_list


async def main():
    data = extract_data(
        "/Users/vkovalev/Desktop/yandex/bittorrent/client/test2.torrent"
    )
    info = data[b'info']
    info_hash = hashlib.sha1(Encoder(info).encode()).digest()
    peer_id = generate_peer_id()
    query_data = {
        'info_hash': info_hash,
        'peer_id': peer_id,
        'port': 6881,
        'uploaded': 0,
        'downloaded': 0,
        'left': info[b'length'],
        'compact': 1
    }
    url = data[b'announce'].decode() + '?' + urlencode(query_data)
    peers = await get_peers(url)
    tasks = [send_handshake(
        info_hash=info_hash, peer_id=peer_id, ip=ip, port=port) for ip, port in peers]
    result = await asyncio.gather(*tasks)
    print(result)
asyncio.run(main())
