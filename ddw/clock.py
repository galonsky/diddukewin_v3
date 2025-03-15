from datetime import datetime
from zoneinfo import ZoneInfo


class Clock:
    def now(self) -> datetime:
        return datetime.now(ZoneInfo("America/New_York"))
