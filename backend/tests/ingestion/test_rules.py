"""Requisitos de las reglas que actúan: DQ01, DQ03, DQ04, DQ05, DQ06, DQ07, DQ08 y DQ13.

Cada regla se prueba aislada. El destino final y la ``action`` de los errores se
prueban en test_pipeline.py.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from analyst_backend.ingestion import rules
from analyst_backend.ingestion.catalog import load_catalog
from analyst_backend.ingestion.pipeline import read_sales_csv

WriteCsv = Callable[..., Path]


@pytest.fixture
def frame_of(write_csv: WriteCsv) -> Callable[..., pd.DataFrame]:
    """Lee filas sintéticas con el lector real y aplica DQ03 (como hace el pipeline)."""

    def _frame(*rows: dict[str, str]) -> pd.DataFrame:
        trimmed = rules.trim_whitespace(read_sales_csv(write_csv(list(rows)))).frame
        assert trimmed is not None
        return trimmed

    return _frame


@pytest.fixture(scope="module")
def real_frame() -> pd.DataFrame:
    root = Path(__file__).resolve().parents[3]
    return read_sales_csv(root / "data/raw/02_Ventas_2026.csv")


def _by_id(issues: list[rules.Issue], registro_id: str) -> list[rules.Issue]:
    return [i for i in issues if i.registro_id == registro_id]


# --- Contrato común ---------------------------------------------------------------


def test_issue_details_serialise_to_json() -> None:
    issue = rules.Issue("V1", 2, "DQ08", "valor_negativo", rules.ERROR, details={"columns": ["unidades"]})

    assert json.loads(issue.details_json() or "") == {"columns": ["unidades"]}
    assert rules.Issue("V1", 2, "DQ05", "mes_invalido", rules.ERROR).details_json() is None


def test_fixed_actions_by_severity() -> None:
    assert rules.Issue("V1", 2, "DQ03", "t", rules.CORRECTION).action == "corregida"
    assert rules.Issue("V1", 2, "DQ11", "t", rules.WARNING).action == "ninguna"
    assert rules.Issue("V1", 2, "DQ05", "t", rules.ERROR).action is None


# --- DQ03 -------------------------------------------------------------------------


def test_dq03_real_file_trims_region_and_channel(real_frame: pd.DataFrame) -> None:
    result = rules.trim_whitespace(real_frame)
    assert result.frame is not None
    trimmed = result.frame.set_index("registro_id")

    assert trimmed.at["V02929", "region"] == "Sur"
    assert trimmed.at["V02612", "canal"] == "Moderno"
    assert [(i.registro_id, i.column_name, i.original_value, i.new_value, i.action) for i in result.issues] == [
        ("V02612", "canal", "Moderno ", "Moderno", "corregida"),
        ("V02929", "region", "Sur ", "Sur", "corregida"),
    ]
    assert not result.mask.any()


def test_dq03_keeps_inner_spaces(write_csv: WriteCsv) -> None:
    result = rules.trim_whitespace(read_sales_csv(write_csv([{"punto_venta_id": " NO T 001 "}])))
    assert result.frame is not None

    assert result.frame.at[0, "punto_venta_id"] == "NO T 001"


# --- DQ01 -------------------------------------------------------------------------


def test_dq01_real_file_identical_duplicate(real_frame: pd.DataFrame) -> None:
    result = rules.find_duplicates(real_frame)

    assert result.mask.sum() == 1
    assert real_frame.loc[result.mask, "source_line"].tolist() == [3998]
    (issue,) = result.issues
    assert (issue.registro_id, issue.source_line, issue.issue_type) == ("V01999", 3998, "duplicado_identico")
    assert issue.details == {"kept_source_line": 2000, "differences": {}}


def test_dq01_duplicate_with_differences(frame_of: Callable[..., pd.DataFrame]) -> None:
    frame = frame_of({"registro_id": "V00001", "unidades": "250"}, {"registro_id": "V00001", "unidades": "260"})

    result = rules.find_duplicates(frame)

    assert frame.loc[~result.mask, "unidades"].tolist() == ["250"]
    (issue,) = result.issues
    assert issue.source_line == 3
    assert issue.issue_type == "duplicado_con_diferencias"
    assert issue.details == {"kept_source_line": 2, "differences": {"unidades": ["250", "260"]}}


def test_dq01_compares_after_trimming(frame_of: Callable[..., pd.DataFrame]) -> None:
    frame = frame_of({"registro_id": "V00001", "region": "Sur"}, {"registro_id": " V00001", "region": "Sur "})

    (issue,) = rules.find_duplicates(frame).issues

    assert issue.issue_type == "duplicado_identico"


# --- DQ04 -------------------------------------------------------------------------


def test_dq04_real_file_normalises_brand(real_frame: pd.DataFrame, paths: Any) -> None:
    trimmed = rules.trim_whitespace(real_frame).frame
    assert trimmed is not None

    result = rules.apply_catalog(trimmed, load_catalog(paths.semantic_layer))
    assert result.frame is not None

    assert result.frame.loc[result.frame["registro_id"] == "V00667", "marca"].tolist() == ["Brio"]
    assert [(i.registro_id, i.column_name, i.original_value, i.new_value, i.action) for i in result.issues] == [
        ("V00667", "marca", "BRIO", "Brio", "corregida")
    ]
    assert not result.mask.any()


def test_dq04_value_outside_catalog_is_retained(frame_of: Callable[..., pd.DataFrame], paths: Any) -> None:
    result = rules.apply_catalog(frame_of({"region": "Caribe"}), load_catalog(paths.semantic_layer))

    assert result.mask.tolist() == [True]
    (issue,) = result.issues
    assert (issue.issue_type, issue.column_name, issue.original_value) == ("valor_no_valido", "region", "Caribe")
    assert issue.action is None  # la decide el destino (en_revision)


def test_dq04_catalog_comes_from_configuration(
    frame_of: Callable[..., pd.DataFrame], paths: Any, tmp_path: Path
) -> None:
    custom = tmp_path / "semantic_layer.yaml"
    custom.write_text(
        paths.semantic_layer.read_text(encoding="utf-8").replace("Occidente]", "Occidente, Caribe]"),
        encoding="utf-8",
    )

    result = rules.apply_catalog(frame_of({"region": "Caribe"}), load_catalog(custom))

    assert result.mask.tolist() == [False]
    assert result.issues == []


# --- DQ05 -------------------------------------------------------------------------


def test_dq05_real_file_month_13(real_frame: pd.DataFrame) -> None:
    result = rules.check_month(real_frame)

    assert real_frame.loc[result.mask, "registro_id"].tolist() == ["V03999"]
    (issue,) = result.issues
    assert (issue.issue_type, issue.column_name, issue.original_value) == ("mes_invalido", "mes", "2026-13")


@pytest.mark.parametrize(("month", "invalid"), [("2025-12", False), ("2026-1", True), ("2026-00", True), ("", True)])
def test_dq05_month_format(frame_of: Callable[..., pd.DataFrame], month: str, invalid: bool) -> None:
    assert rules.check_month(frame_of({"mes": month})).mask.tolist() == [invalid]


# --- DQ06 -------------------------------------------------------------------------


def test_dq06_real_file_empty_units(real_frame: pd.DataFrame) -> None:
    result = rules.check_units(real_frame)

    assert real_frame.loc[result.mask, "registro_id"].tolist() == ["V03358"]
    (issue,) = result.issues
    assert (issue.issue_type, issue.column_name, issue.original_value) == ("unidades_faltantes", "unidades", "")


def test_dq06_non_integer_units(frame_of: Callable[..., pd.DataFrame]) -> None:
    result = rules.check_units(frame_of({"unidades": "12.5"}, {"unidades": "1e3"}, {"unidades": "-3"}))

    assert result.mask.tolist() == [True, True, False]


# --- DQ07 -------------------------------------------------------------------------


def test_dq07_real_file_not_available_sales(real_frame: pd.DataFrame) -> None:
    result = rules.check_sales(real_frame)

    assert real_frame.loc[result.mask, "registro_id"].tolist() == ["V03997"]
    (issue,) = result.issues
    assert (issue.issue_type, issue.column_name, issue.original_value) == ("venta_faltante", "venta_neta_cop", "N/D")


# --- DQ08 -------------------------------------------------------------------------


def test_dq08_real_file_single_issue_for_two_negative_columns(real_frame: pd.DataFrame) -> None:
    result = rules.check_negative(real_frame)

    assert real_frame.loc[result.mask, "registro_id"].tolist() == ["V03998"]
    (issue,) = result.issues
    assert issue.issue_type == "valor_negativo"
    assert issue.details == {"columns": ["unidades", "venta_neta_cop"]}


def test_dq08_zero_is_not_negative(frame_of: Callable[..., pd.DataFrame]) -> None:
    result = rules.check_negative(frame_of({"unidades": "0", "venta_neta_cop": "0"}))

    assert result.mask.tolist() == [False]
    assert result.issues == []


# --- DQ13 -------------------------------------------------------------------------


def test_dq13_positive_sales_with_zero_units(frame_of: Callable[..., pd.DataFrame]) -> None:
    result = rules.check_sales_without_units(
        frame_of(
            {"unidades": "0", "venta_neta_cop": "1200000"},
            {"unidades": "5", "venta_neta_cop": "0"},
            {"unidades": "0", "venta_neta_cop": "0"},
            {"unidades": "0", "venta_neta_cop": "N/D"},
        )
    )

    assert result.mask.tolist() == [True, False, False, False]
    (issue,) = result.issues
    assert (issue.issue_type, issue.column_name, issue.original_value) == ("venta_sin_unidades", "unidades", "0")


def test_dq13_no_cases_in_real_file(real_frame: pd.DataFrame) -> None:
    assert rules.check_sales_without_units(real_frame).issues == []
