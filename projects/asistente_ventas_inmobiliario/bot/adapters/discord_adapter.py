from __future__ import annotations

import os

import discord

from .base import Channel, ChannelAdapter, IncomingMessage, MessageHandler, OutgoingMessage


class DiscordAdapter(ChannelAdapter):
    def __init__(self, bot_token: str) -> None:
        self._token = bot_token
        intents = discord.Intents.default()
        intents.message_content = True
        self._client = discord.Client(intents=intents)

    async def start(self, on_message: MessageHandler) -> None:
        # discord.Client (a diferencia de commands.Bot) no tiene add_listener; su
        # decorador event() registra la corrutina por nombre (coro.__name__), así
        # que el handler de abajo debe llamarse literalmente "on_message". Por eso
        # guardamos el callback original en otra variable antes de shadowearlo.
        handle_message = on_message

        async def on_message(discord_message: discord.Message) -> None:
            if discord_message.author.bot:
                return
            incoming = IncomingMessage(
                channel=Channel.DISCORD,
                user_id=str(discord_message.author.id),
                chat_id=str(discord_message.channel.id),
                text=discord_message.content,
            )
            outgoing = await handle_message(incoming)
            await discord_message.channel.send(outgoing.text)

        self._client.event(on_message)
        await self._client.start(self._token)

    async def send(self, message: OutgoingMessage) -> None:
        channel = self._client.get_channel(int(message.chat_id))
        if channel is not None:
            await channel.send(message.text)


def create_from_env() -> DiscordAdapter:
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_BOT_TOKEN no está configurado en .env")
    return DiscordAdapter(token)
