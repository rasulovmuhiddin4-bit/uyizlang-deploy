import time
from functools import wraps

# Sodd caching sistemasi
cache_data = {}
CACHE_TIMEOUT = 300  # 5 daqiqa

def cache(ttl=CACHE_TIMEOUT):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Cache dan olish
            if key in cache_data:
                data, timestamp = cache_data[key]
                if time.time() - timestamp < ttl:
                    return data
            
            # Yangi ma'lumot olish
            result = func(*args, **kwargs)
            cache_data[key] = (result, time.time())
            return result
        return wrapper
    return decorator

# Cache ni tozalash funksiyasi
def clear_cache():
    cache_data.clear()