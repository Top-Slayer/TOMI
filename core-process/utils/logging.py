from datetime import datetime
from zoneinfo import ZoneInfo
import time

def log_concat(*args) -> str:
    tz = ZoneInfo("Asia/Vientiane")
    ns = time.time_ns()
    dt = datetime.fromtimestamp(ns / 1e9, tz)
    message = " ".join(map(str, args))

    return f"[{dt.strftime('%Y-%m-%d %H:%M:%S')}.{f'{ns % 1_000_000_000:09d}'}] [CORE]: {message}"