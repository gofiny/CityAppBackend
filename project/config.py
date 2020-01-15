'''Информация для подключения к базе данных'''


USER = "telegram"
PASSWORD = "telpass123"
DATABASE = "global_chat"
HOST = "s162935.hostiman.com"
PORT = 5432

DESTINATION = f"postgres://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"
