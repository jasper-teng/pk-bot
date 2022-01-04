import json
import os
import pandas
import time

from discord import Embed
from ext._scraperutils import (
    fetch_page,
    get_play_count,
    get_skill_level,
    get_song_lookup_table,
    login_routine,
    safe_open
)

K_PROFILEURL = 'https://p.eagate.573.jp/game/sdvx/vi/playdata/rival/profile.html'
K_SCOREURL = 'https://p.eagate.573.jp/game/sdvx/vi/playdata/rival/score.html'
K_MUSICURL = 'https://p.eagate.573.jp/game/sdvx/vi/music/index.html'
CLEAR_MARK_TABLE = {'play': 0, 'comp': 1, 'comp_ex': 2, 'uc': 3, 'per': 4}
REL_PATH = os.path.join('..', 'sdvx-score-viewer')
SONG_DB_PATH = os.path.join('..', 'sdvx-db', 'db.json')
CONFIG_PATH = os.path.join(REL_PATH, 'config.json')
PROFILE_LIST_PATH = os.path.join(REL_PATH, 'scores', 'profile_list.json')
INF_NAME = ['', '', 'inf', 'grv', 'hvn', 'vvd']


def is_sdvx_id(st):
    if len(st) == 8:
        try:
            _ = int(st)
            retval = f'SV-{st[:4]}-{st[4:]}'
        except ValueError:
            return False
    elif len(st) == 12:
        if st[:3] != 'SV-':
            return False
        if st[7] != '-':
            return False
        try:
            retval = st
            _ = int(st[3:7]) + int(st[8:])
        except ValueError:
            return False
    else:
        return False
    return retval


async def update_songs(*, bot, full_check=False):
    try:
        music_db = pandas.read_json(SONG_DB_PATH, orient='index')
    except json.JSONDecodeError:
        bot.log('Scraper', 'Song database cannot be read. Overwriting.')
        music_db = pandas.DataFrame()
    except IOError:
        bot.log('Scraper', 'Creating new song database file.')
        music_db = pandas.DataFrame()
    new_data = []

    # Get number of pages to crawl through
    soup = await fetch_page(None,
                            K_MUSICURL,
                            use_post=True,
                            data={'page': 1})
    sel_element = soup.select_one('select#search_page')
    max_page = max([int(e) for e in sel_element.stripped_strings])

    for pg in range(1, max_page + 1):
        soup = await fetch_page(None,
                                K_MUSICURL,
                                use_post=True,
                                data={'page': pg})
        music_data = soup.select('.music')

        song_in_database = False
        for music_info in music_data:
            [song_name, song_artist] = list(music_info.select_one('.info').stripped_strings)
            diff_info = music_info.select_one('.level')
            diff_dict = {e['class'][0]: int(e.string) for e in diff_info.children if hasattr(e, 'contents')}
            diffs = [0] * 5
            inf_ver = None

            song_in_database = False
            for diff_name, diff in diff_dict.items():
                if diff_name == 'nov':
                    diffs[0] = diff
                elif diff_name == 'adv':
                    diffs[1] = diff
                elif diff_name == 'exh':
                    diffs[2] = diff
                elif diff_name == 'mxm':
                    diffs[3] = diff
                else:
                    inf_ver = INF_NAME.index(diff_name)
                    diffs[4] = diff

            song_data = {
                'song_name': song_name,
                'song_name_alt': [],
                'song_artist': song_artist,
                'difficulties': diffs,
                'inf_ver': inf_ver,
                'sdvxin_id': '',
                'ver_path': ['', ''],
                'is_available': True
            }

            songs = music_db.loc[(music_db['song_name'] == song_name)
                                 & (music_db['song_artist'] == song_artist)
                                 & (music_db['inf_ver'] == inf_ver)]
            if len(songs) > 0:
                # Skip song if it's a full check, otherwise stop scraping
                if full_check:
                    continue
                else:
                    song_in_database = True
                    break

            new_data.append(song_data)

        if song_in_database:
            break

    current_id = max(music_db.index, default=-1) + 1
    indexes = []
    for song_data in reversed(new_data):
        songs = music_db.loc[(music_db['song_name'] == song_data['song_name'])
                             & (music_db['song_artist'] == song_data['song_artist'])
                             & (music_db['inf_ver'] == song_data['inf_ver'])]
        if len(songs) == 0:
            indexes.append(current_id)
            current_id += 1
        else:
            indexes.append(songs.indexes[0])

    indexes.reverse()
    new_data = pandas.DataFrame(new_data, index=indexes)
    music_db = new_data.combine_first(music_db)
    music_db.to_json(SONG_DB_PATH, orient='index')

    bot.log('Scraper', f'Written {len(new_data)} new entry(s) to database.')
    return new_data


async def update_score(msg, sdvx_id, *, bot, preview=False):
    # Load config info
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
    uname = config['username']
    pword = config['password']

    # config['sdvx_ids'].append(sdvx_id)
    # Remove duplicates
    # config['sdvx_ids'] = list(set(config['sdvx_ids']))

    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f)

    # Get session object
    session = await login_routine(uname, pword)

    try:
        with open(PROFILE_LIST_PATH, 'r') as f:
            sdvx_id_list = json.load(f)
    except json.JSONDecodeError:
        bot.log('Scraper', 'Profile list cannot be read. Overwriting.')
        sdvx_id_list = []
    except IOError:
        bot.log('Scraper', 'Existing profile list not found. Creating new file.')
        sdvx_id_list = []

    # Load song database
    song_db = pandas.read_json(SONG_DB_PATH, orient='index')
    id_lookup = get_song_lookup_table(song_db)

    completion_status = {}
    unsaved_songs = set()

    completion_status[sdvx_id] = None
    await update_message(msg, sdvx_id, completion_status)

    # Get first page
    soup = await fetch_page(session, f'{K_SCOREURL}?rival_id={sdvx_id}&page=1&sort_id=0&lv=1048575')
    try:
        max_page = int(soup.select('.page_num')[-1].string)
    except IndexError as e:
        bot.log('Scraper', f'Couldn\'t scrape ID {sdvx_id}. Scores may not be public, or profile does not exist.')
        completion_status[sdvx_id] = False
        raise e

    # Load/initialize score database
    try:
        with open(os.path.join(REL_PATH, 'scores', f'{sdvx_id}.json'), 'r') as f:
            player_db = json.load(f)
    except json.JSONDecodeError:
        bot.log('Scraper', f'Database cannot be read. Overwriting {sdvx_id}.json.')
        player_db = {}
    except IOError:
        bot.log('Scraper', f'Creating new file for ID {sdvx_id}.')
        player_db = {}

    # Get profile data
    soup = await fetch_page(session, f'{K_PROFILEURL}?rival_id={sdvx_id}')
    card_name = list(soup.select_one('#player_name').stripped_strings)[1]
    play_count = soup.select_one('.profile_cnt').string
    skill_level = soup.select_one('.profile_skill')['id']
    try:
        skill_name = list(soup.select_one('.profile_skill').stripped_strings)[0]
    except IndexError:
        skill_name = 'N/A'
    timestamp = time.time() * 1000

    player_db['card_name'] = card_name
    player_db['play_count'] = get_play_count(play_count)
    player_db['skill_level'] = get_skill_level(skill_level)
    player_db['skill_name'] = skill_name
    player_db['timestamp'] = timestamp
    player_db['scores'] = player_db.get('scores') or {}
    player_db['updated_scores'] = {}

    # Loop through pages
    scores = {}
    for pg in range(1, max_page + 1):
        completion_status[sdvx_id] = pg, max_page
        await update_message(msg, sdvx_id, completion_status)

        soup = await fetch_page(session, f'{K_SCOREURL}?rival_id={sdvx_id}&page={pg}&sort_id=0&lv=1048575')
        table_rows = soup.select('#pc_table tr')[1:]

        for song_rows in zip(*[iter(table_rows)] * 6):
            [song_name, song_artist] = list(song_rows[0].stripped_strings)
            try:
                song_id = id_lookup[song_name, song_artist]
            except KeyError:
                # bot.log('Scraper', f'Warning: cannot match ({song_name}, {song_artist})')
                unsaved_songs.add((song_name, song_artist))
                continue

            for diff, row in enumerate(song_rows[1:]):
                score_node = row.select_one('#score_col_3') or row.select_one('#score_col_4')
                score_node_str = list(score_node.stripped_strings)[0]
                
                if not score_node:
                    pass
                    # print(f'{K_SCOREURL}?rival_id={sdvx_id}&page={pg}&sort_id=0&lv=1048575')
                    # print(row.prettify())
                    # print(song_name)

                if score_node_str != '0':
                    clear_mark_url = score_node.select_one('img')['src']
                    clear_mark = CLEAR_MARK_TABLE[clear_mark_url[47:-4]]
                    score = int(score_node_str)

                    scores[f'{song_id}|{diff}'] = {
                        'clear_mark': clear_mark,
                        'score': score,
                        'timestamp': timestamp
                    }

    new_entries = []
    for key, data in scores.items():
        prev_data = player_db['scores'].get(key)
        if prev_data is None or data['clear_mark'] != prev_data['clear_mark'] or data['score'] != prev_data['score']:
            # Store old score for comparison
            if prev_data:
                player_db['updated_scores'][key] = prev_data
            else:
                player_db['updated_scores'][key] = {'clear_mark': None, 'score': 0}
            player_db['scores'][key] = data
            new_entries.append(key)

    new_new_entries = []
    for key in new_entries:
        sid, diff = key.split('|')
        sid = int(sid)
        sdata = song_db.loc[sid]
        if diff == '0':
            diff = 'NOV'
        elif diff == '1':
            diff = 'ADV'
        elif diff == '2':
            diff = 'EXH'
        elif diff == '3':
            diff = 'MXM'
        else:
            diff = INF_NAME[sdata.inf_ver].upper()
        new_new_entries.append(f'{sdata.song_name} [{diff}]')
    new_entries = new_new_entries

    # Save data
    if new_entries:
        if not preview:
            with safe_open(os.path.join(REL_PATH, 'scores', f'{sdvx_id}.json'), 'w', encoding='utf-8') as f:
                json.dump(player_db, f)
            if sdvx_id not in sdvx_id_list:
                sdvx_id_list.append(sdvx_id)

            bot.log('Scraper', f'{len(new_entries)} new entry(s) saved to {sdvx_id}.json.')
        else:
            bot.log('Scraper', f'{len(new_entries)} new entry(s) found for {sdvx_id}.')
    else:
        bot.log('Scraper', f'No new entries found for {sdvx_id}.')
    completion_status[sdvx_id] = True

    await update_message(msg, sdvx_id, completion_status)

    sdvx_id_list.sort()
    with safe_open(PROFILE_LIST_PATH, 'w') as f:
        json.dump(sdvx_id_list, f)

    await session.close()
    return {
        'skipped': unsaved_songs,
        'new_entry': new_entries
    }


async def update_message(msg, sdvx_id, status):
    texts = []
    if sdvx_id not in status:
        texts.append(sdvx_id)
    elif status[sdvx_id] is None:
        texts.append(f'{sdvx_id}...')
    elif isinstance(status[sdvx_id], tuple):
        texts.append(f'{sdvx_id}... {status[sdvx_id][0]}/{status[sdvx_id][1]}')
    elif status[sdvx_id]:
        texts.append(f'{sdvx_id}... ⭕')
    elif not status[sdvx_id]:
        texts.append(f'{sdvx_id}... ❌')
    desc = '```' + '\n'.join(texts) + '```'

    embed = Embed(title='SDVX score scraper', description=desc)
    await msg.edit(embed=embed)
