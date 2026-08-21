from fpdf import FPDF
import textwrap

pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)

# Title
pdf.set_font("Arial", 'B', 16)
pdf.cell(200, 10, txt="Apple Inc. Annual Report (Dummy 10-K)", ln=True, align='C')

# Introduction
pdf.set_font("Arial", size=12)
intro_text = "This is a dummy PDF created for the LetsFin AI Equity Analyst. It contains sample text that the FAISS index will ingest so that the Filings Agent can search through it when queried about qualitative information, risk factors, or business strategy."
for line in textwrap.wrap(intro_text, width=80):
    pdf.cell(200, 10, txt=line, ln=True)

pdf.ln(10)

# Risk Factors
pdf.set_font("Arial", 'B', 14)
pdf.cell(200, 10, txt="Item 1A. Risk Factors", ln=True)
pdf.set_font("Arial", size=12)

risk_text = """
The Company's business is subject to numerous risks and uncertainties. One major risk is the intense competition in the technology sector, particularly in cloud computing and artificial intelligence. The Company faces significant competition from other global technology firms which could negatively impact our market share and gross margins.

Another critical risk factor is our reliance on complex global supply chains. Disruptions due to geopolitical tensions, pandemics, or natural disasters could cause significant manufacturing delays for our flagship products. Furthermore, changes in international trade policies, tariffs, or export controls could substantially increase our costs.

We are also subject to stringent data privacy and security regulations worldwide. Any failure to comply with these regulations or any significant data breach could result in substantial fines and reputational damage.
"""

for paragraph in risk_text.strip().split('\n\n'):
    for line in textwrap.wrap(paragraph.strip(), width=80):
        pdf.cell(200, 10, txt=line, ln=True)
    pdf.ln(5)

# Business Strategy
pdf.set_font("Arial", 'B', 14)
pdf.cell(200, 10, txt="Item 1. Business", ln=True)
pdf.set_font("Arial", size=12)

biz_text = """
The Company's core business strategy involves designing and developing innovative hardware, software, and services that seamlessly integrate to provide an unparalleled user experience. We continue to invest heavily in Research and Development (R&D), specifically targeting advancements in machine learning, augmented reality, and sustainable materials.

Our long-term goal is to achieve 100% carbon neutrality across our entire supply chain and product life cycle by the year 2030. We are actively transitioning to renewable energy sources and increasing the use of recycled materials in our products.
"""

for paragraph in biz_text.strip().split('\n\n'):
    for line in textwrap.wrap(paragraph.strip(), width=80):
        pdf.cell(200, 10, txt=line, ln=True)
    pdf.ln(5)

pdf.output("sample_report.pdf")
print("Successfully generated sample_report.pdf")
