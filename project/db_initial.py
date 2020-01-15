import asyncpg
import asyncio


async def connect():
    conn = await asyncpg.connect(user="telegram", password="telpass123", database="global_chat", host="s162935.hostiman.com")
    return conn


async def create_table(conn, sql):
    await conn.execute(sql)
    print("table created")


players = '''CREATE TABLE IF NOT EXISTS "players"
(
    "id" SERIAL NOT NULL PRIMARY KEY,
    "username" varchar(25) NOT NULL UNIQUE,
    "vk_id" integer NOT NULL UNIQUE,
    "token" varchar(64) NOT NULL
);'''

game_objects = '''CREATE TABLE IF NOT EXISTS "game_objects"
(
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" varchar(20) NOT NULL,
    "health" integer NOT NULL,
    "object_type" varchar(7) NULL
);'''

static_objects = '''CREATE TABLE IF NOT EXISTS "static_objects"
(
    "game_object_ptr_id" integer NOT NULL PRIMARY KEY REFERENCES "game_objects" ("id") ON DELETE cascade
);'''

dynamic_objects = '''CREATE TABLE IF NOT EXISTS "dynamic_objects"
(
    "game_object_ptr_id" integer NOT NULL PRIMARY KEY REFERENCES "game_objects" ("id") ON DELETE cascade,
    "power" integer NOT NULL,
    "speed" integer NOT NULL
);'''

map_objects = '''CREATE TABLE IF NOT EXISTS "map_objects"
(
    "id" SERIAL NOT NULL PRIMARY KEY,
    "x" integer NOT NULL,
    "y" integer NOT NULL,
    "game_object_id" integer NOT NULL REFERENCES "game_objects" ("id") ON DELETE cascade,
    "owner_id" integer NULL REFERENCES "players" ("id") ON DELETE cascade
);'''

map_objects_game_object_index = '''CREATE INDEX "map_object_game_object_id_dbce3a33" ON "map_objects" ("game_object_id");'''
map_objects_owner_index = '''CREATE INDEX "map_object_owner_id_c79f0bf2" ON "map_objects" ("owner_id");'''


sqls = [players, game_objects, static_objects, dynamic_objects, map_objects, map_objects_game_object_index, map_objects_owner_index]


async def main():
    conn = await connect()
    for sql in sqls:
        await create_table(conn, sql)
    await conn.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
