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
        self.packet_version = 1
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