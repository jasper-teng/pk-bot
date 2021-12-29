import os
from contextlib import contextmanager
from aiohttp import ClientSession, ClientError

from bs4 import BeautifulSoup

K_CAPTCHA_URL = 'https://p.eagate.573.jp/gate/p/common/login/api/kcaptcha_generate.html'
K_LOGIN_PAGE_ENDPOINT = 'https://p.eagate.573.jp/gate/k/API/common/getloginurl.html'
K_LOGIN_ENDPOINT = 'https://account.konami.net/auth/login.html'
K_HOST = 'https://p.eagate.573.jp/'


@contextmanager
def safe_open(fn, *args, **kwargs):
    try:
        os.replace(fn, f'{fn}.bak')
    except FileNotFoundError:
        pass

    try:
        with open(fn, *args, **kwargs) as f:
            yield f
    finally:
        pass


def get_play_count(s):
    try:
        return int(s[:-1])
    except ValueError:
        return None


def get_skill_level(s):
    try:
        return int(s[6:])
    except ValueError:
        return 12


def get_song_lookup_table(song_db):
    """ Return a reverse lookup table for song name/artist pair. """
    lookup = {}
    for row in song_db.itertuples():
        sid = row.Index
        sn, sa = row.song_name, row.song_artist
        lookup[sn, sa] = sid

    return lookup


async def fetch_page(session, url, use_post=False, **kwargs):
    """ Fetch a page, using Shift-JIS encoding. """
    session_was_none = False
    if session is None:
        session_was_none = True
        session = ClientSession()

    exception_happened = True
    while exception_happened:
        try:
            if use_post:
                r = await session.post(url, **kwargs)
            else:
                r = await session.get(url, **kwargs)
        except ClientError:
            continue
        else:
            exception_happened = False
    # noinspection PyUnboundLocalVariable
    return_val = BeautifulSoup(await r.text(encoding='shift-jis'), 'html5lib')

    if session_was_none:
        await session.close()

    return return_val


async def login_routine(user_id, user_pw):
    """ Return session object, logged in using provided credentials. """
    s = ClientSession()

    # Get login URL
    r = await s.post(K_LOGIN_PAGE_ENDPOINT,
                     data={
                         'path': '/gate/p/login_complete.html'
                     })
    login_url = await r.text()

    # Get "CSRF Middleware Token"
    soup = await fetch_page(s, url=login_url)
    csrf_token_element = soup.select_one('section.login input[name=csrfmiddlewaretoken]')
    csrf_token = csrf_token_element['value']

    # Send login request
    await s.post(K_LOGIN_ENDPOINT,
                 data={
                     'userId': user_id,
                     'password': user_pw,
                     'csrfmiddlewaretoken': csrf_token
                 })

    return s
