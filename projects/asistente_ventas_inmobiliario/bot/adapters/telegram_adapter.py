from __future__ import annotations

import os
import re

from telegram import Bot, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import Application
from telegram.ext import ContextTypes
from telegram.ext import MessageHandler as PTBMessageHandler
from telegram.ext import filters

from .base import Channel, ChannelAdapter, IncomingMessage, MessageHandler, OutgoingMessage

# El LLM genera markdown estilo CommonMark (**negrita**); el modo "Markdown"
# (v1) de Telegram, que es el único que no exige escapar puntuación normal
# como "." o "-", usa una sola asterisco para negrita.
_BOLD_MARKER = re.compile(r"\*\*(.+?)\*\*")


async def _send(bot: Bot, chat_id: str, text: str) -> None:
    normalized = _BOLD_MARKER.sub(r"*\1*", text)
    try:
        await bot.send_message(chat_id=chat_id, text=normalized, parse_mode=ParseMode.MARKDOWN)
    except BadRequest:
        # El LLM no siempre produce markdown balanceado (paréntesis/asteriscos
        # sueltos); mejor perder el formato que no entregar la respuesta.
        await bot.send_message(chat_id=chat_id, text=text)


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
            await _send(context.bot, outgoing.chat_id, outgoing.text)

        self._app.add_handler(PTBMessageHandler(filters.TEXT & ~filters.COMMAND, handle_update))
        await self._app.initialize()
        await self._app.start()
        await self._app.updater.start_polling()

    async def send(self, message: OutgoingMessage) -> None:
        await _send(self._app.bot, message.chat_id, message.text)


def create_from_env() -> TelegramAdapter:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN no está configurado en .env")
    return TelegramAdapter(token)
