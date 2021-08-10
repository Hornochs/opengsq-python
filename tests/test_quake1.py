import opengsq
import pytest


test = opengsq.Quake1(address='35.185.44.174', query_port=27500)

@pytest.mark.asyncio
async def test_get_status():
    response = await test.get_status()
    print(response)