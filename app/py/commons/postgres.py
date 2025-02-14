import asyncpg
from pgvector.asyncpg import register_vector

DATABASE_URL = "postgresql://myuser:mypassword@pg_anometras/mydb"

async def init_vector(conn):
    await register_vector(conn)

class Postgres:
    def __init__(self, database_url: str):
        self.database_url = database_url

    async def connect(self):
        self.pool = await asyncpg.create_pool(self.database_url,init=init_vector)

    async def disconnect(self):
        self.pool.close()

database = Postgres(DATABASE_URL)
