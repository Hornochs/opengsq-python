import pytest
from opengsq.protocols.ut3 import UT3
from ..result_handler import ResultHandler

handler = ResultHandler(__file__)

@pytest.mark.asyncio
async def test_ut3_status():
    ut3 = UT3(host="10.13.37.4", port=14001)
    result = await ut3.get_status()
    await handler.save_result("test_ut3_status", result)

@pytest.mark.asyncio
async def test_ue3_status():
    ue3 = UT3(host="10.13.37.4", port=14001)
    result = await ue3.get_status()
    await handler.save_result("test_ue3_status", result)