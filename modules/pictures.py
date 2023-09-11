# Picture editing section of Glassbox
import os
from os import path
import logging
import urllib.request
import json
import PIL
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger('glassbox')

if not path.exists(path.join(path.curdir, 'data', 'tmp')):
    os.mkdir(path.join(path.curdir, 'data', 'tmp'))
api_token = ''
if not os.path.exists('tenor_api_token.txt'):
    with open('tenor_api_token.txt', 'x') as f:
        f.close()
with open('tenor_api_token.txt', 'r') as f:
    api_token = f.read()
    if api_token == '':
        logger.error("No Tenor API token! This module may not work properly. "
                     "Please put a developer token in tenor_api_token.txt")


def wrap_text(text: str, font: ImageFont.FreeTypeFont, line_length: int, max_height: int):
    lines = ['']
    for word in text.split():
        line = f'{lines[-1]} {word}'.strip()
        if font.getlength(line) <= line_length:
            lines[-1] = line
        else:
            lines.append(word)
    out = '\n'.join(lines)
    if out == '':
        raise UserWarning('Invalid text.')
    elif len(lines) * font.getbbox(out)[3] > max_height:
        raise UserWarning('Input text too long.')
    return out


def downey_meme(text, fnt_size=48):
    if text == '':
        raise UserWarning('No text given.')
    downey = Image.open(path.join(path.curdir, 'data', 'images', 'downey.jpg'))
    downey_draw = ImageDraw.Draw(downey)
    min_size = 18
    max_size = 48
    while abs(max_size-min_size) > 1:
        fnt = ImageFont.truetype(path.join('data', 'fonts', 'arialbd.ttf'), int(fnt_size))
        try:
            wrap_text(text, fnt, 500, 240)
            # The size is too small
            min_size = fnt_size
            fnt_size = int((fnt_size + max_size) / 2)
        except UserWarning:
            # The size is too big
            if fnt_size > 18:
                max_size = fnt_size
                fnt_size = int((fnt_size + min_size) / 2)
            else:
                raise UserWarning('Input text too long.')
    fnt = ImageFont.truetype(path.join('data', 'fonts', 'arialbd.ttf'), int(fnt_size))
    wrapped_text = wrap_text(text, fnt, 500, 240)
    downey_draw.text((100, 150), wrapped_text, font=fnt, fill=(0, 0, 0))
    fp = path.join(path.curdir, 'data', 'tmp', 'tmp_downey.jpg')
    downey.save(fp)
    return fp


def inspirational_meme(image_url, header='', body=''):
    if header == '':
        raise UserWarning('No caption provided!')
    if image_url.startswith('https://tenor.com/view/'):
        image_url = get_tenor_true_url(image_url)
    req = urllib.request.Request(url=image_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as url:
        try:
            image = Image.open(url)
        except PIL.UnidentifiedImageError:
            raise UserWarning('Invalid image!')
    if image.size[0] > 8192 or image.size[1] > 8192:
        raise UserWarning('Image too large!')
    x = round(image.size[0]*1.5)
    y = round(image.size[1]*1.5)
    offset = 0.025 * y
    corner_x = round((x - image.size[0]) * 0.5)
    corner_y = round((y - image.size[1]) * 0.3)
    fnt_head = ImageFont.truetype(path.join('data', 'fonts', 'times.ttf'), round(0.11*y*0.75))
    fnt_body = ImageFont.truetype(path.join('data', 'fonts', 'times.ttf'), round(0.07*y*0.75))
    # TODO implement binary searches for these
    size_bad = True
    while size_bad:
        try:
            wrapped = wrap_text(header.upper(), fnt_head, int(0.9*x), int(0.11*y))
            if '\n' in wrapped:
                fnt_head = ImageFont.truetype(path.join('data', 'fonts', 'times.ttf'), fnt_head.size - 1)
            else: 
                size_bad = False
        except UserWarning:
            fnt_head = ImageFont.truetype(path.join('data', 'fonts', 'times.ttf'), fnt_head.size - 1)
    size_bad = True
    while size_bad and body != '':
        try:
            wrapped = wrap_text(body.upper(), fnt_body, int(0.9*x), int(0.07*y))
            if '\n' in wrapped:
                fnt_body = ImageFont.truetype(path.join('data', 'fonts', 'times.ttf'), fnt_body.size - 1)
            else: 
                size_bad = False
        except UserWarning:
            fnt_body = ImageFont.truetype(path.join('data', 'fonts', 'times.ttf'), fnt_body.size - 1)
    try:
        animated = image.is_animated
    except AttributeError:
        animated = False
    if animated:
        if image.size[0] > 1280 or image.size[1] > 720:
            raise UserWarning('Image too large!')
        frames = []
        for frame_num in range(image.n_frames):
            image.seek(frame_num)
            canvas = Image.new('RGB', (round(image.size[0]*1.5), round(image.size[1]*1.5)))
            draw = ImageDraw.Draw(canvas)
            draw.rectangle((
                (corner_x - offset, corner_y - offset),
                (corner_x + image.size[0] + offset, corner_y + image.size[1] + offset)
            ), fill=(0, 0, 0), outline=(240, 240, 240), width=round(offset/8))
            canvas.paste(image, (corner_x, corner_y))
            draw.text(
                xy=(round(x / 2), round(corner_y + image.size[1] + offset)),
                text=header.upper(),
                fill=(240, 240, 240), font=fnt_head, anchor='ma',
            )
            header_size = fnt_head.getbbox(header.upper())
            draw.text(
                xy=(round(x / 2), round(corner_y + offset + image.size[1] + header_size[1] + header_size[3])),
                text=body.upper(),
                fill=(240, 240, 240), font=fnt_body, anchor='ma',
            )
            canvas = canvas.crop((0, 0, x, int(image.size[1]*1.5*0.79 +
                                               1.5*fnt_head.getbbox(header.upper(), anchor='la')[3] +
                                               1.5*fnt_body.getbbox(header.upper(), anchor='la')[3])))
            canvas = canvas.convert(mode='P', palette=Image.ADAPTIVE)
            frames.append(canvas)
        fp = path.join(path.curdir, 'data', 'tmp', 'tmp_inspirational.gif')
        frames[0].save(fp, append_images=frames[1:], save_all=True, loop=0, duration=image.info.get('duration'))
    else:
        canvas = Image.new('RGB', (round(image.size[0]*1.5), round(image.size[1]*1.5)))
        draw = ImageDraw.Draw(canvas)
        draw.rectangle((
            (corner_x - offset, corner_y - offset),
            (corner_x + image.size[0] + offset, corner_y + image.size[1] + offset)
        ), fill=(0, 0, 0), outline=(240, 240, 240), width=round(offset/8))
        canvas.paste(image, (corner_x, corner_y))
        draw.text(
            xy=(round(x / 2), round(corner_y + image.size[1] + offset)),
            text=header.upper(),
            fill=(240, 240, 240), font=fnt_head, anchor='ma',
        )
        header_size = fnt_head.getbbox(header.upper())
        draw.text(
            xy=(round(x / 2), round(corner_y + offset + image.size[1] + header_size[1] + header_size[3])),
            text=body.upper(),
            fill=(240, 240, 240), font=fnt_body, anchor='ma',
        )
        canvas = canvas.crop((0, 0, x, int(image.size[1]*1.5*0.79 +
                                           1.5*fnt_head.getbbox(header.upper(), anchor='la')[3] +
                                           1.5*fnt_body.getbbox(header.upper(), anchor='la')[3])))
        fp = path.join(path.curdir, 'data', 'tmp', 'tmp_inspirational.jpg')
        canvas.save(fp)
    return fp


def get_tenor_true_url(raw_url: str):
    if api_token == '':
        logger.error('No token provided; Tenor handling cannot continue.')
        raise LookupError('An internal error occurred. Please contact the bot owner.')
    gif_id = raw_url.split('-')[-1]
    url = f'https://tenor.googleapis.com/v2/posts?ids={gif_id}&key={api_token}'
    request_site = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    web_url = urllib.request.urlopen(request_site)
    resp = json.loads(web_url.read().decode(web_url.info().get_content_charset('utf-8')))
    if resp.get('error'):
        error_msg = resp['error']
        raise LookupError(error_msg)
    print(resp['results'][0]['media_formats']['gif']['url'])
    return resp['results'][0]['media_formats']['gif']['url']


def caption(image_url: str, cap=''):
    if cap == '':
        raise UserWarning('No caption provided!')
    if image_url.startswith('https://tenor.com/view/'):
        image_url = get_tenor_true_url(image_url)
    req = urllib.request.Request(url=image_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as url:
        try:
            image = Image.open(url)
        except PIL.UnidentifiedImageError:
            raise UserWarning('Invalid image!')
    if image.size[0] > 8192 or image.size[1] > 8192:
        raise UserWarning('Image too large!')
    font_size = round((image.size[1] / 7.2) * 0.75)
    fnt = ImageFont.truetype(path.join('data', 'fonts', 'impact.ttf'), font_size)
    try:
        wrapped_text = wrap_text(cap, fnt, round(image.size[0] * 0.9), 8192)
    except UserWarning:
        raise UserWarning('Input text too long.')
    x = image.size[0]
    y = image.size[1] + round(ImageDraw.Draw(image).multiline_textbbox(xy=(0, 0), text=wrapped_text, font=fnt)[3] * 1.3)
    try:
        animated = image.is_animated
    except AttributeError:
        animated = False
    if animated:
        if image.size[0] > 1280 or image.size[1] > 720:
            raise UserWarning('Image too large!')
        frames = []
        for frame_num in range(image.n_frames):
            image.seek(frame_num)
            canvas = Image.new('RGB', (x, y))
            draw = ImageDraw.Draw(canvas)
            draw.rectangle((0, 0, x, y), fill=(255, 255, 255))
            canvas.paste(image, (0, y - image.size[1]))
            draw.text(
                xy=(round(x/2), round((y - image.size[1]) / 1.1)),
                text=wrapped_text,
                fill=(0, 0, 0), font=fnt, anchor='md', align='center'
            )
            canvas = canvas.convert(mode='P', palette=Image.ADAPTIVE)
            frames.append(canvas)
        fp = path.join(path.curdir, 'data', 'tmp', 'tmp_captioned.gif')
        frames[0].save(fp, append_images=frames[1:], save_all=True, loop=0, duration=image.info.get('duration'))
    else:
        canvas = Image.new('RGB', (x, y))
        draw = ImageDraw.Draw(canvas)
        draw.rectangle((0, 0, x, y), fill=(255, 255, 255))
        canvas.paste(image, (0, y - image.size[1]))
        draw.text(
            xy=(round(x/2), round((y - image.size[1]) / 1.1)),
            text=wrapped_text,
            fill=(0, 0, 0), font=fnt, anchor='md', align='center'
        )
        fp = path.join(path.curdir, 'data', 'tmp', 'tmp_captioned.png')
        canvas.save(fp)
    return fp


def reverse(image_url: str):
    if image_url.startswith('https://tenor.com/view/'):
        image_url = get_tenor_true_url(image_url)
    req = urllib.request.Request(url=image_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as url:
        try:
            image = Image.open(url)
        except PIL.UnidentifiedImageError:
            raise UserWarning('Invalid image!')
    if image.size[0] > 1280 or image.size[1] > 720:
        raise UserWarning('Image too large!')
    try:
        animated = image.is_animated
    except AttributeError:
        animated = False
    if not animated:
        raise UserWarning('The image is not animated!')
    frames = []
    for frame_num in range(image.n_frames):
        image.seek(frame_num)
        canvas = Image.new('RGBA', image.size)
        canvas.paste(image, (0, 0))
        canvas = canvas.convert(mode='P', palette=Image.ADAPTIVE)
        frames.append(canvas)
    fp = path.join(path.curdir, 'data', 'tmp', 'tmp_reversed.gif')
    frames.reverse()
    frames[0].save(fp, append_images=frames[1:], save_all=True, loop=0, duration=image.info.get('duration'))
    return fp


def make_gif(image_url: str):
    if image_url.startswith('https://tenor.com/view/'):
        image_url = get_tenor_true_url(image_url)
    req = urllib.request.Request(url=image_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as url:
        try:
            image = Image.open(url)
        except PIL.UnidentifiedImageError:
            raise UserWarning('Invalid image!')
    if image.size[0] > 8192 or image.size[1] > 8192:
        raise UserWarning('Image too large!')
    try:
        animated = image.is_animated
    except AttributeError:
        animated = False
    if image_url.endswith('.gif'):
        animated = True
    if animated:
        raise ValueError('The image is already a gif!')
    fp = path.join(path.curdir, 'data', 'tmp', 'tmp_gif.gif')
    image.save(fp, format='PNG', optimize=True)
    return fp
