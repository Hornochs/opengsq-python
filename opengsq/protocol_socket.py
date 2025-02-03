import asyncio
import socket
from enum import Enum, auto
from opengsq.protocol_base import ProtocolBase

class SocketKind(Enum):
    SOCK_STREAM = auto()
    SOCK_DGRAM = auto()

class Socket():
    @staticmethod
    async def gethostbyname(hostname: str):
        return await asyncio.get_running_loop().run_in_executor(None, socket.gethostbyname, hostname)

    def __init__(self, kind: SocketKind):
        self.__timeout = None
        self.__transport = None
        self.__protocol = None
        self.__kind = kind

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def settimeout(self, value: float):
        self.__timeout = value

    async def connect(self, remote_addr):
        print(f"DEBUG Socket - connect() called")
        await asyncio.wait_for(self.__connect(remote_addr), timeout=self.__timeout)

    async def __connect(self, remote_addr):
        loop = asyncio.get_running_loop()
        self.__protocol = self.__Protocol(self.__timeout)

        if self.__kind == SocketKind.SOCK_STREAM:
            self.__transport, _ = await loop.create_connection(
                lambda: self.__protocol,
                host=remote_addr[0],
                port=remote_addr[1],
            )
        else:
            self.__transport, _ = await loop.create_datagram_endpoint(
                lambda: self.__protocol,
                remote_addr=remote_addr,
            )

    def close(self):
        if self.__transport:
            self.__transport.close()

    def send(self, data: bytes):
        if self.__kind == SocketKind.SOCK_STREAM:
            self.__transport.write(data)
        else:
            self.__transport.sendto(data)

    async def recv(self, size: int = None) -> bytes:
        if size:
            data = b""
            while len(data) < size:
                chunk = await self.__protocol.recv()
                data += chunk
                if len(data) >= size:
                    return data[:size]
        return await self.__protocol.recv()

    class __Protocol(asyncio.Protocol):
        def __init__(self, timeout: float):
            self.__packets = asyncio.Queue()
            self.__timeout = timeout

        async def recv(self):
            return await asyncio.wait_for(self.__packets.get(), timeout=self.__timeout)

        def connection_made(self, transport):
            pass

        def connection_lost(self, exc):
            pass

        # Streaming Protocols
        def data_received(self, data):
            """Called when some data is received. data is a non-empty bytes object containing the incoming data."""
            self.__packets.put_nowait(data)

        # Streaming Protocols
        def eof_received(self):
            """
            Called when the other end signals it won't send any more data
            (for example by calling transport.write_eof(), if the other end also uses asyncio).
            """
            pass

        # Datagram Protocols
        def datagram_received(self, data, addr):
            """Called when some datagram is received."""
            self.__packets.put_nowait(data)

        # Datagram Protocols
        def error_received(self, exc):
            """Called when a previous send or receive operation raises an OSError. exc is the OSError instance."""
            pass

class UdpClient(Socket):
    @staticmethod
    async def communicate(protocol: ProtocolBase, data: bytes):
        with UdpClient() as udpClient:
            udpClient.settimeout(protocol._timeout)
            await udpClient.connect((protocol._host, protocol._port))
            udpClient.send(data)
            return await udpClient.recv()

    def __init__(self):
        super().__init__(SocketKind.SOCK_DGRAM)

class BroadcastSocket(Socket):
    def __init__(self, source_port: int = None):
        super().__init__(SocketKind.SOCK_DGRAM)
        print(f"DEBUG 3 - BroadcastSocket init - Port passed: {source_port}")
        self.source_port = source_port
        print(f"DEBUG 3.5 - self.source_port: {self.source_port}")

    async def _connect(self, remote_addr):
        print(f"DEBUG 4 - Before socket bind - Using port: {self.bind_port}")
        print(f"DEBUG Socket - Using port: {self.source_port}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(('0.0.0.0', self.source_port if self.source_port else 0))
        print(f"DEBUG 5 - After socket bind - Actual port: {sock.getsockname()[1]}")
        self.__transport, _ = await loop.create_datagram_endpoint(
            lambda: self.__protocol,
            sock=sock
        )

class UdpBroadcastClient(BroadcastSocket):
    @staticmethod
    async def communicate(protocol: ProtocolBase, data: bytes):
        source_port = 14001 if protocol.__class__.__name__ in ['UDK', 'UT3'] else None
        print(f"DEBUG 2 - communicate() - Port before client creation: {source_port}")
        print(f"DEBUG Client - Setting port: {source_port}")
        with UdpBroadcastClient(source_port=source_port) as udpClient:
            udpClient.settimeout(protocol._timeout)
            await udpClient.connect((protocol._host, protocol._port))
            udpClient.send(data)
            return await udpClient.recv()

    def __init__(self, source_port: int = None):
        super().__init__(source_port)

class TcpClient(Socket):
    @staticmethod
    async def communicate(protocol: ProtocolBase, data: bytes):
        with TcpClient() as tcpClient:
            tcpClient.settimeout(protocol._timeout)
            await tcpClient.connect((protocol._host, protocol._port))
            tcpClient.send(data)
            return await tcpClient.recv()

    def __init__(self):
        super().__init__(SocketKind.SOCK_STREAM)


if __name__ == '__main__':
    async def test_socket_async():
        with Socket() as socket_async:
            socket_async.settimeout(5)
            await socket_async.connect(('122.128.109.245', 27015))
            socket_async.send(
                b'\xFF\xFF\xFF\xFFTSource Engine Query\x00\xFF\xFF\xFF\xFF')
            print(await socket_async.recv())

    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_socket_async())
    loop.close()