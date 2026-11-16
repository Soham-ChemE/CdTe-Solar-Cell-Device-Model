import sys, pymupdf
pdf, out = sys.argv[1], sys.argv[2]
doc = pymupdf.open(pdf)
with open(out, 'w') as f:
    for i, p in enumerate(doc):
        f.write(f"\n===== PAGE {i+1} =====\n")
        f.write(p.get_text())
print(len(doc), "pages")
