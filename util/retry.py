import time
import functools


def a_retry(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # print(f"a_retry calling {func.__name__}")
        attempts = 0
        max_attempts = 3
        delay = 1

        while attempts < max_attempts:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                attempts += 1
                print(f"Attempt {attempts} of {max_attempts} failed for function {func.__name__} with error: {e}")
                time.sleep(delay)

        return False
    return wrapper


def retry(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # print(f"retry calling {func.__name__}")
        attempts = 0
        max_attempts = 3
        delay = 1

        while attempts < max_attempts:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                attempts += 1
                print(f"Attempt {attempts} of {max_attempts} failed for function {func.__name__} with error: {e}")
                time.sleep(delay)

        return False
    return wrapper