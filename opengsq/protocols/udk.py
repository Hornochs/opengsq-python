from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import UdpClient
from opengsq.responses.udk.status import Status, PlatformType
from opengsq.binary_reader import BinaryReader
import struct
import os

class UDK(ProtocolBase):
    full_name = "UnrealEngine3/UDK Protocol"
    LAN_BEACON_PACKET_HEADER_SIZE = 16
    UDK_PORT = 14001
    
    def __init__(self, host: str, port: int = UDK_PORT, timeout: float = 5.0):
        if port != self.UDK_PORT:
            raise ValueError(f"UDK protocol requires port {self.UDK_PORT}")
        super().__init__(host, self.UDK_PORT, timeout)
        self._allow_broadcast = True
        self.packet_version = 5 
        self.game_id = 0x00000000
        self.platform = PlatformType.Windows
        self.client_nonce = os.urandom(8)
        self.packet_types_query = (b'S', b'Q')
        self.packet_types_response = (b'S', b'R')

    async def get_status(self) -> Status:
        packet = self._build_query_packet()
        data = await UdpClient.communicate(self, packet, source_port=self.UDK_PORT)
        if not self._is_valid_response(data):
            raise Exception("Invalid response")
        parsed_data = self._parse_response(data)
        return Status(**parsed_data)
    
    def _build_query_packet(self) -> bytes:
        packet = bytearray(self.LAN_BEACON_PACKET_HEADER_SIZE)
        struct.pack_into("!BB", packet, 0, self.packet_version, self.platform)
        struct.pack_into("!I", packet, 2, self.game_id)
        packet[6:7] = self.packet_types_query[0]
        packet[7:8] = self.packet_types_query[1]
        packet[8:16] = self.client_nonce
        return bytes(packet)

    def _is_valid_response(self, buffer: bytes) -> bool:
        if len(buffer) <= self.LAN_BEACON_PACKET_HEADER_SIZE:
            return False
            
        version = buffer[0]
        platform = buffer[1]
        game_id = struct.unpack("!I", buffer[2:6])[0]
        response_type = (buffer[6:7], buffer[7:8])
        response_nonce = buffer[8:16]
        
        return (version == self.packet_version and
                platform == self.platform and
                game_id == self.game_id and
                response_type == self.packet_types_response and
                response_nonce == self.client_nonce)

    def _parse_response(self, buffer: bytes) -> dict:
        br = BinaryReader(buffer[self.LAN_BEACON_PACKET_HEADER_SIZE:])
        
        raw = {}
        raw['name'] = br.read_string()
        raw['map'] = br.read_string()
        raw['game_type'] = br.read_string()
        raw['num_players'] = br.read_int32()
        raw['max_players'] = br.read_int32()
        raw['password_protected'] = br.read_boolean()
        raw['stats_enabled'] = br.read_boolean()
        raw['lan_mode'] = br.read_boolean()
        
        players = []
        while br.remaining() > 0:
            player_name = br.read_string()
            if not player_name:
                break
            players.append(Player(
                name=player_name,
                score=br.read_int32(),
                ping=br.read_int32(),
                team=br.read_int32()
            ))
        
        raw['players'] = players
        
        return {
            'name': raw['name'],
            'map': raw['map'],
            'game_type': raw['game_type'],
            'num_players': raw['num_players'],
            'max_players': raw['max_players'],
            'password_protected': raw['password_protected'],
            'stats_enabled': raw['stats_enabled'],
            'lan_mode': raw['lan_mode'],
            'players': players,
            'raw': raw
        }