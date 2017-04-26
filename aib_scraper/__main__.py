import pickle
import sys

from . import scraper
from . import diff

STATE_FILE = 'STATE.pkl'

def main():
    new = scraper.AIBScraper().scrape_all()
    try:
        with open(STATE_FILE, 'rb') as f:
            old = pickle.load(f)
    except FileNotFoundError:
        # No previous state: save the current state and return without diffing
        ret = 0
    else:
        # old state available, perform the diff
        ret = diff.diff_all(old, new)

    with open(STATE_FILE, 'wb') as f:
        pickle.dump(new, f)

    sys.exit(ret)


if __name__ == '__main__':
    main()
