"""Requisito: Validación de la entrada (lectura del CSV)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from analyst_backend.ingestion.errors import InputError
from analyst_backend.ingestion.pipeline import RAW_COLUMNS, read_sales_csv

WriteCsv = Callable[..., Path]


def test_real_file_reads_all_rows_with_physical_lines(paths: Any) -> None:
    frame = read_sales_csv(paths.real_csv)

    assert len(frame) == 4000
    assert frame["source_line"].iloc[0] == 2
    assert frame.loc[frame["registro_id"] == "V01999", "source_line"].tolist() == [2000, 3998]


def test_missing_file_names_the_path(tmp_path: Path) -> None:
    missing = tmp_path / "no_existe.csv"

    with pytest.raises(InputError, match="no_existe.csv"):
        read_sales_csv(missing)


def test_missing_column_is_named(write_csv: WriteCsv, paths: Any) -> None:
    header = paths.header.replace(",venta_neta_cop", "")

    with pytest.raises(InputError, match="faltan columnas: venta_neta_cop"):
        read_sales_csv(write_csv([{}], header=header))


def test_extra_column_is_named(write_csv: WriteCsv, paths: Any) -> None:
    with pytest.raises(InputError, match="sobran columnas: descuento"):
        read_sales_csv(write_csv([{}], header=paths.header + ",descuento"))


def test_columns_in_another_order_are_accepted(write_csv: WriteCsv, paths: Any, valid_row: dict[str, str]) -> None:
    reordered = ",".join(reversed(paths.header.split(",")))

    frame = read_sales_csv(write_csv([{}], header=reordered))

    assert tuple(frame.columns[:9]) == RAW_COLUMNS
    assert frame.loc[0, "venta_neta_cop"] == valid_row["venta_neta_cop"]


def test_header_only_is_rejected(write_csv: WriteCsv) -> None:
    with pytest.raises(InputError, match="no tiene filas de datos"):
        read_sales_csv(write_csv([]))


def test_row_with_wrong_field_count_names_the_line(tmp_path: Path, paths: Any, valid_row: dict[str, str]) -> None:
    good = ",".join(valid_row.values())
    short = ",".join(list(valid_row.values())[:8])
    path = tmp_path / "ventas.csv"
    path.write_text("\n".join([paths.header, good, good, good, short]) + "\n", encoding="utf-8")

    with pytest.raises(InputError, match="línea 5"):
        read_sales_csv(path)


def test_latin1_file_is_rejected(tmp_path: Path, paths: Any, valid_row: dict[str, str]) -> None:
    path = tmp_path / "ventas.csv"
    path.write_bytes((paths.header + "\n" + ",".join({**valid_row, "marca": "Brío"}.values()) + "\n").encode("latin-1"))

    with pytest.raises(InputError, match="no es UTF-8"):
        read_sales_csv(path)
