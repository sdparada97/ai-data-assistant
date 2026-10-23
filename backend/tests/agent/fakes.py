"""Modelo de chat con guion para probar el agente sin red.

`GenericFakeChatModel` no implementa `bind_tools` ni `with_structured_output`; esta
subclase sí, y además registra los mensajes que recibe y puede lanzar excepciones
del guion (para simular fallos del proveedor).
"""

from __future__ import annotations

import json
from collections.abc import Iterator, Sequence
from typing import Any

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.runnables import Runnable, RunnableLambda
from pydantic import BaseModel, Field, ValidationError


class ScriptedChatModel(GenericFakeChatModel):
    """Devuelve, en orden, los mensajes (o lanza las excepciones) del guion."""

    received: list[list[BaseMessage]] = Field(default_factory=list)
    bound_tools: list[str] = Field(default_factory=list)
    model: str = "modelo-de-prueba"

    @classmethod
    def from_script(cls, *items: AIMessage | str | BaseException) -> ScriptedChatModel:
        return cls(messages=iter(items))

    def _generate(self, messages: list[BaseMessage], stop: Any = None, run_manager: Any = None, **kwargs: Any) -> ChatResult:
        self.received.append(list(messages))
        item = next(self.messages)
        if isinstance(item, BaseException):
            raise item
        message = AIMessage(content=item) if isinstance(item, str) else item
        return ChatResult(generations=[ChatGeneration(message=message)])

    def bind_tools(self, tools: Sequence[Any], **kwargs: Any) -> ScriptedChatModel:
        self.bound_tools = [tool.name for tool in tools]
        return self

    def with_structured_output(
        self, schema: Any, *, include_raw: bool = False, method: str | None = None, **kwargs: Any
    ) -> Runnable:
        def run(messages: Any) -> Any:
            raw = self.invoke(messages)
            try:
                if raw.tool_calls:
                    data = raw.tool_calls[0]["args"]
                else:
                    data = json.loads(raw.content if isinstance(raw.content, str) else raw.text)
                parsed, error = schema.model_validate(data), None
            except (ValueError, ValidationError) as exc:  # ValueError incluye JSONDecodeError
                parsed, error = None, exc
            if include_raw:
                return {"raw": raw, "parsed": parsed, "parsing_error": error}
            if error is not None:
                raise error
            return parsed

        return RunnableLambda(run)


def tool_call(name: str, args: dict[str, Any], call_id: str) -> dict[str, Any]:
    return {"name": name, "args": args, "id": call_id, "type": "tool_call"}


def plan_message(*calls: dict[str, Any], text: str = "") -> AIMessage:
    """Respuesta del LLM que pide herramientas (el plan)."""
    return AIMessage(content=text, tool_calls=list(calls))


def json_message(model: BaseModel | dict[str, Any]) -> AIMessage:
    data = model.model_dump() if isinstance(model, BaseModel) else model
    return AIMessage(content=json.dumps(data, ensure_ascii=False))


def scripted(items: Iterator[Any]) -> ScriptedChatModel:
    return ScriptedChatModel(messages=items)
