from PIL import Image
from dash.data.penguin import Penguin

from sanic import response
from sanic import Blueprint
from sanic.log import logger

import io
import asyncio
import urllib
import os

opener = urllib.request.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36')]
urllib.request.install_opener(opener)
avatar = Blueprint('avatar', url_prefix='/avatar')


@avatar.get('/<penguin_id:int>')
async def get_avatar(request, penguin_id: int):
    background = request.raw_args.get('photo', 'true')
    size = request.raw_args.get('size', 120)
    if int(size) > 600:
        size = '600'

    clothing = await Penguin.select(
        'photo', 'flag', 'color', 'head', 'face', 'body',  'neck', 'hand', 'feet'
    ).where(Penguin.id == penguin_id).gino.first()

    if clothing is None:
        return response.json({'message': 'Not found'}, status=404)

    if background != 'true':
        clothing.pop(0)

    loop = asyncio.get_event_loop()
    image = await loop.run_in_executor(None, build_avatar, clothing, int(size))
    return response.raw(image, headers={'Content-type': 'image/png'})


def build_avatar(clothing, size):
    avatar_image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    for item in filter(None, clothing):
        try:
            if not os.path.isdir(f"./items/{size}"):
                os.makedirs(f"./items/{size}")
            if not os.path.isfile(f"./items/{size}/{item}.png"): # temporary solution until wand mounts the avatar folder into dash
                urllib.request.urlretrieve(f"https://icer.ink/mobcdn.clubpenguin.com/game/items/images/paper/image/{size}/{item}.png", f"./items/{size}/{item}.png")
            
            item_image = Image.open(f'./items/{size}/{item}.png', 'r')
            avatar_image.paste(item_image, (0, 0), item_image)
        except FileNotFoundError as e:
            logger.error(e)

    b = io.BytesIO()
    avatar_image.save(b, 'PNG')
    return b.getvalue()
