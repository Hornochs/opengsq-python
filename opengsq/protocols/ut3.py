from opengsq.protocols.udk import UDK
from opengsq.responses.ut3.status import Status

class UT3(UDK):
    full_name = "Unreal Tournament 3 Protocol"
    
    def __init__(self, host: str, port: int = 14001, timeout: float = 5.0):
        super().__init__(host, port, timeout)
        self.game_id = 0x4D5707DB

    def _parse_response(self, buffer: bytes) -> dict:
        base_response = super()._parse_response(buffer)
        
        # Process UT3 specific properties
        ut3_properties = {}
        for prop in base_response['raw']['settings_properties']:
            prop_id = prop['id']
            if prop_id == 1073741825:  # Map
                base_response['map'] = prop['data']
                ut3_properties['map'] = prop['data']
            elif prop_id == 1073741826:  # Game Type
                base_response['game_type'] = prop['data']
                ut3_properties['gametype'] = prop['data']
            elif prop_id == 1073741828:  # Custom Mutators
                ut3_properties['custom_mutators'] = self._split_mutators(prop['data'])
            elif prop_id == 268435704:  # Frag Limit
                ut3_properties['frag_limit'] = prop['data']
            elif prop_id == 268435705:  # Time Limit
                ut3_properties['time_limit'] = prop['data']
            elif prop_id == 268435703:  # Number of Bots
                ut3_properties['numbots'] = prop['data']
            elif prop_id == 268435717 or prop_id == 1073741829:  # Stock Mutators
                ut3_properties['stock_mutators'] = self._split_mutators(prop['data'])

        # Process localized settings
        for setting in base_response['raw']['localized_settings']:
            setting_id = setting['id']
            if setting_id == 32779:
                ut3_properties['gamemode'] = setting['value_index']
            elif setting_id == 0:
                ut3_properties['bot_skill'] = setting['value_index']
            elif setting_id == 6:
                ut3_properties['pure_server'] = setting['value_index']
            elif setting_id == 7:
                base_response['password_protected'] = setting['value_index'] == 1
                ut3_properties['password'] = setting['value_index']

        base_response['raw'].update(ut3_properties)
        return base_response

    def _split_mutators(self, mutators_str) -> list:
        if not mutators_str or isinstance(mutators_str, int):
            return []
        return [m for m in mutators_str.split('\x1c') if m]