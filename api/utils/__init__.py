from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_caching import Cache
from flask_limiter.util import get_remote_address

limiter = Limiter(
    get_remote_address,
    storage_uri= 'memory://'
)

cache = Cache()





db = SQLAlchemy()

