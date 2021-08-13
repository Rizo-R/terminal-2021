from multiprocessing import Pool
from tqdm import tqdm
import sys
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

USERNAME = 'USER'
PASSWORD = 'PASS'
SAVE_DIRECTORY = '../replays'

def getMatchContent(match_id):
    try:
        url = 'https://terminal.c1games.com/api/game/replayexpanded/' + str(match_id)
        auth = (USERNAME, PASSWORD)
        r = requests.get(url, auth=auth, verify=False)
        f = open(SAVE_DIRECTORY + str(match_id) + '.replay', 'wb')
        f.write(r.content)
        f.close()
        print('match {} has been downloaded'.format(match_id))
    except Exception as e:
        print("\nerror trying to download match", match_id, ":", e)
        # raise ValueError


if __name__ == "__main__":
    args = sys.argv
    pool = Pool(processes=16)
    res = list(tqdm(pool.imap(getMatchContent, range(870000, 8750000))))
