'''Инициализация таблиц в базе данных'''
import asyncio
import asyncpg
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


async def create_table(conn, sql):
    '''Создает переданную таблицу'''
    await conn.execute(sql)
    print("table created")


PLAYERS = '''CREATE TABLE IF NOT EXISTS "players"
(
    "uuid" uuid NOT NULL PRIMARY KEY,
    "username" varchar(25) NOT NULL UNIQUE,
    "user_id" varchar(50) NOT NULL UNIQUE,
    "token" varchar(64) NOT NULL,
    "metadata" varchar(30)
);'''

GAME_OBJECTS = '''CREATE TABLE IF NOT EXISTS "game_objects"
(
    "uuid" uuid NOT NULL PRIMARY KEY,
    "name" varchar(25) NOT NULL,
    "health" integer NOT NULL,
    "object_type" varchar(15) NULL
);'''

STATIC_OBJECTS = '''CREATE TABLE IF NOT EXISTS "static_objects"
(
    "game_object_ptr" uuid NOT NULL PRIMARY KEY REFERENCES "game_objects" ("uuid") ON DELETE cascade
);'''

GENERATED_OBJECTS = '''CREATE TABLE IF NOT EXISTS "generated_objects"
(
    "game_object_ptr" uuid NOT NULL PRIMARY KEY REFERENCES "game_objects" ("uuid") ON DELETE cascade
);'''

PawnObjects = '''CREATE TABLE IF NOT EXISTS "pawn_objects"
(
    "game_object_ptr" uuid NOT NULL PRIMARY KEY REFERENCES "game_objects" ("uuid") ON DELETE cascade,
    "max_actions" integer NOT NULL,
    "speed" float NOT NULL DEFAULT 0.33,
    "power" integer NOT NULL DEFAULT 10
)'''

MAP_OBJECTS = '''CREATE TABLE IF NOT EXISTS "map_objects"
(
    "uuid" uuid NOT NULL PRIMARY KEY,
    "x" integer NOT NULL,
    "y" integer NOT NULL,
    "game_object" uuid NOT NULL REFERENCES "game_objects" ("uuid") ON DELETE cascade,
    "owner" uuid NULL REFERENCES "players" ("uuid") ON DELETE cascade
);'''

PlayerResources = '''CREATE TABLE IF NOT EXISTS "players_resources"
(
    "uuid" uuid NOT NULL PRIMARY KEY,
    "player" uuid NOT NULL REFERENCES "players" ("uuid") ON DELETE cascade,
    "money" integer NOT NULL,
    "wood" integer NOT NULL,
    "stones" integer NOT NULL
);'''

Actions = '''CREATE TABLE IF NOT EXISTS "actions"
(
    "uuid" uuid NOT NULL PRIMARY KEY,
    "name" varchar(20)
);'''

AvailableActions = '''CREATE TABLE IF NOT EXISTS "available_actions"
(
    "uuid" uuid NOT NULL PRIMARY KEY,
    "action" uuid NOT NULL REFERENCES "actions" ("uuid"),
    "pawn" uuid NOT NULL REFERENCES "game_objects" ("uuid")
);'''

PawnActions = '''CREATE TABLE IF NOT EXISTS "pawn_actions"
(
    "uuid" uuid NOT NULL PRIMARY KEY,
    "pawn" uuid NOT NULL REFERENCES "game_objects" ("uuid") ON DELETE cascade,
    "action" uuid NOT NULL REFERENCES "actions" ("uuid"),
    "start_time" float,
    "end_time" float
);'''


SQLS = [
    PLAYERS,
    GAME_OBJECTS,
    STATIC_OBJECTS,
    GENERATED_OBJECTS,
    MAP_OBJECTS,
    PawnObjects,
    PlayerResources,
    Actions,
    AvailableActions,
    PawnActions
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
