import asyncio
import hashlib
import httpx
import secrets
import socket
import struct

from urllib.parse import urlencode, quote_from_bytes

from client.bencoding import Decoder, Encoder
from client.peer import Handshake

class PeerConnection:
    def __init__(self, ip, port):
        self.buf = b''   
        self.ip = ip
        self.port = port 

    async def initialize(self) -> None:
        self.reader, self.writer = await asyncio.open_connection(self.ip, self.port)
        return

    async def send_handshake(self, handshake: Handshake):
        try:
            print(f'Send handshake to: {self.ip}:{self.port}')
            self.writer.write(handshake.serialize())
            await self.writer.drain()

            raw_response = await asyncio.wait_for(self.reader.readexactly(handshake.length), timeout= 10.0)
            self.buf = raw_response

            data = struct.unpack('>B19s8s20s20s', self.buf)
            pstrlen, pstr, reserved, received_info_hash, received_peer_id = data

            if pstrlen != 19 or received_info_hash:
                print(f"[{self.ip}:{self.port}] Ошибка: Неверная длина протокола ({pstrlen})")
                return None
            if pstr != b'BitTorrent protocol':
                print(f"[{self.ip}:{self.port}] Ошибка: Неверное имя протокола ({pstr})")
                return None
            if received_info_hash != handshake.info_hash:
                print(f"[{self.ip}:{self.port}] Ошибка: Info hash не совпадает!")   
                print(f"  Ожидался: {handshake.info_hash.hex()}")
                print(f"  Получен:  {received_info_hash.hex()}")
                return None
            
            return data 
        
        except asyncio.TimeoutError:
            print(f"Timeout with {self.ip}:{self.port}")
        except asyncio.IncompleteReadError as e:
            print(f"Connection closed by peer {self.ip}:{self.port} [{e}]")
        except Exception as e:
            print(f"fail with {self.ip}:{self.port} [{e}]")
        return

    async def read_message(self):
        try:
            length_data = await self.reader.readexactly(4)
            length = struct.unpack('>I', length_data)[0]

            if length == 0:
                return {"name":"keep-alive", "id": None, "payload":None}

            message_id_data = await self.reader.readexactly(1)
            message_id = struct.unpack('>B', message_id_data)[0]
            msg_name = self._get_message_name(message_id)

            payload_length = length - 1
            if payload_length > 0:
                payload = await self.reader.readexactly(payload_length)
                if msg_name == 'bitfield':
                    print(f"[{self.ip}:{self.port}] Bitfield длина: {payload_length} байт. Начало: {payload[:16].hex()}")
                else:
                    print(f"[{self.ip}:{self.port}] Сообщение: {msg_name}, payload длина: {payload_length}")
            else:
                payload = b''
                print(f"[{self.ip}:{self.port}] Сообщение: {msg_name} (без payload)")

            return {'name': msg_name, 'id': message_id, 'payload':payload}
        
        except asyncio.IncompleteReadError:
            print(f"[{self.ip}:{self.port}] Пир закрыл соединение во время чтения сообщения")
            return None
    async def interact(self, handshake):
        try:
            await self.initialize()

            result_handshake = await self.send_handshake(handshake)

            if result_handshake is None:
                return None

            received_messages = [] 
            while True:
                result_message = await self.read_message()

                if result_message is None:
                    break

                received_messages.append(result_message)

                if len(received_messages) >= 5:
                    print(f'Получено {len(received_messages)} сообщений') 
                    break

            return result_message

        except Exception as e:
            print(f"Ошибка при взаимодействии с {self.ip}:{self.port}: {e}")
            return None
        finally:
            await self.close()


    async def close(self):
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()

    def _get_message_name(self, id):
        names = {
            0: 'choke', 1: 'unchoke', 2: 'interested', 3: 'not interested',
            4: 'have', 5: 'bitfield', 6: 'request', 7: 'piece', 8: 'cancel'
        }
        return names.get(id, f'unknown_{id}')

    def _parse_bitfield(self, buffer: bytes):
        pass

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
        buf = await asyncio.wait_for(
            reader.readexactly(handshake.length), 
            timeout=10.0
        )
        print(f'Received {len(buf)} bytes')

        data = struct.unpack('>b19s8x20s20s', buf)
        print(data)
        return buf
    except asyncio.TimeoutError:
        print(f"Timeout with {ip}:{port}")
    except asyncio.IncompleteReadError as e:
        print(f"Connection closed by peer {ip}:{port} [{e}]")
    except Exception as e:
        print(f"fail with {ip}:{port} [{e}]")
    finally:
        if writer:
            writer.close()
            await writer.wait_closed()
    return


def generate_peer_id():
    prefix = b'-PY0011-'

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
        for i in range(0, len(peers), 6):
            ip = socket.inet_ntoa(peers[i:i+4])
            port = struct.unpack('>H', peers[i+4:i+6])[0]
            peer_list.append((ip, port))
    return peer_list


import hashlib
import asyncio
from urllib.parse import urlencode

def encode_bytes_to_url(data: bytes) -> str:
    return "".join(f"%{byte:02X}" for byte in data)

async def main():
    data = extract_data("/Users/vkovalev/Downloads/ubuntu-24.04.5-desktop-arm64.iso.torrent")
    info = data[b'info']
    
    info_hash = hashlib.sha1(Encoder(info).encode()).digest()
    peer_id = generate_peer_id()

    info_hash_encoded = encode_bytes_to_url(info_hash)
    peer_id_encoded = encode_bytes_to_url(peer_id)

    total_length = info.get(b'length', sum(f[b'length'] for f in info.get(b'files', [])))
    
    query_data = {
        'port': 6881,
        'uploaded': 0,
        'downloaded': 0,
        'left': total_length,
        'compact': 1
    }
    
    base_announce = data[b'announce'].decode('utf-8')
    url = f"{base_announce}?info_hash={info_hash_encoded}&peer_id={peer_id_encoded}&{urlencode(query_data)}"
    
    print(f"Tracker URL: {url}")
    
    peers = await get_peers(url)
    print(f"\nПолучено пиров от трекера: {len(peers)}")

    handshake = Handshake(info_hash,peer_id)
    
    peers = [PeerConnection(ip,port)for ip, port in peers]

    result = await asyncio.gather(*[peer.interact(handshake) for peer in peers])

    print(result)

    successful = [r for r in result if r is not None]
    print(f"Успешных handshake: {len(successful)} из {len(peers)}")

if __name__ == "__main__":
    asyncio.run(main())