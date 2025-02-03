from opengsq.protocols.udk import UDK
from opengsq.responses.ut3.status import Status

class UT3(UDK):
    full_name = "Unreal Tournament 3 Protocol"
    
    def __init__(self, host: str, port: int = 14001, timeout: float = 5.0):
        super().__init__(host, port, timeout)
        self.game_id = 0x58D4B65A  # UT3 specific game ID