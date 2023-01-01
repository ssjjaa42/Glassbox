# Picture editing section of Glassbox
import os
from os import path
import urllib.request
from PIL import Image, ImageDraw, ImageFont

if not path.exists(path.join(path.curdir, 'data', 'tmp')):
    os.mkdir(path.join(path.curdir, 'data', 'tmp'))


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
        raise UserWarning('Input length too long.')
    return out


def downey_meme(text, fnt_size=48):
    if text == '':
        raise UserWarning('No text given.')
    downey = Image.open(path.join(path.curdir, 'data', 'images', 'downey.jpg'))
    downey_draw = ImageDraw.Draw(downey)
    fnt = ImageFont.truetype('arialbd.ttf', fnt_size)
    try:
        wrapped_text = wrap_text(text, fnt, 500, 240)
    except UserWarning:
        if fnt_size >= 8:
            return downey_meme(text, fnt_size - 1)
        else:
            raise UserWarning('Input length too long.')
    downey_draw.text((100, 150), wrapped_text, font=fnt, fill=(0, 0, 0))
    fp = path.join(path.curdir, 'data', 'tmp', 'tmp_downey.jpg')
    downey.save(fp)
    return fp


def inspirational_meme(image_url, header='', body='', head_size=120, body_size=120):
    if header == '':
        raise UserWarning('No caption provided!')
    req = urllib.request.Request(url=image_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as url:
        image = Image.open(url)
    canvas = Image.new('RGB', (round(image.size[0]*1.3) + 60, round(image.size[1]*1.3) + 60))
    draw = ImageDraw.Draw(canvas)
    x = canvas.size[0]
    y = canvas.size[1]
    offset = 13
    corner_x = round((x - image.size[0]) * 0.5)
    corner_y = round((y - image.size[1]) * 0.3)
    draw.rectangle((
        (corner_x - offset, corner_y - offset),
        (corner_x + image.size[0] + offset, corner_y + image.size[1] + offset)
    ), fill=(0, 0, 0), outline=(240, 240, 240), width=5)
    canvas.paste(image, (corner_x, corner_y))
    fnt_head = ImageFont.truetype('times.ttf', round(0.11*y*0.75))
    fnt_body = ImageFont.truetype('times.ttf', round(0.07*y*0.75))
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
    fp = path.join(path.curdir, 'data', 'tmp', 'tmp_inspirational.jpg')
    canvas.save(fp)
    return fp
