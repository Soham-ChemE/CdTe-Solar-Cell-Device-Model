import sys, pymupdf
pdf, outprefix, pages, dpi = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv)>4 else 150
doc = pymupdf.open(pdf)
for s in pages.split(','):
    n = int(s)
    pix = doc[n-1].get_pixmap(dpi=dpi)
    pix.save(f"{outprefix}_p{n}.png")
    print(f"{outprefix}_p{n}.png")
