"""Helpers to digitise Origin-exported figures embedded as vector graphics in PDFs.

Two independent routes are provided:

1. Vector route (primary). The PDF drawing commands are read with PyMuPDF.
   Origin exports every line either as a stroked path (thesis) or as the
   filled outline of the stroke (journal PDFs). For filled outlines the
   centreline is recovered by slicing the outline polygon with vertical and
   horizontal lines and taking the midpoint of each pair of crossings, which
   is exact for straight segments at any slope. Box-plot elements are read
   from rectangle, bar and marker geometry.

2. Raster route (check). The panel is rendered to pixels at high DPI, the
   curve colour is masked, and the centre of each run of coloured pixels is
   located. Pixels are converted to data with the same tick calibration.

Axis calibration uses the centres of the major tick marks found in the
vector drawing, with the tick values typed in from the figure labels. A
least-squares linear (or log10) fit maps page points to data; its residual
is reported.
"""
import numpy as np
import pymupdf

# --------------------------------------------------------------------------
# primitives


def open_page(pdf, page):
    doc = pymupdf.open(pdf)
    return doc, doc[page - 1]


def in_clip(r, clip):
    return not (r.x1 < clip[0] or r.x0 > clip[2] or r.y1 < clip[1] or r.y0 > clip[3])


def prims(page, clip):
    """All drawings whose bounding box touches clip (degenerate boxes kept)."""
    return [d for d in page.get_drawings() if in_clip(d["rect"], clip)]


def pcol(d):
    """Colour that is painted: fill colour for fills, stroke colour for strokes."""
    if d["type"] == "s":
        return d.get("color")
    return d.get("fill")


def is_dark(c, thr=0.35):
    return c is not None and max(c) < thr


def close(c, ref, tol=0.06):
    return c is not None and max(abs(a - b) for a, b in zip(c, ref)) < tol


def _bez(p0, p1, p2, p3, n=6):
    t = np.linspace(0, 1, n)[:, None]
    P = [np.array([p.x, p.y]) for p in (p0, p1, p2, p3)]
    return ((1 - t) ** 3) * P[0] + 3 * ((1 - t) ** 2) * t * P[1] + 3 * (1 - t) * t * t * P[2] + t ** 3 * P[3]


def subpaths(d):
    """Flatten the items of one drawing into continuous (N,2) point arrays."""
    paths, cur = [], []

    def push(pts):
        nonlocal cur
        pts = [tuple(p) for p in np.asarray(pts, float)]
        if cur and np.hypot(cur[-1][0] - pts[0][0], cur[-1][1] - pts[0][1]) < 1e-3:
            cur.extend(pts[1:])
        else:
            if cur:
                paths.append(np.array(cur))
            cur = list(pts)

    for it in d["items"]:
        k = it[0]
        if k == "l":
            push([(it[1].x, it[1].y), (it[2].x, it[2].y)])
        elif k == "c":
            push(_bez(it[1], it[2], it[3], it[4]))
        elif k == "re":
            r = it[1]
            push([(r.x0, r.y0), (r.x1, r.y0), (r.x1, r.y1), (r.x0, r.y1), (r.x0, r.y0)])
        elif k == "qu":
            q = it[1]
            push([(q.ul.x, q.ul.y), (q.ur.x, q.ur.y), (q.lr.x, q.lr.y), (q.ll.x, q.ll.y), (q.ul.x, q.ul.y)])
    if cur:
        paths.append(np.array(cur))
    return paths


def center(d):
    r = d["rect"]
    return (0.5 * (r.x0 + r.x1), 0.5 * (r.y0 + r.y1))


# --------------------------------------------------------------------------
# axis calibration


class Axis:
    """Map a page coordinate (pt) to a data value: v = a + b*pt (or 10**(a+b*pt))."""

    def __init__(self, pts, vals, log=False):
        pts = np.asarray(pts, float)
        vals = np.asarray(vals, float)
        self.log = log
        y = np.log10(vals) if log else vals
        A = np.vstack([np.ones_like(pts), pts]).T
        (self.a, self.b), *_ = np.linalg.lstsq(A, y, rcond=None)
        fit = self.a + self.b * pts
        # residual expressed in page points
        self.resid_pt = float(np.max(np.abs(fit - y)) / abs(self.b)) if len(pts) > 2 else 0.0
        self.pts, self.vals = pts, vals

    def __call__(self, pt):
        v = self.a + self.b * np.asarray(pt, float)
        return 10 ** v if self.log else v

    def inv(self, val):
        v = np.log10(val) if self.log else np.asarray(val, float)
        return (v - self.a) / self.b

    def per_pt(self):
        """Data units per page point (for linear axes)."""
        return abs(self.b)


def find_ticks(ps, axis, line_pos, span, tol=0.7, max_len=4.5):
    """Centres of tick marks perpendicular to an axis line.

    axis='x': ticks are near-vertical marks touching the horizontal line y=line_pos,
    with x within span=(xmin,xmax). Returns list of (centre, length).
    """
    out = []
    for d in ps:
        if not is_dark(pcol(d)):
            continue
        if len(d["items"]) > 2:
            # glyphs and outlines have many items; ticks are 1 rect or 1 line
            continue
        r = d["rect"]
        if axis == "x":
            w, h = r.width, r.height
            if w > 0.6 or h < 0.3 or h > max_len:
                continue
            if not (abs(r.y0 - line_pos) < tol or abs(r.y1 - line_pos) < tol):
                continue
            c = 0.5 * (r.x0 + r.x1)
            if span[0] - 0.5 <= c <= span[1] + 0.5:
                out.append((c, h))
        else:
            w, h = r.width, r.height
            if h > 0.6 or w < 0.3 or w > max_len:
                continue
            if not (abs(r.x0 - line_pos) < tol or abs(r.x1 - line_pos) < tol):
                continue
            c = 0.5 * (r.y0 + r.y1)
            if span[0] - 0.5 <= c <= span[1] + 0.5:
                out.append((c, w))
    out.sort()
    # de-duplicate (fill + stroke of the same tick)
    ded = []
    for c, L in out:
        if ded and abs(ded[-1][0] - c) < 0.2:
            if L > ded[-1][1]:
                ded[-1] = (c, L)
            continue
        ded.append((c, L))
    return ded


def major_ticks(ticks, rel=0.85):
    if not ticks:
        return []
    Lmax = max(L for _, L in ticks)
    return [c for c, L in ticks if L >= rel * Lmax]


def calibrate(ps, axis, line_pos, span, values, log=False, label=""):
    t = major_ticks(find_ticks(ps, axis, line_pos, span))
    if len(t) != len(values):
        raise RuntimeError(f"{label}: found {len(t)} major ticks {np.round(t,2)} but {len(values)} values {values}")
    return Axis(t, values, log=log)


# --------------------------------------------------------------------------
# curves from filled stroke outlines


def edges(paths):
    E = []
    for P in paths:
        Q = np.vstack([P, P[:1]])
        E.append(np.hstack([Q[:-1], Q[1:]]))
    return np.vstack(E)


def _cross(E, pos, along):
    if along == "x":
        a0, b0, a1, b1 = E[:, 0], E[:, 1], E[:, 2], E[:, 3]
    else:
        a0, b0, a1, b1 = E[:, 1], E[:, 0], E[:, 3], E[:, 2]
    m = ((a0 <= pos) & (a1 > pos)) | ((a1 <= pos) & (a0 > pos))
    t = (pos - a0[m]) / (a1[m] - a0[m])
    return np.sort(b0[m] + t * (b1[m] - b0[m]))


def _pair_thickness(E, pos, along, q):
    """Thickness of the crossing pair (slice at pos) that contains coordinate q."""
    b = _cross(E, pos, along)
    if len(b) % 2:
        return np.inf
    for i in range(0, len(b), 2):
        if b[i] - 1e-9 <= q <= b[i + 1] + 1e-9:
            return b[i + 1] - b[i]
    return np.inf


def centreline(paths, step=0.05, wmax=None):
    """Centreline points (x,y) of a filled stroke outline.

    Vertical slices give the centre where the stroke is shallow, horizontal
    slices where it is steep. At every candidate point the slice direction
    with the thinner cut is kept, so each part of the curve is read in its
    best-conditioned direction (exact for straight segments). Candidates
    thicker than wmax (default 2.2 x the minimum thickness) are dropped.
    """
    E = edges(paths)
    allp = np.vstack(paths)
    x0, y0 = allp.min(0)
    x1, y1 = allp.max(0)
    vs, hs = [], []
    # an even number of crossings means the slice passes through separate
    # branches of the stroke; consecutive crossings pair up branch by branch
    for x in np.arange(x0 + step / 2, x1, step):
        b = _cross(E, x, "x")
        if len(b) % 2 == 0:
            for i in range(0, len(b), 2):
                vs.append((x, 0.5 * (b[i] + b[i + 1]), b[i + 1] - b[i]))
    for y in np.arange(y0 + step / 2, y1, step):
        b = _cross(E, y, "y")
        if len(b) % 2 == 0:
            for i in range(0, len(b), 2):
                hs.append((0.5 * (b[i] + b[i + 1]), y, b[i + 1] - b[i]))
    vs, hs = np.array(vs).reshape(-1, 3), np.array(hs).reshape(-1, 3)
    th = np.concatenate([vs[:, 2], hs[:, 2]])
    wmin = np.percentile(th, 2)
    if wmax is None:
        wmax = 2.2 * wmin
    keep = []
    for x, y, t in vs:
        if t <= wmax and _pair_thickness(E, y, "y", x) >= t:
            keep.append((x, y))
    for x, y, t in hs:
        # a short horizontal chord near the edge of a flat stroke is not a
        # centre point: require the stroke to be genuinely steep here
        tv = _pair_thickness(E, x, "x", y)
        if t <= wmax and tv > t and tv > 1.42 * wmin:
            keep.append((x, y))
    P = np.array(keep)
    P = P[np.argsort(P[:, 0], kind="stable")]
    return P, wmin


def rdp(P, eps):
    """Ramer-Douglas-Peucker simplification of an ordered polyline."""
    P = np.asarray(P)
    if len(P) < 3:
        return P
    keep = np.zeros(len(P), bool)
    keep[0] = keep[-1] = True
    stack = [(0, len(P) - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        a, b = P[i], P[j]
        ab = b - a
        n = np.hypot(*ab)
        seg = P[i + 1:j]
        if n == 0:
            dist = np.hypot(*(seg - a).T)
        else:
            dist = np.abs(ab[0] * (seg[:, 1] - a[1]) - ab[1] * (seg[:, 0] - a[0])) / n
        k = int(np.argmax(dist))
        if dist[k] > eps:
            m = i + 1 + k
            keep[m] = True
            stack += [(i, m), (m, j)]
    return P[keep]


def dash_centres(ds):
    """Centre segments of dashes drawn as filled capsules (2 lines + round caps).

    Returns an (N,2) array of points (two per dash: its two ends)."""
    pts = []
    for d in ds:
        ls = [it for it in d["items"] if it[0] == "l"]
        if len(ls) == 2:
            a0, a1 = np.array([ls[0][1].x, ls[0][1].y]), np.array([ls[0][2].x, ls[0][2].y])
            b0, b1 = np.array([ls[1][1].x, ls[1][1].y]), np.array([ls[1][2].x, ls[1][2].y])
            pts.append(0.5 * (a0 + b1))
            pts.append(0.5 * (a1 + b0))
        else:
            P = np.vstack(subpaths(d))
            pts.append(P.mean(0))
    P = np.array(pts)
    return P[np.argsort(P[:, 0], kind="stable")]


def polyline(d):
    """Vertices of a stroked path (thesis style): these are the plotted data points."""
    return np.vstack(subpaths(d))


# --------------------------------------------------------------------------
# box plots


def _is_diamond(d):
    r = d["rect"]
    P = np.vstack(subpaths(d))
    cx, cy = 0.5 * (r.x0 + r.x1), 0.5 * (r.y0 + r.y1)
    # a diamond has vertices at the middle of each side of its bounding box
    tips = [(cx, r.y0), (cx, r.y1), (r.x0, cy), (r.x1, cy)]
    return all(np.min(np.hypot(P[:, 0] - tx, P[:, 1] - ty)) < 0.12 for tx, ty in tips)


def _is_circle(d):
    return any(it[0] == "c" for it in d["items"]) and not any(it[0] == "l" for it in d["items"])


def boxplots(ps, plot_rect, box_fills, yax):
    """Read Origin box plots.

    ps: primitives of the panel; plot_rect: (x0,y0,x1,y1) inside the axes frame;
    box_fills: list of RGB fill colours used for the boxes; yax: Axis for values.
    Returns list of dicts sorted left to right with q1, q3, median, mean,
    whisker_lo, whisker_hi and outliers (data units) and the raw page coordinates.
    """
    X0, Y0, X1, Y1 = plot_rect
    inside = [d for d in ps if X0 - 0.5 <= center(d)[0] <= X1 + 0.5 and Y0 - 0.5 <= center(d)[1] <= Y1 + 0.5]
    boxes = []
    for d in inside:
        c = pcol(d)
        if d["type"] in ("f", "fs") and any(close(c, f) for f in box_fills) and d["rect"].width > 3:
            r = d["rect"]
            if not any(abs(b["x0"] - r.x0) < 0.3 and abs(b["x1"] - r.x1) < 0.3 for b in boxes):
                boxes.append(dict(x0=r.x0, x1=r.x1, ytop=r.y0, ybot=r.y1, fill=tuple(round(v, 3) for v in c)))
    boxes.sort(key=lambda b: b["x0"])
    hbars, markers = [], []
    for d in inside:
        c = pcol(d)
        if not is_dark(c):
            continue
        r = d["rect"]
        if r.height < 0.6 and r.width > 1.5:
            hbars.append((0.5 * (r.x0 + r.x1), 0.5 * (r.y0 + r.y1), r.width))
        elif 0.7 < r.width < 3.0 and 0.7 < r.height < 3.0 and abs(r.width - r.height) < 0.4:
            kind = "circle" if _is_circle(d) else ("diamond" if _is_diamond(d) else "square")
            markers.append((0.5 * (r.x0 + r.x1), 0.5 * (r.y0 + r.y1), kind, d["type"]))
    out = []
    for b in boxes:
        xc, bw = 0.5 * (b["x0"] + b["x1"]), b["x1"] - b["x0"]
        col_bars = [h for h in hbars if abs(h[0] - xc) < 0.35 * bw]
        med = [h for h in col_bars if h[2] > 0.8 * bw and b["ytop"] - 0.3 <= h[1] <= b["ybot"] + 0.3]
        caps = [h for h in col_bars if 0.25 * bw < h[2] < 0.75 * bw]
        up = [h[1] for h in caps if h[1] <= b["ytop"] + 0.3]
        lo = [h[1] for h in caps if h[1] >= b["ybot"] - 0.3]
        mk = [m for m in markers if abs(m[0] - xc) < 0.35 * bw]
        # Origin marks the mean with an open square (or open circle) and
        # outliers with filled diamonds
        means = [m for m in mk if m[2] in ("square", "circle")]
        outl = [m for m in mk if m[2] == "diamond"]
        # de-duplicate fill+outline pairs of the same marker
        def dedup(ms):
            res = []
            for m in sorted(ms, key=lambda m: m[1]):
                if res and abs(res[-1][1] - m[1]) < 0.3:
                    continue
                res.append(m)
            return res
        means, outl = dedup(means), dedup(outl)
        rec = dict(
            x_center_pt=xc,
            fill=b["fill"],
            q3_pt=b["ytop"], q1_pt=b["ybot"],
            median_pt=med[0][1] if len(med) == 1 else (np.nan if not med else min(med, key=lambda h: h[1])[1]),
            n_median_bars=len(med),
            whisker_hi_pt=min(up) if up else np.nan,
            whisker_lo_pt=max(lo) if lo else np.nan,
            mean_pt=means[0][1] if means else np.nan,
            n_mean=len(means),
            outlier_pts=[m[1] for m in outl],
        )
        for k in ("q3", "q1", "median", "whisker_hi", "whisker_lo", "mean"):
            v = rec[k + "_pt"]
            rec[k] = float(yax(v)) if np.isfinite(v) else np.nan
        rec["outliers"] = [float(yax(v)) for v in rec["outlier_pts"]]
        out.append(rec)
    return out


# --------------------------------------------------------------------------
# raster route


def render(page, clip, dpi):
    pix = page.get_pixmap(dpi=dpi, clip=pymupdf.Rect(*clip), alpha=False)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3]
    return img, pix


def pix_to_pt(clip, dpi, col, row):
    s = 72.0 / dpi
    return clip[0] + (np.asarray(col) + 0.5) * s, clip[1] + (np.asarray(row) + 0.5) * s


def raster_curve(img, clip, dpi, rgb, tol=60, along="x", min_run=1):
    """Centres of runs of pixels close to colour rgb (0-255).

    along='x': for each pixel column, centre row of each run -> (x_pt, y_pt).
    along='y': for each pixel row, centre column of each run.
    """
    ref = np.array(rgb, float)
    m = np.sqrt(((img.astype(float) - ref) ** 2).sum(-1)) < tol
    pts = []
    if along == "x":
        for c in range(m.shape[1]):
            rows = np.flatnonzero(m[:, c])
            if len(rows) < min_run:
                continue
            runs = np.split(rows, np.flatnonzero(np.diff(rows) > 1) + 1)
            for r in runs:
                if len(r) >= min_run:
                    pts.append(pix_to_pt(clip, dpi, c, r.mean()))
    else:
        for rr in range(m.shape[0]):
            cols = np.flatnonzero(m[rr, :])
            if len(cols) < min_run:
                continue
            runs = np.split(cols, np.flatnonzero(np.diff(cols) > 1) + 1)
            for r in runs:
                if len(r) >= min_run:
                    pts.append(pix_to_pt(clip, dpi, r.mean(), rr))
    return np.array(pts, float).reshape(-1, 2), m


def dist_to_polyline(P, L):
    """Distance (pt) from each point in P to polyline L (ordered vertices)."""
    A, B = L[:-1], L[1:]
    AB = B - A
    n2 = (AB ** 2).sum(1)
    n2[n2 == 0] = 1e-12
    out = np.empty(len(P))
    for i, p in enumerate(P):
        t = np.clip(((p - A) * AB).sum(1) / n2, 0, 1)
        Q = A + t[:, None] * AB
        out[i] = np.min(np.hypot(*(Q - p).T))
    return out


def trim_ends(P, d):
    """Remove arc length d from both ends of an ordered polyline (round-cap overhang)."""
    P = np.asarray(P, float)

    def cut(Q):
        seg = np.hypot(*np.diff(Q, axis=0).T)
        s = np.concatenate([[0], np.cumsum(seg)])
        if s[-1] <= d:
            return Q
        k = np.searchsorted(s, d)
        t = (d - s[k - 1]) / (s[k] - s[k - 1])
        p = Q[k - 1] + t * (Q[k] - Q[k - 1])
        return np.vstack([p, Q[k:]])

    P = cut(P)
    P = cut(P[::-1])[::-1]
    return P


def resample(xd, yd, grid):
    o = np.argsort(xd)
    return np.interp(grid, xd[o], yd[o])


def grid_vertices(xd, yd, grid, margin):
    """Values at grid points of a polyline whose vertices lie on the grid.

    xd, yd: dense centreline in data units. Each segment between consecutive
    grid points is straight, so a line is fitted to the centreline points of
    that segment away from its ends (margin) and evaluated at both ends. The
    vertex value is the mean of the two estimates from the adjoining segments;
    their difference is returned as a check of the on-grid assumption.
    """
    o = np.argsort(xd)
    xd, yd = xd[o], yd[o]
    left = np.full(len(grid), np.nan)   # estimate from the segment to the left
    right = np.full(len(grid), np.nan)  # estimate from the segment to the right
    for i in range(len(grid) - 1):
        a, b = grid[i], grid[i + 1]
        m = (xd > a + margin) & (xd < b - margin)
        if m.sum() < 3 or np.ptp(xd[m]) < 0.2 * (b - a):
            continue
        k = np.polyfit(xd[m], yd[m], 1)
        right[i] = np.polyval(k, a)
        left[i + 1] = np.polyval(k, b)
    val = np.nanmean(np.vstack([left, right]), axis=0)
    disagree = np.abs(left - right)
    miss = ~np.isfinite(val)
    val[miss] = np.interp(grid[miss], xd, yd)
    return val, disagree


def refine_normal(paths, P, half=1.5, smooth=7):
    """Re-centre centreline points by slicing the outline along the local normal.

    For each point the tangent is estimated from neighbours (window `smooth`),
    the outline is intersected with the normal line through the point, and the
    midpoint of the nearest crossing on each side (within `half` pt) is kept.
    Normal slices remove the small bias that vertical/horizontal chords have
    where the stroke is curved and keep the point order along the curve.
    """
    E = edges(paths)
    A, B = E[:, :2], E[:, 2:]
    D = B - A
    out = []
    n = len(P)
    for i in range(n):
        j0, j1 = max(0, i - smooth), min(n - 1, i + smooth)
        t = P[j1] - P[j0]
        L = np.hypot(*t)
        if L == 0:
            continue
        t = t / L
        nv = np.array([-t[1], t[0]])
        p = P[i]
        # solve p + s*nv = A + u*D for s,u
        den = D[:, 0] * nv[1] - D[:, 1] * nv[0]
        ok = np.abs(den) > 1e-12
        AP = A[ok] - p
        s = (AP[:, 0] * D[ok, 1] - AP[:, 1] * D[ok, 0]) / (-den[ok])
        u = (AP[:, 0] * nv[1] - AP[:, 1] * nv[0]) / (-den[ok])
        hit = (u >= 0) & (u <= 1) & (np.abs(s) <= half)
        s = s[hit]
        pos, neg = s[s > 0], s[s < 0]
        if len(pos) and len(neg):
            m = 0.5 * (pos.min() + neg.max())
            out.append(p + m * nv)
    return np.array(out)


def despike(P, k=4, tol=0.12):
    """Drop isolated centreline points lying more than tol (pt) off the chord
    joining their k-th neighbours on either side (spurious slice pairings)."""
    P = np.asarray(P)
    keep = np.ones(len(P), bool)
    for i in range(k, len(P) - k):
        a, b = P[i - k], P[i + k]
        ab = b - a
        n = np.hypot(*ab)
        if n == 0:
            continue
        d = abs(ab[0] * (P[i, 1] - a[1]) - ab[1] * (P[i, 0] - a[0])) / n
        # compare with the neighbours' own offsets so genuine corners survive
        dn = [abs(ab[0] * (P[j, 1] - a[1]) - ab[1] * (P[j, 0] - a[0])) / n for j in (i - 1, i + 1)]
        if d > tol and d > 3 * max(dn):
            keep[i] = False
    return P[keep]
