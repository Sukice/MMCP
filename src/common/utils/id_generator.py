import random
import string
from src.common.utils import datetime_to_str,get_current_datetime

def generate_unique_id():
    now = get_current_datetime()
    time_str = datetime_to_str(now)  # 年月日时分秒，如 20251214153020
    microsecond = f"{now.microsecond:06d}"  # 微秒（补6位，避免位数不足），如 123456
    time_part = f"{time_str}{microsecond}"  # 拼接后：20251214153020123456
    random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    unique_id = f"{time_part}_{random_part}"
    return unique_id

def generate_task_id():
    return "task_"+generate_unique_id()

def generate_call_id():
    return "call_"+generate_unique_id()
