from __future__ import annotations

import os

from telegram import Update
from telegram.ext import Application
from telegram.ext import ContextTypes
from telegram.ext import MessageHandler as PTBMessageHandler
from telegram.ext import filters

from .base import Channel, ChannelAdapter, IncomingMessage, MessageHandler, OutgoingMessage


class TelegramAdapter(ChannelAdapter):
    def __init__(self, bot_token: str) -> None:
        self._app = Application.builder().token(bot_token).build()

    async def start(self, on_message: MessageHandler) -> None:
        async def handle_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            if update.message is None or update.message.text is None:
                return
            incoming = IncomingMessage(
                channel=Channel.TELEGRAM,
                user_id=str(update.effective_user.id),
                chat_id=str(update.effective_chat.id),
                text=update.message.text,
            )
            outgoing = await on_message(incoming)
            await context.bot.send_message(chat_id=outgoing.chat_id, text=outgoing.text)

        self._app.add_handler(PTBMessageHandler(filters.TEXT & ~filters.COMMAND, handle_update))
        await self._app.initialize()
        await self._app.start()
        await self._app.updater.start_polling()

    async def send(self, message: OutgoingMessage) -> None:
        await self._app.bot.send_message(chat_id=message.chat_id, text=message.text)


def create_from_env() -> TelegramAdapter:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN no está configurado en .env")
    return TelegramAdapter(token)
