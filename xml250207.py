from lxml import etree
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import (
    TA_LEFT,
    TA_CENTER,
    TA_RIGHT,
)  # 确保从 reportlab.lib.enums 导入 TA_CENTER 和 TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch


# Load XML and parse it
def parse_xml(xml_file):
    with open(xml_file, "r", encoding="utf-8") as file:
        tree = etree.parse(file)
    return tree


# Extract data from XML
def extract_data(tree):
    namespaces = {
        "rsm": "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
        "ram": "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100",
        "udt": "urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100",
    }

    invoice_data = {}

    # Extract general information
    invoice_data["invoice_number"] = tree.findtext(
        ".//rsm:ExchangedDocument/ram:ID", namespaces=namespaces
    )
    invoice_data["invoice_date"] = tree.findtext(
        ".//rsm:ExchangedDocument/ram:IssueDateTime/udt:DateTimeString",
        namespaces=namespaces,
    )
    invoice_data["due_date"] = tree.findtext(
        ".//ram:SpecifiedTradePaymentTerms/ram:DueDateDateTime/udt:DateTimeString",
        namespaces=namespaces,
    )
    invoice_data["BuyerReference"] = tree.findtext(
        ".//ram:BuyerReference", namespaces=namespaces
    )
    invoice_data["purchase_order"] = tree.findtext(
        ".//ram:BuyerOrderReferencedDocument/ram:IssuerAssignedID",
        namespaces=namespaces,
    )
    invoice_data["PaymentTerms"] = tree.findtext(
        ".//ram:SpecifiedTradePaymentTerms/ram:Description", namespaces=namespaces
    )

    # Extract seller and buyer details
    seller = tree.find(".//ram:SellerTradeParty", namespaces=namespaces)
    buyer = tree.find(".//ram:BuyerTradeParty", namespaces=namespaces)
    invoice_data["seller"] = {
        "name": seller.findtext("ram:Name", namespaces=namespaces),
        "address": seller.findtext(
            "ram:PostalTradeAddress/ram:LineOne", namespaces=namespaces
        ),
        "city": seller.findtext(
            "ram:PostalTradeAddress/ram:CityName", namespaces=namespaces
        ),
        "postcode": seller.findtext(
            "ram:PostalTradeAddress/ram:PostcodeCode", namespaces=namespaces
        ),
        "country": seller.findtext(
            "ram:PostalTradeAddress/ram:CountryID", namespaces=namespaces
        ),
        "email": seller.findtext(
            "ram:DefinedTradeContact/ram:EmailURIUniversalCommunication/ram:URIID",
            namespaces=namespaces,
        ),
    }

    invoice_data["buyer"] = {
        "name": buyer.findtext("ram:Name", namespaces=namespaces),
        "address": buyer.findtext(
            "ram:PostalTradeAddress/ram:LineOne", namespaces=namespaces
        ),
        "city": buyer.findtext(
            "ram:PostalTradeAddress/ram:CityName", namespaces=namespaces
        ),
        "postcode": buyer.findtext(
            "ram:PostalTradeAddress/ram:PostcodeCode", namespaces=namespaces
        ),
        "country": buyer.findtext(
            "ram:PostalTradeAddress/ram:CountryID", namespaces=namespaces
        ),
        "email": buyer.findtext(
            "ram:DefinedTradeContact/ram:EmailURIUniversalCommunication/ram:URIID",
            namespaces=namespaces,
        ),
    }

    # Extract product lines
    product_lines = []
    for item in tree.findall(
        ".//ram:IncludedSupplyChainTradeLineItem", namespaces=namespaces
    ):
        product = {
            "LineID": item.findtext(".//ram:LineID", namespaces=namespaces),
            "SellerAssignedID": item.findtext(
                ".//ram:SellerAssignedID", namespaces=namespaces
            ),
            "model": item.findtext(".//ram:Name", namespaces=namespaces),
            "Content": item.findtext(".//ram:Content", namespaces=namespaces),
            "description": item.findtext(".//ram:Description", namespaces=namespaces),
            "quantity": item.findtext(".//ram:BilledQuantity", namespaces=namespaces),
            "unit_price": item.findtext(".//ram:ChargeAmount", namespaces=namespaces),
            "total": item.findtext(".//ram:LineTotalAmount", namespaces=namespaces),
        }
        product_lines.append(product)

    invoice_data["products"] = product_lines

    # Totals
    totals = tree.find(
        ".//ram:SpecifiedTradeSettlementHeaderMonetarySummation", namespaces=namespaces
    )
    invoice_data["subtotal"] = totals.findtext(
        "ram:LineTotalAmount", namespaces=namespaces
    )
    invoice_data["tax"] = totals.findtext("ram:TaxTotalAmount", namespaces=namespaces)
    invoice_data["total"] = totals.findtext(
        "ram:GrandTotalAmount", namespaces=namespaces
    )
   

    return invoice_data


# Create PDF with matching layout
def create_pdf(data, output_file):
    doc = SimpleDocTemplate(
        output_file,
        pagesize=A4,
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20,
    )
    styles = getSampleStyleSheet()

    # 添加自定义样式
    center_style = ParagraphStyle(
        name="Center",
        parent=styles["Normal"],
        alignment=TA_CENTER,  # 使用正确的 TA_CENTER
    )
    styles.add(center_style)
    right_style = ParagraphStyle(
        name="Right",
        parent=styles["Normal"],
        alignment=TA_RIGHT,  # 使用正确的 TA_RIGHT
        fontSize=12,
    )
    styles.add(right_style)

    # 添加自定义样式包含字体大小
    large_right_style = ParagraphStyle(
        name="LargeRight",
        parent=styles["Normal"],
        alignment=TA_RIGHT,
        fontSize=32,  # 设置字体大小为 32
    )
    styles.add(large_right_style)

    elements = []

    # Header
    elements.append(Paragraph("Invoice", large_right_style))  # 使用新的样式
    elements.append(Spacer(1, 12))

    # Invoice Information
    invoice_info = f"""
    <b>Invoice number:</b> {data['invoice_number']}<br/>
    <b>Date:</b> {data['invoice_date']}<br/>
    <b>Due date:</b> {data['due_date']}<br/>
    <b>Purchase order:</b> {data['purchase_order']}<br/>
    <b>BuyerReference:</b> {data['BuyerReference']}<br/>
    """
    elements.append(Paragraph(invoice_info, styles["Normal"]))
    elements.append(Spacer(1, 12))

    # Seller and Buyer Information
    seller_info = f"""
    <b>Seller:</b> {data['seller']['name']}<br/>
    {data['seller']['address']}, {data['seller']['city']}<br/>
    {data['seller']['postcode']}, {data['seller']['country']}<br/>
    Email: {data['seller']['email']}<br/>
    """

    buyer_info = f"""
    <b>Buyer:</b> {data['buyer']['name']}<br/>
    {data['buyer']['address']}, {data['buyer']['city']}<br/>
    {data['buyer']['postcode']}, {data['buyer']['country']}<br/>
    Email: {data['buyer']['email']}<br/>
    """

    seller_buyer_table = Table(
        [
            [
                Paragraph(seller_info, styles["Normal"]),
                Paragraph(buyer_info, styles["Normal"]),
            ]
        ],
        colWidths=[260, 260],  # Adjust column widths as needed
    )
    seller_buyer_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),  # Align content to the top
                (
                    "LINEBELOW",
                    (0, 0),
                    (-1, 0),
                    1,
                    colors.black,
                ),  # Add a line below for separation
            ]
        )
    )

    elements.append(seller_buyer_table)
    elements.append(Spacer(1, 12))

    # Product Table
    table_data = [
        [
            "LineID",
            "SellerAssignedID",
            "model and Description",
            "Quantity",
            "Unit Price",
            "Total",
        ]
    ]
    for product in data["products"]:
        model_and_description = (
            f"{product['model']}<br/>{product['description']}<br/>{product['Content']}"
        )
        table_data.append(
            [
                Paragraph(str(product["LineID"]), styles["Normal"]),
                Paragraph(str(product["SellerAssignedID"]), styles["Normal"]),
                Paragraph(model_and_description, styles["Normal"]),
                Paragraph(str(product["quantity"]), styles["Normal"]),
                Paragraph(f"{product['unit_price']} EUR", styles["Normal"]),
                Paragraph(f"{product['total']} EUR", styles["Normal"]),
            ]
        )

    table = Table(table_data, colWidths=[60, 100, 210, 50, 70, 80])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    elements.append(table)
    elements.append(Spacer(1, 12))

    # Totals
    totals = f"""
    <b>Subtotal:</b> {data['subtotal']} <br/>
    <b>VAT:</b> {data['tax']} <br/>
    <b>Total amount:</b> {data['total']} <br/>
    """
    elements.append(Paragraph(totals, styles["Right"]))
    elements.append(Spacer(1, 12))

    # Payment Information
    payment_info1= f"""
    <b>payment:</b> {data['PaymentTerms']} <br/>
   
    """
    elements.append(Paragraph(payment_info1, styles["Normal"]))
    payment_info = "Bank transfer to IBAN: DE67 7524 0000 0712 3557 00"
    elements.append(Paragraph(payment_info, styles["Normal"]))
   
    # Build PDF
    doc.build(elements)


# Main function
def main():
    xml_file = "GRG1242416.xml"
    output_file = "invoice_output1.pdf"

    tree = parse_xml(xml_file)
    data = extract_data(tree)
    create_pdf(data, output_file)


if __name__ == "__main__":
    main()
