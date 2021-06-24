import os
import requests
from contextlib import contextmanager

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


def get_play_count(s: str):
    try:
        return int(s)
    except ValueError:
        return None


def get_skill_level(s: str):
    try:
        return int(s[6:])
    except ValueError:
        return 12


def get_song_lookup_table(song_db: dict) -> dict:
    """ Return a reverse lookup table for song name/artist pair. """
    lookup = {}
    for sid, song_data in song_db.items():
        sn, sa = song_data['song_name'], song_data['song_artist']
        lookup[sn, sa] = sid

    return lookup


def fetch_page(session: [requests.Session, None], url: str, use_post=False, **kwargs) -> BeautifulSoup:
    """ Fetch a page, using Shift-JIS encoding. """
    if session is None:
        session = requests.Session()

    exception_happened = True
    while exception_happened:
        try:
            if use_post:
                r = session.post(url, **kwargs)
            else:
                r = session.get(url, **kwargs)
        except requests.exceptions.ConnectionError:
            continue
        else:
            exception_happened = False
    r.encoding = 'shift-jis'
    return BeautifulSoup(r.text, 'html5lib')


def login_routine(user_id: str, user_pw: str) -> requests.Session:
    """ Return session object, logged in using provided credentials. """
    s = requests.Session()

    # Get login URL
    r = s.post(K_LOGIN_PAGE_ENDPOINT,
               data={
                   'path': '/gate/p/login_complete.html'
               })
    login_url = r.text

    # Get "CSRF Middleware Token"
    soup = fetch_page(s, login_url)
    csrf_token_element = soup.select_one('section.login input[name=csrfmiddlewaretoken]')
    csrf_token = csrf_token_element['value']

    # Send login request
    r = s.post(K_LOGIN_ENDPOINT,
           data={
               'userId': user_id,
               'password': user_pw,
               'csrfmiddlewaretoken': csrf_token
           })

    return s


# def old_login_routine(user_id: str, user_pw: str) -> requests.Session:
#     """ Return session object, logged in using provided credentials. """
#     s = requests.Session()
#
#     # Get captcha data
#     r = s.get(K_CAPTCHA_URL)
#     json = r.json()
#
#     # Load captcha images
#     image_urls = [json['data']['correct_pic']] + [c['img_url'] for c in json['data']['choicelist'] if c['img_url']]
#     images = []
#     for url in image_urls:
#         r = s.get(url)
#         img = Image.open(io.BytesIO(r.content))
#         images.append(numpy.asarray(img))
#
#     # Prepare session key
#     session_key = json['data']['kcsess']
#     keys = [c['key'] for c in json['data']['choicelist'] if c['key']]
#
#     # Solve captcha with SSIM
#     image_hists = [numpy.histogram(img, bins=100)[0] for img in images]
#     image_hists = [img / img.size for img in image_hists]
#     correct_img = image_hists[0]
#     ssim_diff = [compare_ssim(correct_img, img) for img in image_hists[1:]]
#     sorted_ssim = sorted(ssim_diff, reverse=True)
#     selected = [ssim_diff.index(sorted_ssim[0]), ssim_diff.index(sorted_ssim[1])]
#     captcha_arr = ['k', session_key] + [k if i in selected else '' for (i, k) in enumerate(keys)]
#     captcha_string = '_'.join(captcha_arr)
#
#     # Send login request
#     s.post(K_LOGIN_ENDPOINT,
#            params={
#                'login_id': user_id,
#                'pass_word': user_pw,
#                'otp': '',
#                'resrv_url': K_HOST,
#                'captcha': captcha_string
#            })
#
#     return s