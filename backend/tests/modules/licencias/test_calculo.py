from datetime import date

import pytest

from app.modules.licencias.calculo import calcular_dias, ventana_para


def test_calcular_dias_dia_unico():
    assert calcular_dias(date(2026, 5, 10), date(2026, 5, 10)) == 1


def test_calcular_dias_rango_normal():
    assert calcular_dias(date(2026, 5, 10), date(2026, 5, 20)) == 11


def test_calcular_dias_rango_invalido():
    with pytest.raises(ValueError):
        calcular_dias(date(2026, 5, 20), date(2026, 5, 10))


def test_calcular_dias_anio_bisiesto():
    # 2024 es bisiesto; feb 28 -> mar 1 son 3 dias corridos
    assert calcular_dias(date(2024, 2, 28), date(2024, 3, 1)) == 3


def test_ventana_calendario():
    assert ventana_para("anio-calendario", fecha_ingreso=date(2020, 7, 1), fecha_ref=date(2026, 6, 15)) == (
        date(2026, 1, 1), date(2026, 12, 31)
    )


def test_ventana_aniversario():
    # ingreso 1-feb-2020, fecha_ref 15-jun-2026 -> ventana 1-feb-2026 a 31-ene-2027
    assert ventana_para("anio-aniversario", fecha_ingreso=date(2020, 2, 1), fecha_ref=date(2026, 6, 15)) == (
        date(2026, 2, 1), date(2027, 1, 31)
    )
