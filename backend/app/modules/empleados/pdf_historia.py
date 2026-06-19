"""Generate PDF for historia clinica using ReportLab."""
from __future__ import annotations

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.modules.empleados.historia_clinica import HistoriaClinicaOut

_PAGE_W, _PAGE_H = A4
_MARGIN = 1.5 * cm


def generate_pdf(hc: HistoriaClinicaOut) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=_MARGIN,
        rightMargin=_MARGIN,
        topMargin=_MARGIN,
        bottomMargin=_MARGIN,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "HCTitle",
        parent=styles["Heading1"],
        fontSize=16,
        spaceAfter=6,
        textColor=colors.HexColor("#1a365d"),
    )
    h2_style = ParagraphStyle(
        "HCH2",
        parent=styles["Heading2"],
        fontSize=13,
        spaceBefore=14,
        spaceAfter=6,
        textColor=colors.HexColor("#2c5282"),
    )
    h3_style = ParagraphStyle(
        "HCH3",
        parent=styles["Heading3"],
        fontSize=11,
        spaceBefore=8,
        spaceAfter=4,
        textColor=colors.HexColor("#2d3748"),
    )
    normal = styles["Normal"]
    small = ParagraphStyle("HCSmall", parent=normal, fontSize=8, textColor=colors.gray)

    elements: list = []

    # --- Header ---
    elements.append(Paragraph("Historia Clinica", title_style))
    elements.append(Paragraph("Medicina Laboral - Villa Allende", normal))
    elements.append(Spacer(1, 0.5 * cm))

    # --- Empleado ---
    emp = hc.empleado
    elements.append(Paragraph("Datos del empleado", h2_style))
    emp_data = [
        ["Apellido y nombre", f"{emp.apellido}, {emp.nombre}"],
        ["Legajo", emp.legajo],
        ["CUIL", emp.cuil],
        ["Fecha nacimiento", str(emp.fecha_nacimiento) if emp.fecha_nacimiento else "—"],
        ["Fecha ingreso", str(emp.fecha_ingreso)],
        ["Estado", "Activo" if emp.activo else "Inactivo"],
    ]
    t = Table(emp_data, colWidths=[5 * cm, 12 * cm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.lightgrey),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.4 * cm))

    # --- Licencias ---
    if hc.licencias:
        elements.append(Paragraph("Licencias", h2_style))
        lic_header = ["Fecha desde", "Fecha hasta", "Tipo", "Diagnostico", "Dias", "Estado"]
        lic_rows = [lic_header]
        for lic in hc.licencias:
            lic_rows.append([
                str(lic.fecha_desde),
                str(lic.fecha_hasta),
                lic.tipo_licencia_nombre or "—",
                lic.diagnostico or "—",
                str(lic.dias_otorgados if lic.dias_otorgados is not None else lic.dias_solicitados),
                lic.estado.value if hasattr(lic.estado, "value") else str(lic.estado),
            ])
        col_w = [2.5 * cm, 2.5 * cm, 3.5 * cm, 4 * cm, 1.5 * cm, 2.5 * cm]
        t = Table(lic_rows, colWidths=col_w, repeatRows=1)
        t.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#edf2f7")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 0.4 * cm))

    # --- Atenciones ---
    if hc.atenciones:
        elements.append(Paragraph("Atenciones", h2_style))
        for ad in hc.atenciones:
            a = ad.atencion
            fecha_str = a.fecha_turno.strftime("%d/%m/%Y %H:%M") if isinstance(a.fecha_turno, datetime) else str(a.fecha_turno)
            elements.append(Paragraph(
                f"Atencion del {fecha_str} — {a.motivo}",
                h3_style,
            ))
            info_lines = [f"<b>Estado:</b> {a.estado}"]
            if a.notas_medicas:
                info_lines.append(f"<b>Notas medicas:</b> {a.notas_medicas}")
            for line in info_lines:
                elements.append(Paragraph(line, normal))

            # Signos vitales
            if ad.signos_vitales:
                sv = ad.signos_vitales
                sv_parts = []
                if sv.peso_kg is not None:
                    sv_parts.append(f"Peso: {sv.peso_kg} kg")
                if sv.altura_cm is not None:
                    sv_parts.append(f"Altura: {sv.altura_cm} cm")
                if sv.imc is not None:
                    sv_parts.append(f"IMC: {sv.imc}")
                if sv.presion_sistolica is not None and sv.presion_diastolica is not None:
                    sv_parts.append(f"PA: {sv.presion_sistolica}/{sv.presion_diastolica}")
                if sv.temperatura is not None:
                    sv_parts.append(f"Temp: {sv.temperatura}")
                if sv.frecuencia_cardiaca is not None:
                    sv_parts.append(f"FC: {sv.frecuencia_cardiaca}")
                if sv.saturacion_o2 is not None:
                    sv_parts.append(f"SpO2: {sv.saturacion_o2}%")
                if sv.glucemia is not None:
                    sv_parts.append(f"Glucemia: {sv.glucemia}")
                if sv_parts:
                    elements.append(Paragraph(
                        f"<b>Signos vitales:</b> {' | '.join(sv_parts)}",
                        normal,
                    ))

            # Evoluciones
            for ev in ad.evoluciones:
                elements.append(Paragraph(f"<b>Evolucion — Motivo:</b> {ev.motivo_consulta}", normal))
                if ev.anamnesis:
                    elements.append(Paragraph(f"Anamnesis: {ev.anamnesis}", normal))
                if ev.examen_fisico:
                    elements.append(Paragraph(f"Examen fisico: {ev.examen_fisico}", normal))
                if ev.diagnostico_presuntivo:
                    elements.append(Paragraph(f"Dx presuntivo: {ev.diagnostico_presuntivo}", normal))
                if ev.diagnostico_definitivo:
                    elements.append(Paragraph(f"Dx definitivo: {ev.diagnostico_definitivo}", normal))
                if ev.tratamiento:
                    elements.append(Paragraph(f"Tratamiento: {ev.tratamiento}", normal))
                if ev.observaciones:
                    elements.append(Paragraph(f"Obs: {ev.observaciones}", normal))

            # Recetas
            for rec in ad.recetas:
                items_str = ", ".join(
                    f"{it.medicamento}" + (f" ({it.dosis})" if it.dosis else "")
                    for it in rec.items
                )
                elements.append(Paragraph(
                    f"<b>Receta:</b> {items_str}" + (f" — {rec.diagnostico}" if rec.diagnostico else ""),
                    normal,
                ))

            # Pedidos
            for ped in ad.pedidos:
                items_str = ", ".join(it.descripcion for it in ped.items)
                elements.append(Paragraph(
                    f"<b>Pedido ({ped.tipo}):</b> {items_str}" + (f" — {ped.diagnostico}" if ped.diagnostico else ""),
                    normal,
                ))

            elements.append(Spacer(1, 0.3 * cm))

    # --- Footer ---
    elements.append(Spacer(1, 1 * cm))
    elements.append(Paragraph(
        f"Documento generado por sistema — {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        small,
    ))

    doc.build(elements)
    return buf.getvalue()
