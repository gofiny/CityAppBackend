import asyncpg
import asyncio
from time import time


DB_USER = "freelance"
DB_PASSWORD = "pass123"
DB_NAME = "free_db"
DB_HOST = "localhost"
DB_PORT = 5432

DESTINATION = f"postgres://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


async def get_pool():
    return await asyncpg.create_pool(dsn=DESTINATION)


async def delete_data(pool: asyncpg.pool.Pool):
    async with pool.acquire() as conn:
        await conn.execute("delete from test2")
        await conn.execute("delete from test1")


async def many_transaction_test(pool: asyncpg.pool.Pool, row_count: int):  # avg 1.4 sec
    async with pool.acquire() as conn:
        async with conn.transaction():
            now = time()
            for i in range(row_count):
                first = await conn.fetchval(f"insert into test1 (name, number) values ('{i}', {i}) returning number")
                second = await conn.fetchval(f"insert into test2 (name, n) values ('{first}', {first}) returning n")
                third = await conn.fetchrow(f"select * from test1 left join test2 ON test1.number=test2.n where test2.n={second}")
            print(f"many query with tr: {time() - now} sec. with {row_count} rows\n")


async def many_test(pool: asyncpg.pool.Pool, row_count: int):  # avg 3.7 sec
    async with pool.acquire() as conn:
        now = time()
        for i in range(row_count):
            first = await conn.fetchval(f"insert into test1 (name, number) values ('{i}', {i}) returning number")
            second = await conn.fetchval(f"insert into test2 (name, n) values ('{first}', {first}) returning n")
            third = await conn.fetchrow(f"select * from test1 left join test2 ON test1.number=test2.n where test2.n={second}")
        print(f"many query: {time() - now} sec. with {row_count} rows\n")


async def one_transaction_test(pool: asyncpg.pool.Pool, row_count: int):  # 0.8
    async with pool.acquire() as conn:
        async with conn.transaction():
            now = time()
            for i in range(row_count):
                third = await conn.fetchrow(
                    "WITH t1 as ("
                    f"insert into test1 (name, number) values ('{i}', {i}) returning name, number), t2 as ("
                    "insert into test2 (name, n) values ((select name from t1), (select number from t1)) returning n) "
                    "select * from test1 left join test2 ON test1.number=test2.n where test2.n=(select n from t2)"
                )
            print(f"one query tr: {time() - now} sec. with {row_count} rows\n")


async def one_test(pool: asyncpg.pool.Pool, row_count: int):  # 1.8
    async with pool.acquire() as conn:
        now = time()
        for i in range(row_count):
            third = await conn.fetchrow(
                "WITH t1 as ("
                f"insert into test1 (name, number) values ('{i}', {i}) returning name, number), t2 as ("
                "insert into test2 (name, n) values ((select name from t1), (select number from t1)) returning n) "
                "select * from test1 left join test2 ON test1.number=test2.n where test2.n=(select n from t2)"
            )
        print(f"one query: {time() - now} sec. with {row_count} rows\n")


tests = [
    many_test,
    many_transaction_test,
    one_test,
    one_transaction_test
]


async def main():
    pool = await get_pool()
    for test in tests:
        await test(pool, row_count=10000)
        await delete_data(pool)


if __name__ == "__main__":
    asyncio.run(main())
