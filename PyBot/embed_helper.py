from typing import Optional, Union, Tuple

import discord
from discord import Embed, Color, Colour


def to_embed(
        message: str,
        colour: Optional[Union[Colour, Tuple[int, int, int]]] = None,
        title: str = None,
        image_url: Optional[str] = None) -> Embed:
    """
    Convert string to embed with an optional title and colour
    :param message: The message content string
    :param colour: Embed discord colour or an RGB tuple.
    :param title: Embed title
    :param image_url: Optional image url to embed
    :return: The embed object built
    """
    if message is not None:
        description = message
    elif image_url is not None:
        description = image_url
    else:
        raise discord.InvalidArgument('Specify message or image_url')

    return discord.Embed(
        description=description,
        colour=colour if not isinstance(colour, (int, int, int)) else Color.from_rgb(colour[0], colour[1], colour[2]),
        image_url=image_url,
        title=title
    )
