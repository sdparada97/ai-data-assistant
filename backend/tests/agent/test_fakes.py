"""El modelo con guion que usan las pruebas del agente."""

from __future__ import annotations

import pytest
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from .fakes import ScriptedChatModel, json_message, plan_message, tool_call


class _Answer(BaseModel):
    text: str


def test_returns_tool_calls_and_records_messages() -> None:
    model = ScriptedChatModel.from_script(plan_message(tool_call("consultar_metrica", {"metrics": ["x"]}, "c1")))

    message = model.bind_tools([]).invoke([HumanMessage("hola")])

    assert message.tool_calls[0]["name"] == "consultar_metrica"
    assert model.received[0][0].content == "hola"


def test_structured_output_with_include_raw() -> None:
    model = ScriptedChatModel.from_script(json_message({"text": "bien"}), "no es json")
    runnable = model.with_structured_output(_Answer, include_raw=True, method="json_schema")

    ok = runnable.invoke([HumanMessage("a")])
    bad = runnable.invoke([HumanMessage("b")])

    assert ok["parsed"] == _Answer(text="bien") and ok["parsing_error"] is None
    assert bad["parsed"] is None and bad["parsing_error"] is not None


def test_scripted_exception_is_raised() -> None:
    model = ScriptedChatModel.from_script(RuntimeError("fallo simulado"))

    with pytest.raises(RuntimeError, match="fallo simulado"):
        model.invoke([HumanMessage("a")])
