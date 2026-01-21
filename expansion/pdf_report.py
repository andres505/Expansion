from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Image, Spacer
)
from reportlab.lib.units import cm
import numpy as np
import os


# ======================================================
# COLORES
# ======================================================
NETO_BLUE = HexColor("#0B2C4D")
NETO_ORANGE = HexColor("#F37021")
LIGHT_GREY = HexColor("#F4F4F4")

GREEN_BG = HexColor("#DFF2E1")
GREEN_TX = HexColor("#1E7F43")
YELLOW_BG = HexColor("#FFF4CC")
YELLOW_TX = HexColor("#9A7B00")
RED_BG = HexColor("#FDE2E2")
RED_TX = HexColor("#9B1C1C")


# ======================================================
# UTILIDADES
# ======================================================
def _decision_colors(decision: str):
    d = decision.upper()
    if d == "AVANZAR":
        return GREEN_BG, GREEN_TX
    if d == "EVALUAR":
        return YELLOW_BG, YELLOW_TX
    return RED_BG, RED_TX


def _fmt(val):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "-"
    if isinstance(val, (int, float)):
        return f"{int(val):,}".replace(",", ".")
    return str(val)


def _build_styles():
    styles = getSampleStyleSheet()

    def add(ps):
        if ps.name not in styles.byName:
            styles.add(ps)

    add(ParagraphStyle("NetoTitle", fontSize=18, textColor=NETO_BLUE))
    add(ParagraphStyle("NetoSubtitle", fontSize=10, textColor=NETO_ORANGE))
    add(ParagraphStyle("NetoHeader", fontSize=12, textColor=NETO_BLUE))
    add(ParagraphStyle("NetoBody", fontSize=9))
    add(ParagraphStyle("NetoSmall", fontSize=8))

    return styles


def _build_tienda_cercana_rows(payload: dict):
    return [
        ["ID tienda", _fmt(payload.get("id_tienda_cercana"))],
        ["Distancia (km)", _fmt(payload.get("distancia_tienda_cercana_km"))],
        ["Ventas sin impuestos", _fmt(payload.get("tienda_cercanaVenta_Sin_Impuestos"))],
        ["Transacciones", _fmt(payload.get("tienda_cercanaTransacciones"))],
        ["Ticket promedio", _fmt(payload.get("tienda_cercanaTicket_Promedio"))],
        ["Prom. monto sin imp.", _fmt(payload.get("tienda_cercanaProm_Monto_Sin_Imp"))],
    ]


# ======================================================
# FUNCIÓN PRINCIPAL
# ======================================================
def generate_expansion_pdf(
    *,
    payload: dict,
    df_benchmark,
    decision_modelo_1: dict,
    decision_modelo_2: dict,
    output_path: str,
    logo_path: str,
    site_image_path: str | None = None
):

    styles = _build_styles()

    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(A4),
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm
    )

    story = []

    # ================= HEADER =================
    logo = Image(logo_path, width=3.8 * cm, height=3.8 * cm)

    title = Paragraph("Evaluación de sitio – Expansión NETO", styles["NetoTitle"])

    subtitle = Paragraph(
        f"""
        Folio: <b>{payload.get("id_ubicacion","-")}</b> &nbsp;|&nbsp;
        Región: <b>{payload.get("region","-")}</b> &nbsp;|&nbsp;
        Estado: <b>{payload.get("estado","-")}</b><br/>
        Dirección: {payload.get("direccion","-")}<br/>
        Tipo de operación: {payload.get("tipo_operacion","-")}
        """,
        styles["NetoSubtitle"]
    )

    header = Table([[logo, title]], colWidths=[4.5 * cm, 22 * cm])
    header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))

    story += [header, subtitle, Spacer(1, 8)]

    story.append(Table(
        [[""]],
        colWidths=[27 * cm],
        rowHeights=[0.25 * cm],
        style=[("BACKGROUND", (0, 0), (-1, -1), NETO_ORANGE)]
    ))

    story.append(Spacer(1, 12))

    # ================= TIENDA CERCANA (AL PRINCIPIO) =================
    story.append(Paragraph("Tienda NETO más cercana", styles["NetoHeader"]))

    tienda_rows = [["Variable", "Valor"]] + _build_tienda_cercana_rows(payload)

    tienda_table = Table(
        tienda_rows,
        colWidths=[10 * cm, 10 * cm]
    )

    tienda_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NETO_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("GRID", (0, 0), (-1, -1), 0.25, black),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))

    story.append(tienda_table)
    story.append(Spacer(1, 14))

    # ================= BENCHMARK =================
    story.append(Paragraph("Comparativo sitio vs benchmark regional", styles["NetoHeader"]))

    data = [["Variable", "Benchmark", "Sitio", "Δ vs benchmark"]]
    for _, r in df_benchmark.iterrows():
        data.append([
            r["Variable"],
            _fmt(r["Benchmark regional"]),
            _fmt(r["Punto candidato"]),
            f'{int(r["Δ vs benchmark (%)"])}%' if r["Δ vs benchmark (%)"] == r["Δ vs benchmark (%)"] else "-"
        ])

    table = Table(data, colWidths=[9*cm, 6*cm, 6*cm, 5*cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), NETO_BLUE),
        ("TEXTCOLOR", (0,0), (-1,0), white),
        ("GRID", (0,0), (-1,-1), 0.25, black),
        ("PADDING", (0,0), (-1,-1), 6),
    ]))

    story.append(table)
    story.append(Spacer(1, 12))

    # ================= IMAGEN =================
    if site_image_path and os.path.exists(site_image_path):
        img = Image(site_image_path, width=24*cm, height=10*cm)
        img.hAlign = "CENTER"
        story.append(img)
        story.append(Spacer(1, 12))

    # ================= DECISIONES =================
    story.append(Paragraph("Evaluación de modelos", styles["NetoHeader"]))

    def decision_row(label, d):
        bg, tx = _decision_colors(d["decision"])
        badge = Table([[d["decision"]]], colWidths=[3*cm], rowHeights=[1*cm])
        badge.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), bg),
            ("TEXTCOLOR", (0,0), (-1,-1), tx),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ("FONT", (0,0), (-1,-1), "Helvetica-Bold"),
        ]))
        return [label, badge, Paragraph(d["explicacion"], styles["NetoSmall"])]

    decisions = Table(
        [
            ["Escenario", "Decisión", "Explicación"],
            decision_row("Con tienda NETO cercana", decision_modelo_1),
            decision_row("Sin tienda NETO cercana", decision_modelo_2),
        ],
        colWidths=[6*cm, 4*cm, 17*cm]
    )

    decisions.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), NETO_BLUE),
        ("TEXTCOLOR", (0,0), (-1,0), white),
        ("GRID", (0,0), (-1,-1), 0.25, black),
        ("PADDING", (0,0), (-1,-1), 6),
    ]))

    story.append(decisions)

    doc.build(story)
