import redis.asyncio as redis
import os

ANNOT_MQ_HOST=os.environ.get('ANNOT_MQ_HOST')
REDIS_PORT = 6379#os.environ.get('REDIS_PORT')

INPUT_CHANNEL_NAME='raw_input'


class RedisPool:
    def __init__(self, host:str ): 
        #database_url: str):
        # self.database_url = database_url
        self.host = host
        

    async def connect(self):
        self.pool = redis.ConnectionPool(host=self.host)
        return self.pool

    async def client(self):
        return redis.Redis.from_pool(self.pool)
        # return await redis.from_url(f'redis://{self.host}:{REDIS_PORT}')

    async def disconnect(self):
        self.pool.aclose()


if ANNOT_MQ_HOST == None:
  raise Exception("enviroment variables are not set") 



broker = RedisPool(ANNOT_MQ_HOST)
