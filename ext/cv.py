import io
import re

import requests
import cv2
import numpy as np
import pytesseract
from discord import File, DeletedReferencedMessage
from discord.ext import commands


# TODO: refactor cvtest() to call smaller functions
class ComputerVision(commands.Cog):
    def __init__(self):
        # Result screen template
        self._template = cv2.imread('ext/cvtest/template.png')
        template_bw = cv2.cvtColor(self._template, cv2.COLOR_BGR2GRAY)

        # Score numbers
        self._nums = cv2.imread('ext/cvtest/numbers.png')
        self._nums = cv2.cvtColor(self._nums, cv2.COLOR_BGR2GRAY)
        _, self._nums = cv2.threshold(self._nums, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)

        # initialize SIFT (might change to ORB or something else)
        self._sift = cv2.SIFT_create()
        self._tkey, self._tdesc = self._sift.detectAndCompute(template_bw, None)
        self._matcher = cv2.FlannBasedMatcher({'algorithm': 1, 'trees': 5}, {'checks': 50})

        # Other parameters
        self._good_match_threshold = 75
        self._lowe_test_threshold = 0.7
        self._name_allowlist = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.!?#&*-'
        self._tess_params = f'--psm 7 -c tessedit_char_whitelist={self._name_allowlist}'

    @commands.command()
    async def cvtest(self, ctx):
        """ computer vision test """
        msg = ctx.message
        in_img = None
        while in_img is None:
            # in case message reference returns None
            if msg is None:
                break
            # check attachments
            if msg.attachments:
                for attach_img in msg.attachments:
                    try:
                        in_img = cv2.imdecode(np.frombuffer(await attach_img.read(), np.uint8), cv2.IMREAD_COLOR)
                    except Exception:
                        continue
            # otherwise check links in message
            urls = re.finditer(
                r'(?:https?://)?'               # http or https (optional)
                r'(?:[a-z0-9-]+\.)*'            # subdomain, etc (optional)
                r'[a-z0-9-]+\.[a-z0-9-]{2,}'    # domain and tld
                r'(?:/[a-z0-9~_!@.-]+)*/?'      # path
                r'(?:\?[a-z0-9_=,.-]*)?'        # query
                r'(?:#[a-z0-9_=,.-]*)?',        # anchor
                msg.content,
                re.IGNORECASE
            )
            for match in urls:
                url = match.group()
                print(url)
                try:
                    in_img = cv2.imdecode(np.frombuffer(requests.get(url).content, np.uint8), cv2.IMREAD_COLOR)
                except Exception:
                    continue
            # otherwise check reply
            if msg.reference is not None and not isinstance(msg.reference.resolved, DeletedReferencedMessage):
                msg = msg.reference.resolved
                continue
            break

        if in_img is None:
            await ctx.reply('Please provide an image!')
            return

        # Resize image to reasonable dimensions
        in_img = cv2.resize(in_img, (1200, in_img.shape[0] * 1200 // in_img.shape[1]))
        key, desc = self._sift.detectAndCompute(cv2.cvtColor(in_img, cv2.COLOR_BGR2GRAY), None)

        # Match features with the desired matcher
        matches = self._matcher.knnMatch(desc, self._tdesc, k=2)
        good_points = []
        for m, n in matches:
            if m.distance < self._lowe_test_threshold * n.distance:
                good_points.append(m)

        if len(good_points) < self._good_match_threshold:
            await ctx.reply(f'Image not recognized. ({len(good_points)} good matches)')
            return

        # Get points to find homography, and then warp the image
        src_pts = np.float32([key[m.queryIdx].pt for m in good_points]).reshape(-1, 1, 2)
        dst_pts = np.float32([self._tkey[m.trainIdx].pt for m in good_points]).reshape(-1, 1, 2)
        matrix, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

        temp_h, temp_w, _ = self._template.shape
        out_img = cv2.warpPerspective(in_img, matrix, (temp_w, temp_h))

        # Image output specification:
        # dimensions: 475 x 295
        # jacket resized to 115 x 115
        # diff resized to 115 x 27
        # score resized to 475 x 69
        # black background
        # ---
        # big_score = out_img[207:262, 438:670]
        # small_score = out_img[225:262, 670:815]
        # pb = out_img[274:289, 828:942]
        # diff = out_img[294:309, 828:942]
        score = out_img[207:262, 438:815]
        song_title = out_img[137:166, 403:878]
        song_artist = out_img[170:200, 403:878]
        diff = out_img[10:30, 205:289]
        details = out_img[338:480, 31:391]
        jacket = out_img[34:306, 23:295]
        card_name = out_img[600:625, 156:425]

        # Try to read score number
        score_bw = cv2.resize(score, (475, 69))
        score_bw = cv2.cvtColor(score_bw, cv2.COLOR_BGR2GRAY)
        score_bw = cv2.GaussianBlur(score_bw, (5, 5), 0)
        _, score_bw = cv2.threshold(score_bw, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        cur_x = 0
        score_val = 0
        for d in range(8):
            if d < 4:
                dw, dh = 72, 69
            else:
                dw, dh = 48, 46
            # Resize to fit template
            digit = score_bw[-dh:, cur_x:cur_x + dw]
            digit = cv2.resize(digit, (52, dh * 52 // dw))
            cur_x += dw

            # Nothing too fancy, just using template matching
            match_result = cv2.matchTemplate(digit, self._nums, cv2.TM_CCOEFF_NORMED)
            topleft_pos = cv2.minMaxLoc(match_result)[3]
            score_val = 10 * score_val + int(topleft_pos[0] / 52 + 0.5)  # rounding, not flooring

        # Try to read card name (sharpen filter ftw)
        card_name_bw = cv2.cvtColor(card_name, cv2.COLOR_BGR2GRAY)
        card_name_bw = cv2.filter2D(card_name_bw, -1, np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]]))
        card_name_bw = cv2.resize(card_name_bw, (0, 0), fx=4, fy=4)
        _, card_name_bw = cv2.threshold(card_name_bw, 0, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
        card_name_bw = card_name_bw[:, :538]
        # Slap the image in the middle of a big blank canvas
        #   otherwise Tesseract doesn't play nice
        # The canvas size is arbitrary tbh
        card_name_out = np.ones((1075, 1075), np.uint8) * 255
        # Is there a better way to write this?
        card_name_out[488:588, 268:806] = card_name_bw
        card_name_val = pytesseract.image_to_string(card_name_out, config=self._tess_params)
        card_name_val = card_name_val.strip()

        # Slot in all the cropped bits into the summarized image
        img = np.zeros((295, 475, 3), np.uint8)
        img[:25, :269] = card_name
        img[25:94, :] = cv2.resize(score, (475, 69))
        img[94:123, :] = song_title
        img[123:153, :] = song_artist
        img[153:, :360] = details
        img[153:268, 360:] = cv2.resize(jacket, (115, 115))
        img[268:, 360:] = cv2.resize(diff, (115, 27))
        # Encode image to a bytes sequence, and then put it in
        # BytesIO so that it plays nice with discord.File
        _, outbuf = cv2.imencode('.png', img)
        outbuf = io.BytesIO(outbuf)
        reply = f'{len(good_points)} good feature matches.\n'
        reply += f'I think the score is {score_val}'
        if card_name_val:
            reply += f' and the player name is {card_name_val}'
        reply += '.'
        await ctx.reply(reply, file=File(outbuf, 'output.png'))
        return


def setup(bot):
    bot.add_cog(ComputerVision())
