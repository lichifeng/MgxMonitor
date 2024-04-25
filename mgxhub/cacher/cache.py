'''Cache assistant'''

import json

from sqlalchemy.orm import Session

from mgxhub.model.orm import Cache


class Cacher:
    '''Cache assistant'''

    def __init__(self, db: Session):
        self.db = db

    def get(self, k: str) -> str | None:
        '''Get value from cache'''

        result = self.db.query(Cache.value).filter(Cache.key == k).first()
        if result:
            return result[0]
        return None

    def set(self, k: str, v: str | dict) -> None:
        '''Set value to cache'''

        # If v is a dict, serialize it to a JSON string
        serialized_v = json.dumps(v) if isinstance(v, dict) else v

        cache = self.db.query(Cache).filter(Cache.key == k).first()
        if cache:
            cache.value = serialized_v
        else:
            cache = Cache(key=k, value=serialized_v)
            self.db.add(cache)
        self.db.commit()

    def purge(self) -> None:
        '''Purge all cache'''

        self.db.query(Cache).delete()
        self.db.commit()
