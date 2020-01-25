'''Информация для подключения к базе данных'''


USER = "dmitry"
PASSWORD = "6PEMGE2x"
DATABASE = "game"
HOST = "localhost"
PORT = 5432

DESTINATION = f"postgres://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"
