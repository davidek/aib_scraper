import datetime as dt
from difflib import Differ, SequenceMatcher  # ?
import re
import subprocess
import sys

from .scraper import Transaction, AccountInfo

OLD_TXT_FILE = 'STATE_OLD.txt'
NEW_TXT_FILE = 'STATE_NEW.txt'

def diff_all(old, new):
    """Run the diff and return the diff exit code."""
    with open(OLD_TXT_FILE, 'w') as f:
        f.write(diffable_account_list_repr(old))
    with open(NEW_TXT_FILE, 'w') as f:
        f.write(diffable_account_list_repr(new))
    #call(['diff', '-u0', '-F^[^ ]', OLD_TXT_FILE, NEW_TXT_FILE])
    diff_res = subprocess.run(
        ['diff', '-u0', '-F^[^ ]', OLD_TXT_FILE, NEW_TXT_FILE],
        stdout=subprocess.PIPE)
    if diff_res.returncode >= 2:
        raise Exception(f'diff returned error {diff_res.returncode}')
    if diff_res.returncode == 1:
        lines = diff_res.stdout.decode().splitlines(True)
        lines = lines[2:]  # trim file names
        lines = [re.sub('@@.*@@', '@@', l) for l in lines]  # trim line numbers
        sys.stdout.writelines(lines)
    return diff_res.returncode
    # Exit status is 0 if inputs are the same, 1 if different, 2 if trouble


def diff(old, new):
    """Difference between the old AccountInfo and the new.
    
    Only care about new transactions and balance changes.
    Ignore trasnactions that disappeared from the recent ones.
    """


def diffable_account_list_repr(account_list):
    return '\n\n'.join(
        diffable_account_repr(account)
        for account in sorted(account_list, key=lambda a: a.name))


def diffable_account_repr(account):
    return f'''{account.name}
 Balance:\t{account.balance}
 Available:\t{account.available}
 Transactions:
{diffable_transaction_list_repr(account.pending + account.recent)}'''


def diffable_transaction_list_repr(tr_list):
    return '  ' + '\n  '.join(
        nice_transaction_repr(t) for t in
        sorted(tr_list, key=lambda t: (t.date, t.desc, t.value))
    )


def nice_transaction_repr(tr):
    return f'{tr.date}\t{tr.value:>10}   {tr.desc}'


# {'Jan': 1, ...}
MONTHS = {s: i+1 for i, s in enumerate(
    'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split())}


def date_sort_key(date):
    """Tries to parse the date.
    
    >>> date_sort_key('Tuesday, 21st February 17')
    (17, 1, 21)
    """
    if isinstance(date, str):
        match = re.match(r'^[^ ]+ ([0-9]+).. ([^ ]+) ([0-9]+)', date)
        if match is not None:
            d, m, y = match[1], match[2], match[3]
            d, m, y = int(d, base=10), MONTHS[m[:3]], int(y, base=10)
            return (y, m, d)
    return date
            
