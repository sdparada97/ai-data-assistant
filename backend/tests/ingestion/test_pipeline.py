"""Requisitos: Destino único por fila, Acción e impacto de cada incidencia, Filas en
revisión, DQ11, DQ12 e Incidencias del archivo real."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from analyst_backend.ingestion.catalog import QualityConfig, load_catalog, load_quality_config
from analyst_backend.ingestion.pipeline import RulesOutcome, apply_rules, read_sales_csv

WriteCsv = Callable[..., Path]


@pytest.fixture(scope="module")
def real(paths: Any) -> RulesOutcome:
    return apply_rules(
        read_sales_csv(paths.real_csv), load_catalog(paths.semantic_layer), load_quality_config(paths.data_quality)
    )


@pytest.fixture
def run(write_csv: WriteCsv, paths: Any) -> Callable[..., RulesOutcome]:
    def _run(*rows: dict[str, str], threshold: float = 0.5, semantic_layer: Path | None = None) -> RulesOutcome:
        catalog = load_catalog(semantic_layer or paths.semantic_layer)
        return apply_rules(read_sales_csv(write_csv(list(rows))), catalog, QualityConfig(threshold))

    return _run


def _issues(outcome: RulesOutcome, rule_code: str) -> pd.DataFrame:
    return outcome.issues[outcome.issues["rule_code"] == rule_code]


# --- Destino único por fila ----------------------------------------------------------


def test_invalid_month_and_missing_sales_is_excluded(run: Callable[..., RulesOutcome]) -> None:
    outcome = run({"registro_id": "V00001", "mes": "2026-13", "venta_neta_cop": "N/D"})

    assert outcome.destinations.tolist() == ["excluida"]
    assert outcome.sales.empty and outcome.review.empty
    line_errors = outcome.issues[(outcome.issues["source_line"] == 2) & (outcome.issues["severity"] == "error")]
    assert sorted(line_errors["rule_code"]) == ["DQ05", "DQ07"]


def test_every_row_has_exactly_one_destination(real: RulesOutcome) -> None:
    counts = real.counts()

    assert counts == {"rows_read": 4000, "rows_sales": 3995, "rows_review": 2, "rows_excluded": 2, "rows_removed": 1}


# --- Acción e impacto de cada incidencia ----------------------------------------------


def test_error_actions_follow_final_destination(run: Callable[..., RulesOutcome]) -> None:
    outcome = run({"mes": "2026-13", "venta_neta_cop": "N/D"})
    errors = outcome.issues[outcome.issues["rule_code"].isin(["DQ05", "DQ07"])]

    assert errors["action"].tolist() == ["excluida", "excluida"]
    assert errors["affected_net_sales_cop"].isna().all()


def test_negative_sales_impact_is_recorded(real: RulesOutcome) -> None:
    (impact,) = _issues(real, "DQ08")["affected_net_sales_cop"].tolist()

    assert impact == -1000000


def test_actions_by_severity_in_real_file(real: RulesOutcome) -> None:
    actions = real.issues.groupby("severity")["action"].unique().map(sorted).to_dict()

    assert actions == {
        "aviso": ["ninguna"],
        "correccion": ["corregida"],
        "error": ["eliminada", "en_revision", "excluida"],
    }


# --- Filas en revisión -----------------------------------------------------------------


def test_real_review_rows_keep_original_values(real: RulesOutcome) -> None:
    review = real.review.set_index("registro_id")

    assert sorted(review.index) == ["V03998", "V03999"]
    assert review.at["V03999", "rule_codes"] == "DQ05"
    assert review.at["V03999", "mes"] == "2026-13"
    assert "2026-13" in review.at["V03999", "reason"]
    assert review.at["V03998", "rule_codes"] == "DQ08"
    assert review.at["V03998", "unidades"] == "-90"
    assert set(review["status"]) == {"en_revision"}
    assert not set(review.index) & set(real.sales["registro_id"])


def test_review_lists_every_retaining_rule(run: Callable[..., RulesOutcome]) -> None:
    outcome = run({"region": "Caribe", "unidades": "-5"})

    assert outcome.review["rule_codes"].tolist() == ["DQ04,DQ08"]


def test_review_keeps_untrimmed_values(run: Callable[..., RulesOutcome]) -> None:
    outcome = run({"region": "Caribe "})

    assert outcome.review["region"].tolist() == ["Caribe "]


# --- DQ11 ---------------------------------------------------------------------------------


def test_dq11_real_single_points_of_sale(real: RulesOutcome) -> None:
    warnings = _issues(real, "DQ11")

    assert sorted(warnings["original_value"]) == ["CE-M-014", "CE-T-015", "SU-T-013"]
    assert set(warnings["action"]) == {"ninguna"}
    assert [json.loads(d) for d in warnings["details"]] == [{"occurrences": 1, "median_occurrences": 30}] * 3


def test_dq11_does_not_change_destination(run: Callable[..., RulesOutcome]) -> None:
    outcome = run({"punto_venta_id": "NO-T-001"}, {"punto_venta_id": "NO-T-001"}, {"punto_venta_id": "SU-T-099"})

    assert len(_issues(outcome, "DQ11")) == 1
    assert len(outcome.sales) == 3


# --- DQ12 ---------------------------------------------------------------------------------

SCALE_ROWS = (
    {"unidades": "100", "venta_neta_cop": "1230000"},
    {"unidades": "200", "venta_neta_cop": "2460000"},
    {"unidades": "300", "venta_neta_cop": "3690000"},
    {"unidades": "310", "venta_neta_cop": "3810"},
)


def test_dq12_no_warnings_in_real_file(real: RulesOutcome) -> None:
    assert _issues(real, "DQ12").empty


def test_dq12_scale_error_is_flagged_but_kept(run: Callable[..., RulesOutcome]) -> None:
    outcome = run(*SCALE_ROWS, threshold=0.5)

    (warning,) = _issues(outcome, "DQ12").to_dict("records")
    details = json.loads(warning["details"])
    assert warning["source_line"] == 5
    assert warning["action"] == "ninguna"
    assert details["unit_price"] == pytest.approx(12.2903, abs=1e-3)
    assert details["median_unit_price"] == pytest.approx(12300)
    assert details["deviation"] > 0.99
    assert len(outcome.sales) == 4


def test_dq12_threshold_comes_from_configuration(run: Callable[..., RulesOutcome]) -> None:
    assert _issues(run(*SCALE_ROWS, threshold=1.0), "DQ12").empty


# --- Incidencias del archivo real -----------------------------------------------------------


def test_real_file_issue_distribution(real: RulesOutcome) -> None:
    by_rule = real.issues.groupby("rule_code").size().to_dict()

    assert by_rule == {"DQ01": 1, "DQ03": 2, "DQ04": 1, "DQ05": 1, "DQ06": 1, "DQ07": 1, "DQ08": 1, "DQ11": 3}
    assert len(real.issues) == 11


# --- Destino final y THEN completos de cada regla (resultado de la carga) ---------------


def _issue(outcome: RulesOutcome, rule_code: str, registro_id: str) -> dict[str, Any]:
    (record,) = outcome.issues[
        (outcome.issues["rule_code"] == rule_code) & (outcome.issues["registro_id"] == registro_id)
    ].to_dict("records")
    return record


def test_dq01_first_occurrence_invalid_keeps_id_out_of_sales(run: Callable[..., RulesOutcome]) -> None:
    outcome = run({"registro_id": "V00001", "mes": "2026-13"}, {"registro_id": "V00001"})

    assert outcome.destinations.tolist() == ["en_revision", "eliminada"]
    assert outcome.review["registro_id"].tolist() == ["V00001"]
    assert "V00001" not in set(outcome.sales["registro_id"])


def test_dq01_real_duplicate_full_then(real: RulesOutcome) -> None:
    issue = _issue(real, "DQ01", "V01999")
    sales = real.sales[real.sales["registro_id"] == "V01999"]

    assert (issue["source_line"], issue["issue_type"], issue["action"]) == (3998, "duplicado_identico", "eliminada")
    assert issue["affected_net_sales_cop"] == 1142900
    assert json.loads(issue["details"])["kept_source_line"] == 2000
    assert sales["source_line"].tolist() == [2000]


def test_dq03_real_corrected_rows_reach_sales(real: RulesOutcome) -> None:
    sales = real.sales.set_index("registro_id")

    assert sales.at["V02929", "region"] == "Sur"
    assert sales.at["V02612", "canal"] == "Moderno"
    assert _issue(real, "DQ03", "V02929")["action"] == "corregida"


def test_dq04_real_brand_reaches_sales(real: RulesOutcome) -> None:
    assert real.sales.set_index("registro_id").at["V00667", "marca"] == "Brio"
    assert _issue(real, "DQ04", "V00667")["action"] == "corregida"


def test_dq04_value_outside_catalog_full_then(run: Callable[..., RulesOutcome]) -> None:
    outcome = run({"registro_id": "V00001", "region": "Caribe"})
    issue = _issue(outcome, "DQ04", "V00001")

    assert outcome.review["rule_codes"].tolist() == ["DQ04"]
    assert outcome.sales.empty
    assert (issue["issue_type"], issue["column_name"], issue["action"]) == ("valor_no_valido", "region", "en_revision")


def test_dq04_configured_value_reaches_sales(
    run: Callable[..., RulesOutcome], paths: Any, tmp_path: Path
) -> None:
    custom = tmp_path / "semantic_layer.yaml"
    custom.write_text(
        paths.semantic_layer.read_text(encoding="utf-8").replace("Occidente]", "Occidente, Caribe]"),
        encoding="utf-8",
    )

    outcome = run({"region": "Caribe"}, semantic_layer=custom)

    assert outcome.sales["region"].tolist() == ["Caribe"]


def test_dq05_real_full_then(real: RulesOutcome) -> None:
    issue = _issue(real, "DQ05", "V03999")

    assert (issue["action"], issue["affected_net_sales_cop"]) == ("en_revision", 1470000)


def test_dq05_valid_month_outside_semester_reaches_sales(run: Callable[..., RulesOutcome]) -> None:
    assert run({"mes": "2025-12"}).sales["mes"].tolist() == ["2025-12"]


def test_dq06_real_full_then(real: RulesOutcome) -> None:
    issue = _issue(real, "DQ06", "V03358")

    assert (issue["action"], issue["affected_net_sales_cop"]) == ("excluida", 935000)
    assert "V03358" not in set(real.sales["registro_id"]) | set(real.review["registro_id"])


def test_dq07_real_full_then(real: RulesOutcome) -> None:
    issue = _issue(real, "DQ07", "V03997")

    assert (issue["original_value"], issue["action"]) == ("N/D", "excluida")
    assert pd.isna(issue["affected_net_sales_cop"])
    assert "V03997" not in set(real.sales["registro_id"]) | set(real.review["registro_id"])


def test_dq08_zero_values_reach_sales(run: Callable[..., RulesOutcome]) -> None:
    outcome = run({"unidades": "0", "venta_neta_cop": "0"})

    assert len(outcome.sales) == 1
    assert _issues(outcome, "DQ08").empty


def test_dq13_full_then(run: Callable[..., RulesOutcome]) -> None:
    outcome = run({"registro_id": "V00001", "unidades": "0", "venta_neta_cop": "1200000"})
    issue = _issue(outcome, "DQ13", "V00001")

    assert outcome.review["rule_codes"].tolist() == ["DQ13"]
    assert (issue["action"], issue["affected_net_sales_cop"]) == ("en_revision", 1200000)


def test_dq13_zero_sales_with_units_reaches_sales(run: Callable[..., RulesOutcome]) -> None:
    outcome = run({"unidades": "5", "venta_neta_cop": "0"})

    assert len(outcome.sales) == 1
    assert _issues(outcome, "DQ13").empty


def test_dq01_duplicate_with_differences_keeps_line_2_in_sales(run: Callable[..., RulesOutcome]) -> None:
    outcome = run({"registro_id": "V00001", "unidades": "250"}, {"registro_id": "V00001", "unidades": "260"})

    assert outcome.sales[["registro_id", "source_line", "unidades"]].values.tolist() == [["V00001", 2, 250]]
    assert outcome.destinations.tolist() == ["sales", "eliminada"]


def test_dq06_non_integer_units_full_then(run: Callable[..., RulesOutcome]) -> None:
    outcome = run({"unidades": "12.5"})

    assert outcome.destinations.tolist() == ["excluida"]
    assert len(_issues(outcome, "DQ06")) == 1


def test_dq12_groups_with_zero_median_are_not_evaluated(run: Callable[..., RulesOutcome]) -> None:
    outcome = run(
        {"unidades": "10", "venta_neta_cop": "0"},
        {"unidades": "20", "venta_neta_cop": "0"},
        {"unidades": "30", "venta_neta_cop": "5"},
    )

    assert len(outcome.sales) == 3
    assert _issues(outcome, "DQ12").empty
