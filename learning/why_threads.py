import time
from concurrent.futures import ThreadPoolExecutor


def slow_lookup(city):
    time.sleep(1)              # pretend: waiting for a website to answer
    return f"got {city}"


cities = ["Paris", "New York", "Bengaluru"]

start = time.time()
[slow_lookup(c) for c in cities]
print(f"one after another: {time.time() - start:.1f}s")

start = time.time()
with ThreadPoolExecutor() as pool:
    list(pool.map(slow_lookup, cities))
print(f"all at once:       {time.time() - start:.1f}s")