# Picture editing section of Glassbox
import os
from os import path
from PIL import Image, ImageDraw, ImageFont

if not path.exists(path.join(path.curdir, 'data', 'tmp')):
    os.mkdir(path.join(path.curdir, 'data', 'tmp'))


def wrap_text(text: str, font: ImageFont.ImageFont, line_length: int):
    lines = ['']
    for word in text.split():
        line = f'{lines[-1]} {word}'.strip()
        if font.getlength(line) <= line_length:
            lines[-1] = line
        else:
            lines.append(word)
    if '\n'.join(lines) == '':
        raise UserWarning('Invalid text.')
    elif len(lines) > 5:
        raise UserWarning('Input length too long.')
    return '\n'.join(lines)


def downey_meme(text):
    downey = Image.open(path.join(path.curdir, 'data', 'images', 'downey.jpg'))
    downey_draw = ImageDraw.Draw(downey)
    fnt = ImageFont.truetype('arialbd.ttf', 48)
    wrapped_text = wrap_text(text, fnt, 500)
    downey_draw.text((100, 150), wrapped_text, font=fnt, fill=(0, 0, 0))
    fp = path.join(path.curdir, 'data', 'tmp', 'tmp_downey.jpg')
    downey.save(fp)
    return fp
