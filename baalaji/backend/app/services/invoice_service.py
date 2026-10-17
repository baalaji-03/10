from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from backend.app.models import Sale, PharmacySetting

def generate_pdf_invoice(sale: Sale, setting: PharmacySetting, format_type: str = "A4") -> BytesIO:
    """
    Generates PDF invoice in A4, 80mm, or 58mm format using ReportLab.
    """
    buffer = BytesIO()

    if format_type.upper() == "58MM":
        page_width = 58 * mm
        left_margin = right_margin = top_margin = bottom_margin = 3 * mm
        doc = SimpleDocTemplate(
            buffer,
            pagesize=(page_width, 250 * mm),
            leftMargin=left_margin,
            rightMargin=right_margin,
            topMargin=top_margin,
            bottomMargin=bottom_margin
        )
        return _build_thermal_receipt(doc, buffer, sale, setting, is_58mm=True)

    elif format_type.upper() == "80MM":
        page_width = 80 * mm
        left_margin = right_margin = top_margin = bottom_margin = 4 * mm
        doc = SimpleDocTemplate(
            buffer,
            pagesize=(page_width, 300 * mm),
            leftMargin=left_margin,
            rightMargin=right_margin,
            topMargin=top_margin,
            bottomMargin=bottom_margin
        )
        return _build_thermal_receipt(doc, buffer, sale, setting, is_58mm=False)

    else:  # A4 Full-Page Invoice
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=12 * mm,
            rightMargin=12 * mm,
            topMargin=12 * mm,
            bottomMargin=12 * mm
        )
        return _build_a4_invoice(doc, buffer, sale, setting)

def _build_a4_invoice(doc, buffer, sale: Sale, setting: PharmacySetting) -> BytesIO:
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=18,
        textColor=colors.HexColor('#0f766e'),
        alignment=1 # Center
    )
    sub_title_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        alignment=1
    )
    bold_style = ParagraphStyle(
        'BoldSmall',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10
    )
    normal_style = ParagraphStyle(
        'NormalSmall',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10
    )
    right_bold = ParagraphStyle(
        'RightBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        alignment=2 # Right
    )

    story = []

    # Header / Pharmacy info
    p_name = setting.pharmacy_name if setting else "Baalaji Medicals & Healthcare"
    p_tag = setting.tagline if setting and setting.tagline else "Your Trusted Pharmacy"
    p_addr = f"{setting.address_line1}, {setting.address_line2 or ''}, {setting.city} - {setting.postal_code}" if setting else "Chennai, Tamil Nadu"
    p_dl = f"D.L. No: {setting.dl_number}" if setting and setting.dl_number else ""
    p_gst = f"GSTIN: {setting.gstin}" if setting and setting.gstin else ""
    p_phone = f"Phone: {setting.phone} | Email: {setting.email}" if setting else ""

    story.append(Paragraph(p_name.upper(), title_style))
    story.append(Paragraph(f"<i>{p_tag}</i>", sub_title_style))
    story.append(Paragraph(p_addr, sub_title_style))
    story.append(Paragraph(f"{p_phone}", sub_title_style))
    story.append(Paragraph(f"<b>{p_gst}</b> | <b>{p_dl}</b>", sub_title_style))
    story.append(Spacer(1, 4 * mm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#0f766e')))
    story.append(Spacer(1, 2 * mm))

    # Meta Section (Invoice details left, Customer right)
    inv_date = sale.invoice_date.strftime("%d-%m-%Y") if sale.invoice_date else ""
    inv_time = sale.invoice_time.strftime("%I:%M %p") if sale.invoice_time else ""

    meta_data = [
        [
            Paragraph("<b>TAX INVOICE</b>", ParagraphStyle('H2', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#0f766e'))),
            Paragraph("<b>BILLED TO (CUSTOMER):</b>", bold_style)
        ],
        [
            Paragraph(f"<b>Invoice No:</b> {sale.invoice_number}", normal_style),
            Paragraph(f"<b>Name:</b> {sale.customer_name or 'Walk-in Customer'}", normal_style)
        ],
        [
            Paragraph(f"<b>Date & Time:</b> {inv_date} {inv_time}", normal_style),
            Paragraph(f"<b>Mobile:</b> {sale.customer_mobile or 'N/A'}", normal_style)
        ],
        [
            Paragraph(f"<b>Payment Mode:</b> {sale.payment_method} ({sale.payment_status})", normal_style),
            Paragraph(f"<b>Prescribing Doctor:</b> {sale.doctor_name or 'Self / Walk-in'}", normal_style)
        ]
    ]

    meta_table = Table(meta_data, colWidths=[90 * mm, 96 * mm])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('TOPPADDING', (0,0), (-1,-1), 1),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 3 * mm))

    # Items Table
    headers = ["#", "Medicine Description", "HSN", "Batch", "Expiry", "Qty", "MRP", "Disc%", "GST%", "Total (₹)"]
    table_rows = [headers]

    idx = 1
    for itm in sale.items:
        exp_str = itm.expiry_date.strftime("%m/%y") if itm.expiry_date else ""
        table_rows.append([
            str(idx),
            itm.medicine_name[:26],
            str(itm.hsn_code or "3004"),
            itm.batch_number[:10],
            exp_str,
            str(itm.quantity),
            f"{float(itm.mrp or itm.unit_price):.2f}",
            f"{float(itm.discount_percent or 0):.1f}%",
            f"{float(itm.gst_rate or 12):.0f}%",
            f"{float(itm.total_amount):.2f}"
        ])
        idx += 1

    item_table = Table(table_rows, colWidths=[8*mm, 52*mm, 15*mm, 20*mm, 15*mm, 12*mm, 16*mm, 14*mm, 14*mm, 20*mm])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f766e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7.5),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
        ('TOPPADDING', (0, 0), (-1, 0), 4),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (5, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(item_table)
    story.append(Spacer(1, 3 * mm))

    # Summary and Tax Breakdown
    subtotal = float(sale.subtotal or 0)
    disc = float(sale.discount_amount or 0)
    taxable = float(sale.taxable_amount or 0)
    cgst = float(sale.cgst_amount or 0)
    sgst = float(sale.sgst_amount or 0)
    igst = float(sale.igst_amount or 0)
    total_tax = float(sale.tax_amount or 0)
    round_off = float(sale.round_off or 0)
    net_amt = float(sale.net_amount or 0)
    paid_amt = float(sale.paid_amount or 0)

    summary_data = [
        [
            Paragraph(f"<b>Tax Breakdown:</b> Taxable: ₹{taxable:.2f} | CGST: ₹{cgst:.2f} | SGST: ₹{sgst:.2f} | IGST: ₹{igst:.2f}", normal_style),
            Paragraph("Subtotal:", normal_style),
            Paragraph(f"₹ {subtotal:.2f}", right_bold)
        ],
        [
            "",
            Paragraph("Discount:", normal_style),
            Paragraph(f"- ₹ {disc:.2f}", right_bold)
        ],
        [
            "",
            Paragraph("Total GST:", normal_style),
            Paragraph(f"₹ {total_tax:.2f}", right_bold)
        ],
        [
            "",
            Paragraph("Round Off:", normal_style),
            Paragraph(f"₹ {round_off:.2f}", right_bold)
        ],
        [
            "",
            Paragraph("<b>GRAND TOTAL:</b>", ParagraphStyle('Grand', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#0f766e'))),
            Paragraph(f"<b>₹ {net_amt:.2f}</b>", ParagraphStyle('GrandVal', fontName='Helvetica-Bold', fontSize=11, textColor=colors.HexColor('#0f766e'), alignment=2))
        ],
        [
            "",
            Paragraph("Paid Amount:", normal_style),
            Paragraph(f"₹ {paid_amt:.2f}", right_bold)
        ]
    ]

    summary_table = Table(summary_data, colWidths=[96 * mm, 45 * mm, 45 * mm])
    summary_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('LINEABOVE', (1,4), (-1,4), 1, colors.HexColor('#0f766e')),
        ('LINEBELOW', (1,4), (-1,4), 1, colors.HexColor('#0f766e')),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 4 * mm))

    # Declarations and Signature
    declaration_text = setting.invoice_declaration if setting and setting.invoice_declaration else "Goods once sold cannot be returned without bill."
    footer_data = [
        [
            Paragraph(f"<b>Terms & Conditions:</b><br/>{declaration_text}", ParagraphStyle('Decl', fontName='Helvetica', fontSize=7, leading=9)),
            Paragraph(f"For <b>{p_name}</b><br/><br/><br/>Authorized Signatory / Pharmacist", ParagraphStyle('Sign', fontName='Helvetica', fontSize=8, leading=10, alignment=2))
        ]
    ]
    footer_table = Table(footer_data, colWidths=[120 * mm, 66 * mm])
    footer_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(footer_table)

    doc.build(story)
    buffer.seek(0)
    return buffer

def _build_thermal_receipt(doc, buffer, sale: Sale, setting: PharmacySetting, is_58mm: bool) -> BytesIO:
    font_size = 6 if is_58mm else 7.5
    title_size = 9 if is_58mm else 11

    title_style = ParagraphStyle('TTitle', fontName='Helvetica-Bold', fontSize=title_size, leading=title_size+2, alignment=1)
    center_style = ParagraphStyle('TCenter', fontName='Helvetica', fontSize=font_size, leading=font_size+2, alignment=1)
    left_style = ParagraphStyle('TLeft', fontName='Helvetica', fontSize=font_size, leading=font_size+2, alignment=0)
    bold_left = ParagraphStyle('TBoldLeft', fontName='Helvetica-Bold', fontSize=font_size, leading=font_size+2, alignment=0)
    bold_right = ParagraphStyle('TBoldRight', fontName='Helvetica-Bold', fontSize=font_size, leading=font_size+2, alignment=2)

    story = []

    p_name = setting.pharmacy_name if setting else "Baalaji Medicals"
    story.append(Paragraph(p_name.upper(), title_style))
    story.append(Paragraph(f"{setting.address_line1 if setting else 'Chennai'}", center_style))
    story.append(Paragraph(f"Ph: {setting.phone if setting else ''}", center_style))
    if setting and setting.gstin:
        story.append(Paragraph(f"GSTIN: {setting.gstin}", center_style))
    if setting and setting.dl_number:
        story.append(Paragraph(f"DL: {setting.dl_number}", center_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.black))

    inv_date = sale.invoice_date.strftime("%d/%m/%Y") if sale.invoice_date else ""
    inv_time = sale.invoice_time.strftime("%I:%M %p") if sale.invoice_time else ""
    story.append(Paragraph(f"Bill No: <b>{sale.invoice_number}</b>", bold_left))
    story.append(Paragraph(f"Date: {inv_date} {inv_time}", left_style))
    story.append(Paragraph(f"Cust: {sale.customer_name or 'Walk-in'} ({sale.customer_mobile or ''})", left_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.black))

    if is_58mm:
        # Narrow columns for 58mm: Item(qty), Batch, Amt
        item_rows = [["Item", "Batch", "Qty", "Amt"]]
        for itm in sale.items:
            item_rows.append([
                itm.medicine_name[:12],
                itm.batch_number[:6],
                str(itm.quantity),
                f"{float(itm.total_amount):.1f}"
            ])
        item_table = Table(item_rows, colWidths=[20*mm, 12*mm, 8*mm, 12*mm])
    else:
        # 80mm columns
        item_rows = [["Item", "Batch", "Exp", "Qty", "Rate", "Amt"]]
        for itm in sale.items:
            exp = itm.expiry_date.strftime("%m/%y") if itm.expiry_date else ""
            item_rows.append([
                itm.medicine_name[:16],
                itm.batch_number[:8],
                exp,
                str(itm.quantity),
                f"{float(itm.unit_price):.1f}",
                f"{float(itm.total_amount):.2f}"
            ])
        item_table = Table(item_rows, colWidths=[26*mm, 13*mm, 10*mm, 6*mm, 9*mm, 10*mm])

    item_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), font_size),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('ALIGN', (-1,0), (-1,-1), 'RIGHT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('LINEBELOW', (0,0), (-1,0), 0.5, colors.black),
    ]))
    story.append(item_table)
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.black))

    # Total section
    net_amt = float(sale.net_amount or 0)
    tax_amt = float(sale.tax_amount or 0)
    story.append(Paragraph(f"Tax Included: ₹{tax_amt:.2f}", left_style))
    story.append(Paragraph(f"<b>NET TOTAL: ₹{net_amt:.2f}</b>", bold_right))
    story.append(Paragraph(f"Paid ({sale.payment_method}): ₹{float(sale.paid_amount or net_amt):.2f}", left_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.black))

    story.append(Paragraph("Thank you! Get Well Soon!", center_style))
    story.append(Paragraph("Goods once sold cannot be returned without bill", center_style))

    doc.build(story)
    buffer.seek(0)
    return buffer
