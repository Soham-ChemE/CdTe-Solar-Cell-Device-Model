import sys, pymupdf, csv
doc = pymupdf.open(sys.argv[1]); pg = doc[12]
X0,Y0,X1,Y1 = 355,175,545,445
dr = [d for d in pg.get_drawings() if d["rect"].x0>=X0 and d["rect"].x1<=X1 and d["rect"].y0>=Y0 and d["rect"].y1<=Y1]
ht = sorted({round(d["rect"].y0,2) for d in dr if "".join(i[0] for i in d["items"])=="l" and abs(d["rect"].width-4.9)<0.2 and d["rect"].height<0.1})
vt = sorted({round(d["rect"].x0,2) for d in dr if "".join(i[0] for i in d["items"])=="l" and abs(d["rect"].height-4.9)<0.2 and d["rect"].width<0.1})
print("y major ticks", ht); print("x major ticks", vt)
# y ticks: top->bottom = 1e16,1e15,1e14
y16,y15,y14 = ht
x00,x05,x10 = vt
def ty(y): return 10**(14 + (y14-y)/(y14-y15))
def tx(x): return (x-x00)/(x10-x00)
rows=[]
for d in dr:
    ops = "".join(i[0] for i in d["items"]); r=d["rect"]; cx,cy=(r.x0+r.x1)/2,(r.y0+r.y1)/2
    if ops=="cccc" and abs(r.width-5.2)<0.2: rows.append(("ZnSe_100nm",tx(cx),ty(cy)))
    elif ops=="lll" and abs(r.width-6.2)<0.2:
        # triangle centroid: use bbox center-ish (vertical centroid at 2/3 from apex)
        pts=[it[1] for it in d["items"]]+[d["items"][-1][2]]
        ys=[p.y for p in pts]; xs=[p.x for p in pts]
        rows.append(("ZnS_110nm",tx(sum(xs[:3])/3),ty(sum(ys[:3])/3)))
    elif ops.startswith("llllll") and d.get("width",0)>1.5:
        pts=[d["items"][0][1]]+[it[2] for it in d["items"]]
        for p in pts: rows.append(("ZnO_120nm_line",tx(p.x),ty(p.y)))
# drop legend markers (x beyond plot data region near legend text, y < 230)
rows=[r for r in rows if not (r[0]!="ZnO_120nm_line" and ty(232)<r[2] and r[1]>0.35 and r[1]<0.62 and r[2]>9e15)]
rows.sort(key=lambda r:(r[0],r[1]))
with open(sys.argv[2],"w",newline="") as f:
    w=csv.writer(f); w.writerow(["series","Wd_normalised","rho_cm3"])
    for r in rows: w.writerow([r[0],f"{r[1]:.4f}",f"{r[2]:.4g}"])
import collections; print(collections.Counter(r[0] for r in rows))
