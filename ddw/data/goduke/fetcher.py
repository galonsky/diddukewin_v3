import requests


class GoDukeFetcher:
    def fetch_schedule(self) -> str:
        headers = {
            "User-Agent": "diddukewin/1.0",
        }
        return requests.get(
            "https://goduke.com/services/schedule_txt.ashx?schedule=814",
            headers=headers,
        ).text
