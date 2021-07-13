import urllib.request
import json
import time

papers_to_check = {
        'Linde attractors' : ('1503361',20),
        'Palti swampland' : ('1725205',380),
        }

for ptitle,(pid,seen) in papers_to_check.items():
    with urllib.request.urlopen(f'https://inspirehep.net/api/literature?sort=mostrecent&size=25&page=1&q=refersto%3Arecid%3A{pid}') as r:
        data = json.loads(r.read())
        total = data['hits']['total']
        missed = total-seen
        print(f"{ptitle}: {missed} new citations")
        if missed > 0:
            if missed > 25:
                missed = 25
                print("\tMore than 25 new citations, just printing most recent 25:")
            for i in range(missed):
                result = data['hits']['hits'][i]
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
        time.sleep(1)
