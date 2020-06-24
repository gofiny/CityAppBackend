create_table_user = '''CREATE TABLE IF NOT EXISTS "users"
                        (
                            "uuid" uuid NOT NULL PRIMARY KEY,
                            "gp_id" varchar(50) NOT NULL UNIQUE,
                            "username" varchar(30) NOT NULL UNIQUE,
                            "money" integer NOT NULL DEFAULT 100, 
                            "wood" integer NOT NULL DEFAULT 100,
                            "stones" integer NOT NULL DEFAULT 100
                        )'''

save_user_resources = '''UPDATE 
                            users 
                        SET 
                            money=%s,
                            wood=%s,
                            stones=%s,
                        WHERE 
                            uuid="%s"'''