create_table_user = '''CREATE TABLE IF NOT EXISTS "users"
                        (
                            "uuid" uuid NOT NULL PRIMARY KEY,
                            "gp_id" varchar(50) NOT NULL UNIQUE,
                            "username" varchar(30) NOT NULL UNIQUE,
                            "reg_time" integer NOT NULL,
                            "money" integer NOT NULL DEFAULT 100, 
                            "wood" integer NOT NULL DEFAULT 100,
                            "stones" integer NOT NULL DEFAULT 100
                        )'''

create_table_game_objects = '''CREATE TABLE IF NOT EXISTS "game_objects"
                        (
                            "uuid" uuid NOT NULL PRIMARY KEY,
                            "name" varchar(25) NOT NULL,
                            "object_type" varchar(25) NOT NULL,
                            "level" integer NOT NULL DEFAULT 1,
                            "health" integer,
                            "speed" float,
                            "power" integer,
                            "max_tasks" integer    
                        )'''

create_table_map_objects = '''CREATE TABLE IF NOT EXISTS "map_objects"
                            (
                                "uuid" uuid NOT NULL PRIMARY KEY,
                                "pos" point,
                                "game_object" uuid NOT NULL REFERENCES "game_objects" ("uuid") on delete cascade, 
                                "owner" uuid null REFERENCES "users" ("uuid"),
                                "is_free" bool default true
                            )'''

save_user_resources = "UPDATE users SET money=%s, wood=%s, stones=%s, WHERE uuid='%s'"

check_reg_user = "SELECT gp_id, username FROM users where gp_id='%s' OR username='%s'"

get_user = "SELECT * FROM users WHERE gp_id='%s'"

create_new_user = """INSERT INTO users
                    (
                        uuid,
                        gp_id,
                        username,
                        reg_time
                    )
                    VALUES ('%s', '%s', '%s', %s) returning *"""

create_game_object = """INSERT INTO game_objects
                        (
                            uuid,
                            name,
                            object_type,
                            level,
                            health,
                            speed,
                            power,
                            max_tasks
                        )
                        VALUES ('%s', '%s', '%s', %s, %s, %s, %s, %s)
                        returning *"""

create_start_user = """WITH user as (
                        """

get_random_object_pos = """SELECT pos 
                            FROM map_objects 
                                OFFSET RANDOM() * (SELECT COUNT(*) FROM map_objects)
                            LIMIT %s"""