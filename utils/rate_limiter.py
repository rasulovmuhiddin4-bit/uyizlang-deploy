import time
from collections import defaultdict

# User based rate limiting
user_requests = defaultdict(list)
RATE_LIMIT = 10  # 10 so'rov daqiqasiga
TIME_WINDOW = 60  # 60 soniya

def rate_limit(user_id):
    now = time.time()
    user_requests[user_id] = [req_time for req_time in user_requests[user_id] 
                             if now - req_time < TIME_WINDOW]
    
    if len(user_requests[user_id]) >= RATE_LIMIT:
        return False
    
    user_requests[user_id].append(now)
    return True