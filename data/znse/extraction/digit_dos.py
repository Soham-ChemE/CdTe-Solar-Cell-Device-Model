import sys, pymupdf, collections
doc = pymupdf.open(sys.argv[1]); pg = doc[4]
panels = {
 # name: (region x0,y0,x1,y1), (xpix_a, xval_a, xpix_b, xval_b), (ypix_a, yval_a, ypix_b, yval_b)
 "ZnSe_c": ((122,490,300,622), (140.5,0.2,287.0,1.0), (620.75,0.0,500.65,5e16)),
 "ZnS_d":  ((362,490,545,624), (382.1,0.2,530.65,1.0), (623.2,0.0,501.4,1e16)),
}
if len(sys.argv)>2:
    exec(sys.argv[2])
for name,(reg,xc,yc) in panels.items():
    x0,y0,x1,y1 = reg
    fx = lambda p: xc[1]+(p-xc[0])*(xc[3]-xc[1])/(xc[2]-xc[0])
    fy = lambda p: yc[1]+(p-yc[0])*(yc[3]-yc[1])/(yc[2]-yc[0])
    shapes = collections.defaultdict(list)
    for d in pg.get_drawings():
        r=d["rect"]
        if r.x0<x0 or r.x1>x1 or r.y0<y0 or r.y1>y1: continue
        if r.width<6 and r.height<6 and r.width>1 and r.height>1:
            ops="".join(i[0] for i in d["items"])
            shapes[(ops,round(r.width,1),round(r.height,1))].append(((r.x0+r.x1)/2,(r.y0+r.y1)/2))
    print("==",name)
    for k,v in sorted(shapes.items(), key=lambda kv:-len(kv[1])):
        if len(v)<5: continue
        top = sorted(v, key=lambda p:p[1])[:3]
        print(k, len(v), "max Nt points:", [(round(fx(px),3), f"{fy(py):.2e}") for px,py in top])
