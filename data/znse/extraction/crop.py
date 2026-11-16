import sys, pymupdf
pdf, out, page, x0,y0,x1,y1, dpi = sys.argv[1], sys.argv[2], int(sys.argv[3]), *map(float, sys.argv[4:8]), int(sys.argv[8])
doc = pymupdf.open(pdf)
p = doc[page-1]
r = p.rect
clip = pymupdf.Rect(r.width*x0, r.height*y0, r.width*x1, r.height*y1)
p.get_pixmap(dpi=dpi, clip=clip).save(out); print(out)
