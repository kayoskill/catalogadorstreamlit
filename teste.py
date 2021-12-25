from datetime import date, datetime
import time
print(time.time())

t = f'{datetime.now().date()} {datetime.now().time()}'

print(datetime.fromisoformat(t))
