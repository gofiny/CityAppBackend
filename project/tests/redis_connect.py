import asyncio
import aioredis


class Redis:
    def __init__(self):
        self.test = True

    async def init_databases(self):
        self.redis_pool = await aioredis.create_pool(address="redis://localhost", db=0)

    async def get_redis_connection(self) -> aioredis.RedisConnection:
        conn = await self.redis_pool.get_connection()[0]
        if conn:
            return conn
        return await self.redis_pool.acquire()

    async def get_conn(self):
        return await self.redis_pool.acquire()

    
async def main_test():
    redis = Redis()
    await redis.init_databases()
    conn = await redis.get_conn()
    print(type(conn))

if __name__ == "__main__":
    asyncio.run(main_test())
