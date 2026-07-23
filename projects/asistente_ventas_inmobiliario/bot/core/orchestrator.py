from __future__ import annotations

import logging
import uuid

from ..adapters.base import IncomingMessage, OutgoingMessage
from .errors import to_user_friendly_message
from .exceptions import BotError, LLMProviderError
from .features import FeatureExtractor
from .message_formatter import NO_RESULTS_MESSAGE, format_search_results
from .models import RankedResult, SearchFilters
from .nlu import ExtractedIntent, Intent, IntentExtractor
from .ranking import rank
from .repository import ApartmentsRepository
from .session import ConversationSession, SessionStore

logger = logging.getLogger(__name__)

_OUT_OF_SCOPE_MESSAGE = (
    "Solo puedo ayudarte a buscar departamentos disponibles. "
    "¿En qué zona y con qué presupuesto estás buscando?"
)
_NO_ACTIVE_SEARCH_MESSAGE = "No tengo una búsqueda activa para continuar. Cuéntame qué tipo de departamento buscas."


class Orchestrator:
    """Coordina el pipeline completo: NLU -> filtros -> repository -> ranking ->
    extracción de características -> formato, y el estado de conversación entre
    turnos. Es el único componente que conoce el pipeline de punta a punta."""

    def __init__(
        self,
        intent_extractor: IntentExtractor,
        repository: ApartmentsRepository,
        feature_extractor: FeatureExtractor,
        session_store: SessionStore,
        page_size: int = 3,
    ) -> None:
        self._intent_extractor = intent_extractor
        self._repository = repository
        self._feature_extractor = feature_extractor
        self._session_store = session_store
        self._page_size = page_size

    async def handle_message(self, message: IncomingMessage) -> OutgoingMessage:
        correlation_id = uuid.uuid4().hex
        try:
            return await self._handle(message)
        except BotError as exc:
            logger.warning("bot_error correlation_id=%s error=%r", correlation_id, exc)
            return OutgoingMessage(chat_id=message.chat_id, text=to_user_friendly_message(exc))
        except Exception as exc:  # último resguardo: nunca filtrar detalles internos al usuario
            logger.exception("unexpected_error correlation_id=%s", correlation_id)
            return OutgoingMessage(chat_id=message.chat_id, text=to_user_friendly_message(exc))

    async def _handle(self, message: IncomingMessage) -> OutgoingMessage:
        session = self._session_store.get(message.channel.value, message.user_id)
        extracted = await self._intent_extractor.extract(message.text, session)

        if extracted.intent == Intent.OUT_OF_SCOPE:
            return OutgoingMessage(chat_id=message.chat_id, text=_OUT_OF_SCOPE_MESSAGE)

        if extracted.intent == Intent.CLARIFICATION_NEEDED:
            question = extracted.clarification_question or _NO_ACTIVE_SEARCH_MESSAGE
            return OutgoingMessage(chat_id=message.chat_id, text=question)

        filters, offset = self._resolve_filters_and_offset(extracted, session)
        if filters is None:
            return OutgoingMessage(chat_id=message.chat_id, text=_NO_ACTIVE_SEARCH_MESSAGE)

        results, has_more = self._repository.search(filters, offset, self._page_size)
        ranked = rank(results, filters)

        self._session_store.save(
            ConversationSession(
                channel=message.channel.value,
                user_id=message.user_id,
                filters=filters,
                offset=offset,
            )
        )

        response_text = await self._build_response(filters, ranked, has_more)
        return OutgoingMessage(chat_id=message.chat_id, text=response_text)

    async def _build_response(self, filters: SearchFilters, ranked: list[RankedResult], has_more: bool) -> str:
        if not ranked:
            return NO_RESULTS_MESSAGE
        try:
            features = await self._feature_extractor.extract([r.apartment.descripcion for r in ranked])
        except LLMProviderError as exc:
            # Las características son opcionales: si la extracción falla, seguimos
            # con el mensaje armado solo desde los amenities estructurados.
            logger.warning("feature_extraction_failed error=%r", exc)
            features = [[] for _ in ranked]
        return format_search_results(filters, ranked, features, has_more)

    def _resolve_filters_and_offset(
        self, extracted: ExtractedIntent, session: ConversationSession | None
    ) -> tuple[SearchFilters | None, int]:
        if extracted.intent == Intent.NEW_SEARCH:
            return extracted.filters, 0

        if session is None or session.filters is None:
            return None, 0

        if extracted.intent == Intent.NEXT_PAGE:
            return session.filters, session.offset + self._page_size

        if extracted.intent == Intent.CHANGE_SORT and extracted.filters is not None:
            # El NLU ya recibe los filtros activos de la sesión como contexto y
            # devuelve el set combinado (no solo el campo sort) — usarlo tal cual
            # en vez de reconstruirlo evita descartar cambios de zona/precio/etc.
            # que el usuario haya mencionado junto con el reordenamiento.
            return extracted.filters, 0

        return session.filters, session.offset
