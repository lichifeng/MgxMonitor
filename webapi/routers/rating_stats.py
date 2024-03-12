'''Get rating statistics of different versions'''

from datetime import datetime

from mgxhub.db.operation import get_rating_stats
from webapi import app


@app.get("/rating/stats")
async def get_rating_meta() -> dict:
    '''Get rating statistics of different versions.

    Used in ratings page to show the number of ratings for each version.

    Defined in: `mgxhub/handler/db_handler.py`
    '''

    stats = get_rating_stats()
    current_time = datetime.now().isoformat()

    return {'stats': stats, 'generated_at': current_time}
