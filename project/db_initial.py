'''Инициализация таблиц в базе данных'''
import asyncio
import asyncpg


async def connect():
    '''Подключается к БД и возваращает объект соединения'''
    conn = await asyncpg.connect(
        user="telegram",
        password="telpass123",
        database="global_chat",
        host="s162935.hostiman.com"
    )
    return conn


async def create_table(conn, sql):
    '''Создает переданную таблицу'''
    await conn.execute(sql)
    print("table created")


PLAYERS = '''CREATE TABLE IF NOT EXISTS "players"
(
    "id" SERIAL NOT NULL PRIMARY KEY,
    "username" varchar(25) NOT NULL UNIQUE,
    "vk_id" integer NOT NULL UNIQUE,
    "token" varchar(64) NOT NULL
);'''

GAME_OBJECTS = '''CREATE TABLE IF NOT EXISTS "game_objects"
(
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" varchar(20) NOT NULL,
    "health" integer NOT NULL,
    "object_type" varchar(7) NULL
);'''

STATIC_OBJECTS = '''CREATE TABLE IF NOT EXISTS "static_objects"
(
    "game_object_ptr_id" integer NOT NULL PRIMARY KEY REFERENCES "game_objects" ("id") ON DELETE cascade
);'''

DYNAMIC_OBJECTS = '''CREATE TABLE IF NOT EXISTS "dynamic_objects"
(
    "game_object_ptr_id" integer NOT NULL PRIMARY KEY REFERENCES "game_objects" ("id") ON DELETE cascade,
    "power" integer NOT NULL,
    "speed" integer NOT NULL
);'''

MAP_OBJECTS = '''CREATE TABLE IF NOT EXISTS "map_objects"
(
    "id" SERIAL NOT NULL PRIMARY KEY,
    "x" integer NOT NULL,
    "y" integer NOT NULL,
    "game_object_id" integer NOT NULL REFERENCES "game_objects" ("id") ON DELETE cascade,
    "owner_id" integer NULL REFERENCES "players" ("id") ON DELETE cascade
);'''

MAP_OBJECTS_GAME_OBJECTS_INDEX = '''CREATE INDEX "map_object_game_object_id_dbce3a33" ON "map_objects" ("game_object_id");'''
MAP_OBJECTS_OWNER_INDEX = '''CREATE INDEX "map_object_owner_id_c79f0bf2" ON "map_objects" ("owner_id");'''


SQLS = [
    PLAYERS,
    GAME_OBJECTS,
    STATIC_OBJECTS,
    DYNAMIC_OBJECTS,
    MAP_OBJECTS,
    MAP_OBJECTS_GAME_OBJECTS_INDEX,
    MAP_OBJECTS_OWNER_INDEX
]


async def main():
    '''Основная корутина, для создания таблиц'''
    conn = await connect()
    for sql in SQLS:
        await create_table(conn, sql)
    await conn.close()


if __name__ == "__main__":
    LOOP = asyncio.get_event_loop()
    LOOP.run_until_complete(main())
