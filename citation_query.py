import urllib.request
import json
import time
from datetime import datetime
import os

queries_to_make = {
        # papers
        'Linde attractors' : '1503361',
        'Freivogel et al' : '1478826',
        'MMPW' : '1242556',
        'Dias, Frazer, Marsh' : '1449883',
        'Masoumi et al random potentials' : '1503151',
        'DBM paper' : '1683333',
        'Swampland' : '1679222',
        'High slope potentials' : '1735860',
        'Achucarro+ non-Gauss' : '1750069',
        'Manyfield inflation prior dependence' : '1744453',
        'Palma BH' : '1790956',
        'Rapid-turn solutions' : '1827326',
        'Palti swampland review' : '1725205',
        # people
        'Ana Achucarro' : 'A.Achucarro.1',
        'Yvette Welling' : 'Y.Welling.1',
        'Oliver Janssen' : 'O.Janssen.1',
        'Diederik Roest' : 'D.Roest.1',
        'Perseas Christodoulidis' : 'P.Christodoulidis.1',
        'Katie Freese' : 'K.Freese.1',
        'Matt Kleban' : 'M.Kleban.1',
        'Liam McAllister' : 'L.McAllister.1',
        'Alex Westphal' : 'A.Westphal.1',
        'Cumrun Vafa' : 'C.Vafa.1',
        'Luis Ibáñez' : 'L.E.Ibanez.1',
        'Jacques Distler' : 'J.Distler.1',
        'Sonia Paban' : 'S.Paban.1',
        'Gonzalo Palma' : 'G.A.Palma.1',
        'Evangelos' : 'E.I.Sfakianakis.1',
        'David Kaiser' : 'D.I.Kaiser.1',
        'Thomas Hertog' : 'T.Hertog.1',
        'Sebastien Renaux-Petel' : 'S.Renaux.Petel.1',
        'Claudia de Rham' : 'C.de.Rham.1',
        'Kristof Turzynski' : 'K.Turzynski.1',
        'Spyros Sypsas' : 'S.Sypsas.1',
        'Fumagalli' : 'J.Fumagalli.1',
        'David Wands' : 'D.Wands.1',
        'Mateo Fasiello' : 'M.Fasiello.1',
        'Tyson Littenberg1' : 'T.B.Littenberg.1',
        'Tyson Littenberg2' : 'T.B.Littenberg.2',
        'David Andriot' : 'D.Andriot.1',
        }
lastrun = datetime(2021,6,28)

def process_json_date(datestr):
    try:
        return datetime.strptime(datestr, "%Y-%m-%d")
    except:
        return datetime.strptime(datestr, "%Y-%m")
def output_info(ptitle,result):
    outputstr = ""
    title = result['titles'][0]['title']
    hasarxiv = False
    if 'arxiv_eprints' in result.keys():
        hasarxiv = True
        arxivno = result['arxiv_eprints'][0]['value']
        arxivcat = result['primary_arxiv_category'][0]
    controlno = result['control_number']
    authcount = result['author_count']
    authors = result['authors']
    outputstr += f"{title}\n"
    print('\t',title)
    if authcount < 5:
        authlist = f'{"; ".join(auth["first_name"]+" "+auth["last_name"] for auth in authors)}'
    else:
        authlist = f'{authors[0]["full_name"]} et al'
    outputstr += f"{authlist}\n"
    print(f'\t\t {authlist}')
    if hasarxiv:
        outputstr += f"https://arxiv.org/abs/{arxivno}\n"
        print(f'\t\t https://arxiv.org/abs/{arxivno}')
    outputstr += f"https://inspirehep.net/literature/{controlno}\n"
    print(f'\t\t https://inspirehep.net/literature/{controlno}')
    print('')
    os.system(f'notify-send "New citation for {ptitle}" "{outputstr}"')

for ptitle,pid in queries_to_make.items():
    if pid[1] == '.':
        url = f'https://inspirehep.net/api/literature?sort=mostrecent&size=25&page=1&q=exactauthor%3A{pid}'
    else:
        url = f'https://inspirehep.net/api/literature?sort=mostrecent&size=25&page=1&q=refersto%3Arecid%3A{pid}'
    with urllib.request.urlopen(url) as r:
        data = json.loads(r.read())
        latest_update = process_json_date(data['hits']['hits'][0]['metadata']['earliest_date'])
        if lastrun < latest_update:
            print(f"{ptitle}: new results")
            for i in range(25):
                result = data['hits']['hits'][i]['metadata']
                latest_update = process_json_date(result['earliest_date'])
                if latest_update > lastrun:
                    output_info(ptitle,result)
                else:
                    break
        time.sleep(1)
