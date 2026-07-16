from __future__ import annotations

from typing import Callable

from . import discord_adapter, telegram_adapter
from .base import ChannelAdapter

# Un canal nuevo se agrega acá y en su propio archivo (discord_adapter.py,
# telegram_adapter.py, ...); nada más del bot necesita cambiar.
_CHANNEL_FACTORIES: dict[str, Callable[[], ChannelAdapter]] = {
    "telegram": telegram_adapter.create_from_env,
    "discord": discord_adapter.create_from_env,
}


def create_channel_adapters(enabled_channels: list[str]) -> list[ChannelAdapter]:
    """Construye un ChannelAdapter por cada nombre en enabled_channels (definido
    en ENABLED_CHANNELS del .env), para correr varios canales a la vez."""
    adapters = []
    for name in enabled_channels:
        factory = _CHANNEL_FACTORIES.get(name)
        if factory is None:
            disponibles = ", ".join(sorted(_CHANNEL_FACTORIES))
            raise ValueError(f"Canal desconocido: '{name}'. Disponibles: {disponibles}")
        adapters.append(factory())
    return adapters
