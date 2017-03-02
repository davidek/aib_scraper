import functools
import json
import os
from getpass import getpass

credentials_file = 'CREDENTIALS.json'

@functools.lru_cache()
def credentials():
    """Read the credentials file, return a pair of (registration_number, pac) strings"""
    with open(credentials_file) as f:
        c = json.loads(f.read())
    registration_number = c['registration_number']
    pac = c['pac']
    if pac is None and 'AIB_PAC' in os.environ and os.environ['AIB_PAC']:
        pac = os.environ['AIB_PAC']
    if pac is None:
        pac = getpass()

    if len(registration_number) != 8:
        raise Exception('Registration number should be of 8 digits')
    if len(pac) != 5:
        raise Exception('Pin should be of 5 digits')

    return (registration_number, pac)
