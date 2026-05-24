import markdown2
from fpdf import FPDF

# Read the markdown text
with open("rapor.md", "r", encoding="utf-8") as f:
    text = f.read()

# Convert markdown to HTML
html = markdown2.markdown(text)

# Create PDF
pdf = FPDF()
pdf.add_page()

# Add fonts to support Turkish characters
try:
    pdf.add_font("ArialTR", "", r"C:\Windows\Fonts\arial.ttf")
    pdf.add_font("ArialTR", "B", r"C:\Windows\Fonts\arialbd.ttf")
    pdf.add_font("ArialTR", "I", r"C:\Windows\Fonts\ariali.ttf")
    pdf.add_font("ArialTR", "BI", r"C:\Windows\Fonts\arialbi.ttf")
    pdf.set_font("ArialTR", size=11)
except Exception as e:
    print("Could not load Arial font, using default:", e)
    pdf.set_font("Helvetica", size=11)

# Ensure HTML does not have any tags that fpdf cannot handle, though markdown2 output is usually safe
pdf.write_html(html)

# Save PDF
pdf.output("rapor.pdf")
print("PDF created successfully as rapor.pdf")
