import json
import os
from multiprocessing import Pool
from tqdm import tqdm

def parse_replay(path):
    with open('../replays/' + path, 'r') as f:
        prefix = path.split('.')[0]
        lines = f.readlines()
        s = ''.join(lines).strip('\n')
        if s == '':
            pass
        else:
            lines = s.split('\n')
            config = json.loads(lines[0])
            if config['resources']['bitsPerRound'] != 1.0:
                return None
            else:
                turns = []
                for line in lines[2:]:
                    record = json.loads(line)
                    if record['turnInfo'][0] == 0:
                        turns.append(record)
                out = []
                for x in turns:
                    out.append(json.dumps(x))
                out = '\n'.join(out)
                outpath = prefix + '.turn'
                with open(f'../turndata/{outpath}', 'w') as outf:
                    outf.write(out)

if __name__ == '__main__':
    pool = Pool()
    replays = [f for f in os.listdir('../replays/') if f.endswith('replay')]
    res = list(tqdm(pool.imap(parse_replay, replays)))

