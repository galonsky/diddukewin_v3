import requests


class ScoreFetcher:
    URL = 'http://m.espn.com/ncb/clubhouse?teamId=150'

    def fetch(self) -> str:
        response = requests.get(self.URL, allow_redirects=False)
        return response.text
