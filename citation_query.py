import urllib.request
import json
import time
from datetime import datetime, timedelta, timezone
import os
from sys import platform
import subprocess
import webbrowser

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
        'GWTA' : '1877713',
        'Rapid turn sugra': '1942221',
        'SGWBinner release': '1740929',
        # people
        'Ana Achucarro' : 'A.Achucarro.1',
        'Quentin Baghi' : 'Q.Baghi.1',
        'John Baker' : 'J.G.Baker.1',
        'Ira Thorpe' : 'J.I.Thorpe.1',
        'Jacob Slutsky1' : 'J.Slutsky.1',
        'Jacob Slutsky2' : 'J.Slutsky.2',
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
        'Sébastien Renaux-Petel' : 'S.Renaux.Petel.1',
        'Claudia de Rham' : 'C.de.Rham.1',
        'Kristof Turzynski' : 'K.Turzynski.1',
        'Spyros Sypsas' : 'S.Sypsas.1',
        'David Wands' : 'D.Wands.1',
        'Mateo Fasiello' : 'M.Fasiello.1',
        'Tyson Littenberg1' : 'T.B.Littenberg.1',
        'Tyson Littenberg2' : 'T.B.Littenberg.2',
        'David Andriot' : 'D.Andriot.1',
        'Mateo Braglia': 'M.Braglia.1',
        'Vikas Aragam': 'V.Aragam.1',
        'Joseph Romano': 'J.D.Romano.1',
        'Neil Cornish': 'N.J.Cornish.1',
        'Matt Digman': 'M.C.Digman.1',
        'Nikos Karnesis': "N.Karnesis.3",
        'Jacopo Fumagalli': 'J.Fumagalli.1',
        'Lucas Witowski': 'L.T.Witkowski.1',
        'M.C. David Marsh': 'M.C.D.Marsh.2',
        'Daniel Green': 'Daniel.R.Green.1',
        'Daniel Baumann': 'Daniel.Baumann.1',
        'Mauro Pieroni': 'M.Pieroni.1',
        'Richard Easther': 'R.Easther.1',
        'Martina Muratore': 'M.Muratore.1',
        'Marc Lilley': 'M.Lilley.1',
        'Jean-Baptiste Bayle': 'J.B.Bayle.1',
        'Nikolaos Karnesis': 'N.Karnesis.3',
        'Olaf Hartwig': 'O.Hartwig.1',
        'Antoine Petiteau': 'A.Petiteau.1',
        }

def process_json_date(datestr):
    try:
        return datetime.strptime(datestr, "%Y-%m-%d").astimezone(timezone.utc)
    except:
        try:
            return datetime.strptime(datestr, "%Y-%m").astimezone(timezone.utc)
        except:
            return datetime.strptime(datestr, "%Y").astimezone(timezone.utc)
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
    outputstr += f"https://inspirehep.net/literature/{controlno}\n"
    outputstr += f"{title}\n"
    print('\t',title)
    if authcount < 5:
        auths = []
        for auth in authors:
            if 'last_name' in auth.keys():
                auths.append(auth["first_name"]+" "+auth["last_name"])
            else:
                auths.append(auth["first_name"])
        authlist = "; ".join(auths)
    else:
        authlist = f'{authors[0]["full_name"]} et al'
    outputstr += f"{authlist}\n"
    print(f'\t\t {authlist}')
    if hasarxiv:
        outputstr += f"https://arxiv.org/abs/{arxivno}\n"
        print(f'\t\t https://arxiv.org/abs/{arxivno}')
    inspireurl = f'https://inspirehep.net/literature/{controlno}'
    print(f'\t\t {inspireurl}')
    print('')
    if platform == 'darwin':
        CMD = '''
        on run argv
          display notification (item 2 of argv) with title (item 1 of argv)
        end run
        '''
        subprocess.call(['osascript', '-e', CMD, f"New citations for {ptitle}", outputstr])
    else:
        if 'TERMUX_VERSION' in os.environ.keys():
            os.system(f'termux-notification --action "xdg-open https://inspirehep.net/literature/{controlno}" -c "New citation for {ptitle}: {title}"')
        else:
            os.system(f'notify-send "New citation for {ptitle}" "{outputstr}"')
    return inspireurl

if os.path.exists('./lastrun'):
    with open('./lastrun','r') as f:
        lastrun = datetime.fromisoformat(f.read().strip())
else:
    print("Couldn't find ./lastrun file! Searching the past week")
    lastrun = datetime.now() - timedelta(days=7)
    lastrun = lastrun.astimezone()
urls = []
for ptitle,pid in queries_to_make.items():
    if not pid[0].isdigit():
        url = f'https://inspirehep.net/api/literature?sort=mostrecent&size=25&page=1&q=exactauthor%3A{pid}'
    else:
        url = f'https://inspirehep.net/api/literature?sort=mostrecent&size=25&page=1&q=refersto%3Arecid%3A{pid}'
    print(f"Checking {ptitle}")
    with urllib.request.urlopen(url) as r:
        data = json.loads(r.read())
        try:
            latest_update = process_json_date(data['hits']['hits'][0]['metadata']['earliest_date'])
        except Exception as e:
            print("Couldn't get latest update:",e)
        if lastrun < latest_update:
            for i in range(25):
                result = data['hits']['hits'][i]['metadata']
                latest_update = process_json_date(result['earliest_date'])
                if latest_update > lastrun:
                    url = output_info(ptitle,result)
                    urls.append(url)
                else:
                    break
        time.sleep(1)

with open('./lastrun','w') as f:
    f.write(datetime.now(timezone.utc).astimezone().isoformat())

urls = list(set(urls))
if len(urls) > 0:
    webbrowser.open_new(urls[0])
    for url in urls[1:]:
        webbrowser.open_new_tab(url)
