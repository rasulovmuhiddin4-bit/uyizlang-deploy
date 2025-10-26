import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def monitor_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        logger.info(f"{func.__name__} executed in {execution_time:.2f} seconds")
        
        if execution_time > 5:  # 5 soniyadan ko'p bo'lsa ogohlantirish
            logger.warning(f"SLOW PERFORMANCE: {func.__name__} took {execution_time:.2f}s")
            
        return result
    return wrapper