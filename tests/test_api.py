import asyncio
import httpx
from app import app

def test_http_health_chat():
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url="http://test") as cli:
            health=await cli.get("/healthz")
            assert health.status_code==200 and health.json()["status"]=="ok"
            page=await cli.get("/")
            assert page.status_code==200 and "CareBridge" in page.text
            reply=await cli.post("/api/chat",json={"question":"What is a VIS?","mode":"hybrid"})
            assert reply.status_code==200
            assert "sources" in reply.json()
    asyncio.run(run())
