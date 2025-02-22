import asyncpg
from pgvector.asyncpg import register_vector
import os

db_host = os.environ.get('ANNOT_POSTGRES_HOST')
db_username = os.environ.get('ANNOT_POSTGRES_USER')
db_password = os.environ.get('ANNOT_POSTGRES_PASSWORD')
database = os.environ.get('ANNOT_POSTGRES_DB')

async def init_vector(conn):
    await register_vector(conn)

class Postgres:
    def __init__(self, db_host:str, username:str, password:str, database:str ): 
        #database_url: str):
        # self.database_url = database_url
        self.host = db_host
        self.username = username
        self.password = password
        self.database = database

    async def connect(self):
        self.pool = await asyncpg.create_pool( host=self.host,
                                               user=self.username,
                                               password=self.password,
                                               database=self.database,
                                               init=init_vector)

    async def disconnect(self):
        await self.pool.close()


if db_host == None and  db_username == None and  db_password == None and database == None:
  raise Exception("enviroment variables are not set") 



database = Postgres(db_host, db_username, db_password, database)
