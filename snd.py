
from jsonrpcclient import request_json, parse_json, Ok
import asyncio


async def tcp_echo_client(message):
    reader, writer = await asyncio.open_connection(
        '127.0.0.1', 3326)

    print(f'Send: {message!r}')
    writer.write(f"{request_json(message)}\n".encode())
    await writer.drain()

    data = await reader.read(100)
    print(f'Received: {data.decode()!r}')

    print('Close the connection')
    writer.close()
    await writer.wait_closed()

asyncio.run(tcp_echo_client('hashrate'))