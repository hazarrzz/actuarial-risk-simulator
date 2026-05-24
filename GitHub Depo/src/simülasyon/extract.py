import fitz

doc = fitz.open("Kalın kuyruklu hasar modellerinde iflas olasılığının benzetim yöntemi ile hesabı_ Trafik sigortası örneği[#123886]-105673.pdf")
text = ""
for page in doc:
    text += page.get_text()

keywords = ["lambda", "poisson", "prim", "log-normal", "pareto", "c =", "c="]
lines = text.split('\n')
found = set()

with open("extract_out.txt", "w", encoding="utf-8") as f:
    for i, line in enumerate(lines):
        if any(k in line.lower() for k in keywords):
            # We want to print unique blocks
            block = "\n".join(lines[max(0, i-2):min(len(lines), i+3)])
            if block not in found:
                f.write(f"--- Line {i} ---\n")
                f.write(block + "\n\n")
                found.add(block)
