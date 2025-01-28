from opengsq.protocol_base import ProtocolBase
from opengsq.protocol_socket import UdpBroadcastClient
from opengsq.responses.udk.status import Status, PlatformType
from opengsq.binary_reader import BinaryReader
import struct
import os

class UDK(ProtocolBase):
    full_name = "UnrealEngine3/UDK Protocol"
    LAN_BEACON_PACKET_HEADER_SIZE = 16
    
    def __init__(self, host: str, port: int = 14001, timeout: float = 5.0):
        super().__init__(host, port, timeout)
        self.packet_version = 1
        self.game_id = 0x00000000
        self.platform = PlatformType.Windows
        self.client_nonce = os.urandom(8)
        # Packet identifiers matching JS implementation
        self.packet_types_query = (b'S', b'Q')
        self.packet_types_response = (b'S', b'R')

    async def get_status(self) -> Status:
        packet = self._build_query_packet()
        data = await UdpBroadcastClient.communicate(self, packet)
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
        # Implement parsing logic here
        pass
