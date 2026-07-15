from __future__ import annotations

import discord

from .base import Channel, ChannelAdapter, IncomingMessage, MessageHandler, OutgoingMessage


class DiscordAdapter(ChannelAdapter):
    def __init__(self, bot_token: str) -> None:
        self._token = bot_token
        intents = discord.Intents.default()
        intents.message_content = True
        self._client = discord.Client(intents=intents)

    async def start(self, on_message: MessageHandler) -> None:
        async def handle_discord_message(discord_message: discord.Message) -> None:
            if discord_message.author.bot:
                return
            incoming = IncomingMessage(
                channel=Channel.DISCORD,
                user_id=str(discord_message.author.id),
                chat_id=str(discord_message.channel.id),
                text=discord_message.content,
            )
            outgoing = await on_message(incoming)
            await discord_message.channel.send(outgoing.text)

        self._client.add_listener(handle_discord_message, "on_message")
        await self._client.start(self._token)

    async def send(self, message: OutgoingMessage) -> None:
        channel = self._client.get_channel(int(message.chat_id))
        if channel is not None:
            await channel.send(message.text)
