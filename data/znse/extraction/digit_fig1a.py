import sys, pymupdf, csv
doc = pymupdf.open(sys.argv[1]); pg = doc[12]
dr = pg.get_drawings()
# major ticks in panel (a) region x 130-320, y 160-440
reg=(125,160,320,440)
sel=[d for d in dr if d["rect"].x0>=reg[0] and d["rect"].x1<=reg[2] and d["rect"].y0>=reg[1] and d["rect"].y1<=reg[3]]
ht = sorted({round(d["rect"].y0,2) for d in sel if "".join(i[0] for i in d["items"])=="l" and 4.5<d["rect"].width<5.5 and d["rect"].height<0.1 and d["rect"].x0<140})
vt = sorted({round(d["rect"].x0,2) for d in sel if "".join(i[0] for i in d["items"])=="l" and 4.5<d["rect"].height<5.5 and d["rect"].width<0.1 and d["rect"].y0>400})
print("y ticks", ht, "x ticks", vt)
y2e17,y1e17,y0 = ht; xm1,_,x0v,_,xp1 = vt
fx=lambda x: -1+(x-xm1)*2/(xp1-xm1)
fy=lambda y: (y0-y)*1e17/(y0-y1e17)
ser={"ZnSe_100nm":[], "ZnS_110nm":[]}
for d in sel:
    ops="".join(i[0] for i in d["items"]); r=d["rect"]
    if ops=="cccc" and abs(r.width-5.2)<0.2: ser["ZnSe_100nm"].append((fx((r.x0+r.x1)/2), fy((r.y0+r.y1)/2)))
    elif ops=="lll" and abs(r.width-6.2)<0.2:
        pts=[it[1] for it in d["items"]]
        ser["ZnS_110nm"].append((fx(sum(p.x for p in pts)/3), fy(sum(p.y for p in pts)/3)))
import bisect
out=[]
for k,v in ser.items():
    v=[p for p in v if not (p[0]<-0.85 and p[1]<0.2e17)]  # drop legend markers near bottom-left
    v.sort()
    print(k, len(v), "V range", round(v[0][0],3), round(v[-1][0],3))
    # interpolate at V=0
    for i in range(len(v)-1):
        if v[i][0]<=0<=v[i+1][0]:
            a,b=v[i],v[i+1]; y=a[1]+(b[1]-a[1])*(0-a[0])/(b[0]-a[0])
            C_A=y**-0.5; W=10.16*8.854e-14/C_A
            print(f"  1/C2(0V)={y:.3e} cm4/F2 -> C/A={C_A:.3e} F/cm2 -> W(eps=10.16)={W*1e4:.2f} um")
    for p in v: out.append((k,round(p[0],4),f"{p[1]:.4e}"))
with open(sys.argv[2],"w",newline="") as f:
    w=csv.writer(f); w.writerow(["series","bias_V","invC2_cm4_per_F2"]); w.writerows(out)
