from collections import OrderedDict
from decimal import Decimal
import re
from typing import NamedTuple, Any, List

from selenium import webdriver

from . import credentials


class TryAgainException(Exception):
    pass


class Transaction(NamedTuple):
    date: str  # Union(str, dt.date)?
    value: Decimal
    desc: str

    def __str__(self):
        return f'{self.date}, {self.value} {self.desc}'


class AccountInfo(NamedTuple):
    name: str
    balance: Decimal
    available: Decimal
    pending: List[Transaction]
    recent: List[Transaction]


class AIBScraper(object):
    def __init__(self):
        self.regnum, self.pac = credentials.credentials()
        self.reset()

    def reset(self):
        self.browser = webdriver.PhantomJS()
        self.browser.set_window_size(1024, 768) # The default w=400 triggers mobile site TODO: try out
        self.login()

    def login(self):
        self.browser.get('https://onlinebanking.aib.ie/inet/roi/login.htm')
        self.browser.find_element_by_css_selector('input#regNumber_id').send_keys(self.regnum)
        self.browser.find_element_by_id('nextButton').click()

        self.browser.find_element_by_id('loginstep2Form')
        for i in (1, 2, 3):
            fname = 'digit{}Text'.format(i)
            digit_str = self.browser.find_element_by_css_selector('form#loginstep2Form label[for={}]'.format(fname)).text
            if not digit_str.strip().startswith('Digit'):
                raise Exception('Expecting Digit')
            digit_index = int(digit_str.strip()[5:].strip()) - 1  # make it zero-based
            digit = self.pac[digit_index]
            self.browser.find_element_by_css_selector('form#loginstep2Form input#{}'.format(fname)).send_keys(digit)
        self.browser.find_element_by_id('nextButton').click()

        if 'Please try again later' in self.browser.find_element_by_css_selector('body').text:
            raise TryAgainException()

    def check_errors(self):
        errors = self.browser.find_elements_by_css_selector('.error_panel')
        errors = [e for e in errors if e.is_displayed()]
        errors = ' --- '.join([e.text for e in errors])
        if errors:
            if 'Please try again later' in errors:
                raise TryAgainException(errors)
            else:
                raise Exception(errors)

        timeoutbtns = self.browser.find_elements_by_id('stayLoggedIn')
        timeoutbtns = [b for b in timeoutbtns if b.is_displayed()]
        if timeoutbtns:
            timeoutbtn, = timeoutbtns
            timeoutbtn.click()
            print('Clicked on stay logged in!')

        loginbtns = self.browser.find_elements_by_css_selector('form#login button')
        loginbtns = [b for b in loginbtns if b.is_displayed()]
        if loginbtns:
            raise Exception('Logged out')

        logoutbtns = self.browser.find_elements_by_css_selector('form#formLogout button')
        logoutbtns = [b for b in logoutbtns if b.is_displayed()]
        if not logoutbtns:
            print('No logout button, maybe login didn\'t succeed?')

    def back_to_accounts(self):
        self.check_errors()
        self.browser.find_element_by_id('accountoverview_button_id').click()

    # def _findform(self, form_text):
    #     form, = [f for f in self.browser.find_elements_by_css_selector('form') if f.text.strip().lower() == form_text.lower()]
    #     return form

    def list_accounts(self):
        self.back_to_accounts()
        accountspans = self.browser.find_elements_by_css_selector('.myaccounts-list .myaccounts-item form button span')
        return [span.text for span in accountspans]

    def _enter_account(self, account_name):
        self.back_to_accounts()
        accountspans = self.browser.find_elements_by_css_selector('.myaccounts-list .myaccounts-item form button span')
        for span in accountspans:
            if span.text.strip() == account_name:
                break
        else:
            raise Exception('Account "{}" not found'.format(account_name))
        span.click()

    def scrape_account(self, account_name):
        self._enter_account(account_name)
        assert account_name == self.browser.find_element_by_css_selector('h2').text.strip()
        summary = self.browser.find_element_by_css_selector('.summary-panel')
        # sample summary.text:  'Balance:\n€1,234.56\nAvailable Funds :\n€1,234.56'
        match = re.search(r'Balance[^0-9,\.]+([0-9,\.]+)\s+Available[^0-9,\.]+([0-9,\.]+)', summary.text, flags=re.U|re.I)
        balance, available = _num(match[1]), _num(match[2])

        tables = self.browser.find_elements_by_css_selector('table.transaction-table')
        tables = [_parse_transaction_table(table) for table in tables]
        if len(tables) == 1:
            recent_table, = tables
            pending_table = []
        elif len(tables) == 2:
            pending_table, recent_table = tables
        else:
            raise Exception(f'Too many (or no) transaction tables: {len(tables)}')
        return AccountInfo(account_name, balance, available, pending_table, recent_table)

    def scrape_all(self):
        return [self.scrape_account(account) for account in self.list_accounts()]

    def status(self):
        print(self.browser.find_element_by_css_selector('body').text)


def _num(text_num):
    """Turn a string currency value to a Decimal.

    Values must have exately 2 sub-integer digits.
    >>> _num('1,234.56')
    Decimal('1234.56')
    """
    ret = Decimal(text_num.strip().replace(',', ''))
    assert ret.as_tuple().exponent == -2  # currency values have 2 decimal digits
    return ret


def _parse_transaction_table(table):
    """Given a selenium element (the transactions table), return a list of transactions"""
    rows = table.find_elements_by_css_selector('tr')
    header = rows[0]
    header = [td.text.strip() for td in header.find_elements_by_css_selector('td')]
    if header != ['Description', 'Paid out', 'Paid in', 'Balance'] and header != ['Description', 'Paid out', '', '']:
        raise Exception('unexcepted transaction table header!')
    rows = [r for r in rows[1:] if r.text]  # filter out empty rows
    ret = []
    date = None
    # Stateful parsing: each item starts with a date row and has one row with 'Paid out' or 'Paid in'
    for row in rows:
        if 'date-row' in row.get_attribute('class').split():
            date = _parse_datetime(row.text)
        else:
            cells = [c.text.strip() for c in row.find_elements_by_css_selector('td')]
            assert not (cells[1] and cells[2])  # either Paid in, or Paid out
            value = cells[1] or cells[2]
            if value:
                value = _num(value)
                ret.append(Transaction(date=date, value=value, desc=cells[0]))
    return ret


def _parse_datetime(datetime_str):
    return datetime_str
