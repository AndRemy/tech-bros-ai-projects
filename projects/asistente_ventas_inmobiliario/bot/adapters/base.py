from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Awaitable, Callable

from pydantic import BaseModel


class Channel(str, Enum):
    TELEGRAM = "telegram"
    DISCORD = "discord"


class IncomingMessage(BaseModel):
    channel: Channel
    user_id: str
    chat_id: str
    text: str


class OutgoingMessage(BaseModel):
    chat_id: str
    text: str


MessageHandler = Callable[[IncomingMessage], Awaitable[OutgoingMessage]]


class ChannelAdapter(ABC):
    """Puerto que traduce entre la API nativa de un canal y los mensajes genéricos
    del bot. El Orchestrator solo conoce IncomingMessage/OutgoingMessage."""

    @abstractmethod
    async def start(self, on_message: MessageHandler) -> None:
        """Empieza a escuchar el canal (polling o webhook) y llama a on_message
        por cada mensaje entrante, enviando la respuesta que este devuelva."""

    @abstractmethod
    async def send(self, message: OutgoingMessage) -> None:
        """Envía un mensaje fuera de la respuesta directa a on_message,
        por ejemplo un mensaje proactivo o de seguimiento."""
