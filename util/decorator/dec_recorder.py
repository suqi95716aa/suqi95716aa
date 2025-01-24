"""
进行log日志记录
"""

import os
import json
from functools import wraps
from datetime import datetime

access_log_path = os.path.join(
    os.path.dirname(__file__),
    "..",
    "log",
    "access",
    "access_"+datetime.now().strftime("%Y-%m-%d")+".log"
)


def log_recorder(f):
    @wraps(f)
    async def wrapped(request, *args, **kwargs):
        route_response = await f(request, *args, **kwargs)

        # Get useful information
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ip = request.headers.get('X-Real-IP') or request.headers.get('X-Forwarded-For') or request.remote_addr
        response_data = json.loads(route_response.body)

        if not os.path.exists(os.path.dirname(access_log_path)):
            os.makedirs(os.path.dirname(access_log_path))

        # log the record
        with open(access_log_path, "a", encoding="utf-8") as file:
            file.write(
                f"""
/*
Time: {time_str}
IP: {ip}
Request: {str(request.form)}
Response: {str(response_data)[:100]}
*/
                 """
                )

        return route_response
    return wrapped

