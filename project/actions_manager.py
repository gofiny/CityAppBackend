import asyncio
import asyncpg
from asyncpg.connection import Connection
import config


async def connect():
    '''Подключается к БД и возваращает объект соединения'''
    conn = await asyncpg.connect(
        user=config.USER,
        password=config.PASSWORD,
        database=config.DATABASE,
        host=config.HOST
    )
    return conn


async def create_actions(conn: Connection):
    pass