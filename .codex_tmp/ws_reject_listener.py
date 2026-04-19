import asyncio
import json
import time
import websockets

TASK_ID = 'a3bb641f-402e-4161-a82e-4e3925cd9650'
APPROVAL_ID = '307a136f-91f8-4e45-8bef-9cfc088b1ca8'
WS_URL = 'ws://127.0.0.1:8001/ws/live_reject_probe'
TIMEOUT_SECONDS = 300

async def main():
    start = time.time()
    async with websockets.connect(WS_URL) as ws:
        while time.time() - start < TIMEOUT_SECONDS:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
            except asyncio.TimeoutError:
                continue
            try:
                payload = json.loads(msg)
            except Exception:
                continue
            is_match = (
                payload.get('task_id') == TASK_ID
                or payload.get('approval_id') == APPROVAL_ID
            )
            if is_match:
                print(json.dumps(payload, ensure_ascii=False), flush=True)

asyncio.run(main())
