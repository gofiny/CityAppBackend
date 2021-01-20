'''Информация для подключения к базе данных'''


USER = ""
PASSWORD = ""
DATABASE = "game"
HOST = "localhost"
PORT = 5432

DESTINATION = f"postgres://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"
