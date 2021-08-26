import asyncio
import json
import os
import sys
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
SONG_DB_PATH = os.path.join(REL_PATH, 'song_db.json')
CONFIG_PATH = os.path.join(REL_PATH, 'config.json')
PROFILE_LIST_PATH = os.path.join(REL_PATH, 'scores', 'profile_list.json')


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


async def update_songs(full_check=False):
    try:
        with open(SONG_DB_PATH, 'r', encoding='utf-8') as f:
            music_db = json.load(f)
    except json.JSONDecodeError:
        print('<Scraper> Database cannot be read. Overwriting.')
        music_db = {}
    except IOError:
        print('<Scraper> Creating new song database file.')
        music_db = {}
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
            diffs = [None] * 5
            diff4_name = None

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
                    diff4_name = diff_name.upper()
                    diffs[4] = diff

            song_data = {
                'song_name': song_name,
                'song_artist': song_artist,
                'diff4_name': diff4_name,
                'difficulties': diffs
            }

            if song_data in music_db.values():
                # Skip song if it's a full check, otherwise stop scraping
                if full_check:
                    continue
                else:
                    song_in_database = True
                    break

            new_data.append(song_data)

        if song_in_database:
            break

    current_id = max([int(sid) for sid in music_db], default=-1) + 1
    if music_db:
        id_list, data_list = zip(*music_db.items())
    else:
        id_list = []
        data_list = []
    for song_data in reversed(new_data):
        try:
            song_id = data_list.index(song_data)
        except ValueError:
            song_id = current_id
            current_id += 1

        music_db[song_id] = song_data

    with safe_open(SONG_DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(music_db, f)

    print(f'<Scraper> Written {len(new_data)} new entry(s) to database.')
    return new_data


async def update_score(msg, sdvx_ids):
    # Load config info
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
    uname = config['username']
    pword = config['password']

    config['sdvx_ids'].extend(sdvx_ids)
    config['sdvx_ids'] = list(set(config['sdvx_ids']))

    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f)

    # Get session object
    session = await login_routine(uname, pword)

    try:
        with open(PROFILE_LIST_PATH, 'r') as f:
            sdvx_id_list = json.load(f)
    except json.JSONDecodeError:
        print('<Scraper> Database cannot be read. Overwriting.')
        sdvx_id_list = []
    except IOError:
        print('<Scraper> Existing data not found. Creating new file.')
        sdvx_id_list = []

    # Load song database
    with open(SONG_DB_PATH, 'r', encoding='utf-8') as f:
        song_db = json.load(f)
    id_lookup = get_song_lookup_table(song_db)

    completion_status = {}
    unsaved_songs = set()

    async def coroutine(d_id):
        completion_status[d_id] = None
        await update_message(msg, sdvx_ids, completion_status)

        # Get first page
        soup = await fetch_page(session, f'{K_SCOREURL}?rival_id={d_id}&page=1&sort_id=0&lv=1048575')
        try:
            max_page = int(soup.select('.page_num')[-1].string)
        except IndexError:
            print(f'<Scraper> Couldn\'t scrape ID {d_id}. Scores may not be public, or profile does not exist.')
            completion_status[d_id] = False
            return

        # Load/initialize score database
        try:
            with open(os.path.join(REL_PATH, 'scores', f'{d_id}.json'), 'r') as f:
                player_db = json.load(f)
        except json.JSONDecodeError:
            print(f'<Scraper> Database cannot be read. Overwriting {d_id}.json.')
            player_db = {}
        except IOError:
            print(f'<Scraper> Creating new file for ID {d_id}.')
            player_db = {}

        # Get profile data
        soup = await fetch_page(session, f'{K_PROFILEURL}?rival_id={d_id}')
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
            completion_status[d_id] = pg, max_page
            await update_message(msg, sdvx_ids, completion_status)

            soup = await fetch_page(session, f'{K_SCOREURL}?rival_id={d_id}&page={pg}&sort_id=0&lv=1048575')
            table_rows = soup.select('#pc_table tr')[1:]

            for song_rows in zip(*[iter(table_rows)] * 6):
                [song_name, song_artist] = list(song_rows[0].stripped_strings)
                try:
                    song_id = id_lookup[song_name, song_artist]
                except KeyError:
                    print(f'<Scraper> Warning: cannot match ({song_name}, {song_artist})')
                    unsaved_songs.add((song_name, song_artist))
                    continue

                for diff, row in enumerate(song_rows[1:]):
                    score_node = row.select_one('#score_col_3') or row.select_one('#score_col_4')
                    score_node_str = list(score_node.stripped_strings)[0]
                    
                    if not score_node:
                        print(f'{K_SCOREURL}?rival_id={d_id}&page={pg}&sort_id=0&lv=1048575')
                        print(row.prettify())
                        print(song_name)

                    if score_node_str != '0':
                        clear_mark_url = score_node.select_one('img')['src']
                        clear_mark = CLEAR_MARK_TABLE[clear_mark_url[47:-4]]
                        score = int(score_node_str)

                        scores[f'{song_id}|{diff}'] = {
                            'clear_mark': clear_mark,
                            'score': score,
                            'timestamp': timestamp
                        }

        new_entries = 0
        for key, data in scores.items():
            prev_data = player_db['scores'].get(key)
            if prev_data is None or data['clear_mark'] != prev_data['clear_mark'] or data['score'] != prev_data['score']:
                # Store old score for comparison
                if prev_data:
                    player_db['updated_scores'][key] = prev_data
                else:
                    player_db['updated_scores'][key] = {'clear_mark': None, 'score': 0}
                player_db['scores'][key] = data
                new_entries += 1

        # Save data
        if new_entries:
            with safe_open(os.path.join(REL_PATH, 'scores', f'{d_id}.json'), 'w', encoding='utf-8') as f:
                json.dump(player_db, f)
            if d_id not in sdvx_id_list:
                sdvx_id_list.append(d_id)

            print(f'<Scraper> {new_entries} new entry(s) saved to {d_id}.json.')
        else:
            print(f'<Scraper> No new entries found for {d_id}.')
        completion_status[d_id] = True

    coros = [coroutine(sdvx_id) for sdvx_id in sdvx_ids]
    await asyncio.gather(*coros)

    await update_message(msg, sdvx_ids, completion_status)

    sdvx_id_list.sort()
    with safe_open(PROFILE_LIST_PATH, 'w') as f:
        json.dump(sdvx_id_list, f)

    await session.close()
    return unsaved_songs


async def update_message(msg, id_list, status, skipped_songs=None):
    texts = []
    for sdvx_id in sorted(id_list):
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
