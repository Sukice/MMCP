from datetime import datetime

def get_current_datetime() -> datetime:
    return datetime.now()

def datetime_to_str(dt: datetime) -> str:
    return dt.strftime("%Y%m%d%H%M%S")