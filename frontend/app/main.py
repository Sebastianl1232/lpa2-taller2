from flask import Flask, render_template, request, send_file, abort
import requests
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from io import BytesIO
import os

app = Flask(__name__)
BACKEND_URL = os.getenv('BACKEND_API_URL', 'http://backend:8000')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generar-pdf', methods=['POST'])
def generar_pdf():
    id_factura = request.form.get('id_factura', '').strip()
    if not id_factura:
        abort(400, description="El número de factura es obligatorio")

    try:
        response = requests.get(
            f'{BACKEND_URL}/facturas/v1/{id_factura}',
            timeout=10
        )
        
        if response.status_code != 200:
            abort(404, description="Factura no encontrada")
            
        factura = response.json()
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm
        )
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("FACTURA", styles['Title']))
        elements.append(Paragraph(
            f"Número: {factura['numero_factura']}<br/>"
            f"Fecha de emisión: {factura['fecha_emision']}",
            styles['Normal']
        ))
        elements.append(Spacer(1, 10))

        empresa = factura['empresa']
        elements.append(Paragraph(
            f"<b>Empresa</b><br/>{empresa['nombre']}<br/>"
            f"{empresa['direccion']}<br/>"
            f"{empresa['telefono']}<br/>{empresa['email']}",
            styles['Normal']
        ))
        elements.append(Spacer(1, 10))

        cliente = factura['cliente']
        elements.append(Paragraph(
            f"<b>Cliente</b><br/>{cliente['nombre']}<br/>"
            f"{cliente['direccion']}<br/>{cliente['telefono']}",
            styles['Normal']
        ))
        elements.append(Spacer(1, 15))

        detalle = [['Cantidad', 'Descripción', 'Precio unitario', 'Total']]
        for item in factura['detalle']:
            detalle.append([
                str(item['cantidad']),
                item['descripcion'],
                f"${item['precio_unitario']:.2f}",
                f"${item['total']:.2f}"
            ])

        detalle_table = Table(detalle, colWidths=[25 * mm, 85 * mm, 35 * mm, 35 * mm])
        detalle_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(detalle_table)
        elements.append(Spacer(1, 15))

        resumen = [
            ['Subtotal', f"${factura['subtotal']:.2f}"],
            ['Impuesto (21%)', f"${factura['impuesto']:.2f}"],
            ['Total', f"${factura['total']:.2f}"],
        ]
        resumen_table = Table(resumen, colWidths=[145 * mm, 35 * mm], hAlign='RIGHT')
        resumen_table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(resumen_table)

        doc.build(elements)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'factura-{id_factura}.pdf'
        )
    except requests.exceptions.ConnectionError:
        abort(503, description="Error de conexión con el servidor")
    except requests.exceptions.Timeout:
        abort(504, description="El servidor tardó demasiado en responder")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)

