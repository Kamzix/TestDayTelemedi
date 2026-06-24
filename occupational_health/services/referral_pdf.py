from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from occupational_health.models import ExposureFactor


FONT_NAME = 'TelemediPdfFont'
FONT_CANDIDATES = [
    Path('C:/Windows/Fonts/DejaVuSans.ttf'),
    Path('C:/Windows/Fonts/arial.ttf'),
    Path('C:/Windows/Fonts/calibri.ttf'),
    Path('C:/Windows/Fonts/segoeui.ttf'),
]


class PdfFontError(RuntimeError):
    pass


def generate_referral_pdf(referral):
    font_path = _find_font_path()
    _register_font(font_path)

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.6 * cm,
        leftMargin=1.6 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title=f'Skierowanie {referral.pk}',
    )
    styles = _build_styles()
    story = []

    story.append(Paragraph('SKIEROWANIE NA BADANIA LEKARSKIE', styles['Title']))
    story.append(Spacer(1, 0.4 * cm))
    story.extend(_employer_section(referral, styles))
    story.extend(_examination_section(referral, styles))
    story.extend(_employee_section(referral, styles))
    story.extend(_work_section(referral, styles))
    story.extend(_exposure_section(referral, styles))
    story.extend(_signature_section(styles))

    document.build(story)
    return buffer.getvalue()


def get_pdf_font_path():
    return _find_font_path()


def _find_font_path():
    for path in FONT_CANDIDATES:
        if path.exists():
            return path
    raise PdfFontError(
        'Nie znaleziono lokalnej czcionki TrueType obslugujacej polskie znaki.'
    )


def _register_font(font_path):
    if FONT_NAME not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(FONT_NAME, str(font_path)))


def _build_styles():
    base_styles = getSampleStyleSheet()
    styles = {
        'Title': ParagraphStyle(
            'TelemediTitle',
            parent=base_styles['Title'],
            fontName=FONT_NAME,
            fontSize=16,
            leading=20,
            spaceAfter=10,
            alignment=1,
        ),
        'Heading': ParagraphStyle(
            'TelemediHeading',
            parent=base_styles['Heading2'],
            fontName=FONT_NAME,
            fontSize=12,
            leading=15,
            spaceBefore=8,
            spaceAfter=6,
        ),
        'Normal': ParagraphStyle(
            'TelemediNormal',
            parent=base_styles['Normal'],
            fontName=FONT_NAME,
            fontSize=9,
            leading=12,
        ),
        'Small': ParagraphStyle(
            'TelemediSmall',
            parent=base_styles['Normal'],
            fontName=FONT_NAME,
            fontSize=8,
            leading=10,
        ),
    }
    return styles


def _employer_section(referral, styles):
    organization = referral.organization
    rows = [
        ('Nazwa organizacji', organization.name),
        ('Adres', organization.address),
        ('Kod pocztowy i miasto', f'{organization.postal_code} {organization.city}'),
        ('NIP', organization.tax_id),
        ('Miejsce i data wystawienia', f'{organization.city}, {_format_date(timezone.localdate())}'),
    ]
    return _section('Dane pracodawcy', rows, styles)


def _examination_section(referral, styles):
    rows = [
        ('Rodzaj badania', referral.get_examination_type_display()),
    ]
    return _section('Rodzaj badania', rows, styles)


def _employee_section(referral, styles):
    employee = referral.employee
    identity_rows = [('PESEL', employee.pesel)]
    if not employee.pesel:
        identity_rows = [
            ('Data urodzenia', _format_date(employee.birth_date)),
            ('Dokument tożsamości', employee.identity_document),
        ]
    rows = [
        ('Imię i nazwisko', f'{employee.first_name} {employee.last_name}'),
        *identity_rows,
        ('Adres', _employee_address(employee)),
    ]
    if employee.email:
        rows.append(('E-mail', employee.email))
    if employee.phone:
        rows.append(('Telefon', employee.phone))
    return _section('Dane pracownika', rows, styles)


def _work_section(referral, styles):
    rows = [
        ('Stanowisko', referral.job_position),
        ('Szczegółowy opis pracy', referral.work_description),
        ('Termin wykonania badań', _format_date(referral.deadline)),
    ]
    return _section('Informacje o pracy', rows, styles)


def _exposure_section(referral, styles):
    story = [Paragraph('Czynniki narażenia', styles['Heading'])]
    exposures = list(referral.exposures.all())
    story.append(Paragraph(f'Łączna liczba czynników: {len(exposures)}', styles['Normal']))

    for category_value, category_label in ExposureFactor.Category.choices:
        category_exposures = [
            exposure for exposure in exposures
            if exposure.exposure_factor.category == category_value
        ]
        if not category_exposures:
            continue

        story.append(Paragraph(category_label, styles['Heading']))
        data = [[
            Paragraph('Czynnik', styles['Small']),
            Paragraph('Opis narażenia', styles['Small']),
            Paragraph('Wynik pomiaru', styles['Small']),
        ]]
        for exposure in category_exposures:
            data.append([
                Paragraph(_safe(exposure.exposure_factor.name), styles['Small']),
                Paragraph(_safe(exposure.exposure_description), styles['Small']),
                Paragraph(_safe(exposure.measurement_result or '-'), styles['Small']),
            ])
        story.append(_table(data))
        story.append(Spacer(1, 0.2 * cm))

    return story


def _signature_section(styles):
    return [
        Spacer(1, 1.0 * cm),
        Paragraph('............................................................', styles['Normal']),
        Paragraph('Podpis pracodawcy lub osoby upoważnionej', styles['Small']),
    ]


def _section(title, rows, styles):
    data = [
        [
            Paragraph(_safe(label), styles['Small']),
            Paragraph(_safe(value), styles['Small']),
        ]
        for label, value in rows
    ]
    return [
        Paragraph(title, styles['Heading']),
        _table(data),
        Spacer(1, 0.2 * cm),
    ]


def _table(data):
    table = Table(data, colWidths=[5.0 * cm, 11.0 * cm], hAlign='LEFT')
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ('BACKGROUND', (0, 0), (0, -1), colors.whitesmoke),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    return table


def _employee_address(employee):
    apartment = f'/{employee.apartment_number}' if employee.apartment_number else ''
    return f'{employee.street} {employee.building_number}{apartment}, {employee.city}'


def _format_date(value):
    if not value:
        return ''
    return value.strftime('%d.%m.%Y')


def _safe(value):
    return escape(str(value or ''))
