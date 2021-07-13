import urllib.request
import json
import time
from datetime import datetime

queries_to_make = {
        'Linde attractors' : '1503361',
        'Palti swampland' : '1725205',
        'Ana Achucarro' : 'authors/1018994',
        }
lastrun = datetime(2021,6,28)

def process_json_date(datestr):
    try:
        return datetime.strptime(datestr, "%Y-%m-%d")
    except:
        return datetime.strptime(datestr, "%Y-%m")

for ptitle,pid in queries_to_make.items():
    if '/' in pid:
        url = f'https://inspirehep.net/api/{pid}'
    else:
        url = f'https://inspirehep.net/api/literature?sort=mostrecent&size=25&page=1&q=refersto%3Arecid%3A{pid}'
    with urllib.request.urlopen(url) as r:
        data = json.loads(r.read())
        latest_update = process_json_date(data['hits']['hits'][0]['metadata']['earliest_date'])
        if lastrun < latest_update:
            print(f"{ptitle}: new results")
            for i in range(25):
                result = data['hits']['hits'][i]
                latest_update = process_json_date(result['metadata']['earliest_date'])
                if latest_update > lastrun:
                    title = result['metadata']['titles'][0]['title']
                    hasarxiv = False
                    if 'arxiv_eprints' in result['metadata'].keys():
                        hasarxiv = True
                        arxivno = result['metadata']['arxiv_eprints'][0]['value']
                        arxivcat = result['metadata']['primary_arxiv_category'][0]
                    authcount = result['metadata']['author_count']
                    authors = result['metadata']['authors']
                    print('\t',title)
                    if authcount < 5:
                        print(f'\t\t {"; ".join(auth["first_name"]+" "+auth["last_name"] for auth in authors)}')
                    else:
                        print(f'\t\t {authors[0]["full_name"]} et al')
                    if hasarxiv:
                        print(f'\t\t https://arxiv.org/abs/{arxivno}')
                    print('')
                else:
                    break
        time.sleep(1)
