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
