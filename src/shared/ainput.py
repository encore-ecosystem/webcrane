import asyncio
import sys


async def ainput(string: str) -> str:
    await asyncio.to_thread(sys.stdout.write, f'{string} ')
    return await asyncio.to_thread(sys.stdin.readline)

__all__ = [
    'ainput'
]
