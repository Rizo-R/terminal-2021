import json
import os
from multiprocessing import Pool
from tqdm import tqdm


def reader(path):
    with open(f'../turndata/{path}') as f:
        for turn in f:
            json.loads(turn)


if __name__ == '__main__':

    turndata = [f for f in os.listdir('../turndata/') if f.endswith('turn')]
    pool = Pool(16)
    res = list(tqdm(pool.imap(reader, turndata)))
