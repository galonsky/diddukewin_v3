import requests

class ScoreFetcher:
    # URL = 'http://m.espn.com/ncb/clubhouse?teamId=150'
    URL = 'http://m.espn.com/mlb/clubhouse?teamId=16'

    def fetch(self):
        response = requests.get(self.URL, allow_redirects=False)
        with open('cubs.html', 'a') as file:
            file.write(response.text)

fetcher = ScoreFetcher()
fetcher.fetch()