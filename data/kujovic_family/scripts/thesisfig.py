"""Helpers for the thesis figures, which are stroked vector paths with text tick labels."""
import re
import numpy as np
import pymupdf
import vecfig as V

NUM = re.compile(r"^-?\d+(\.\d+)?(e-?\d+)?$")


def spans(page, clip):
    out = []
    for b in page.get_text("dict", clip=pymupdf.Rect(*clip))["blocks"]:
        for ln in b.get("lines", []):
            for s in ln["spans"]:
                t = s["text"].strip()
                if t:
                    x0, y0, x1, y1 = s["bbox"]
                    out.append((t, 0.5 * (x0 + x1), 0.5 * (y0 + y1), s["bbox"], ln["dir"]))
    return out


def find_axes(page, clip, minlen=50):
    """Candidate axis lines with ticks inside clip."""
    ps = V.prims(page, clip)
    H = [d for d in ps if V.is_dark(V.pcol(d)) and d["rect"].height < 0.6 and d["rect"].width > minlen]
    Vv = [d for d in ps if V.is_dark(V.pcol(d)) and d["rect"].width < 0.6 and d["rect"].height > minlen]
    xs, ys = [], []
    for d in H:
        r = d["rect"]
        for pos in (0.5 * (r.y0 + r.y1), r.y0, r.y1):
            t = V.find_ticks(ps, "x", pos, (r.x0, r.x1))
            if len(t) >= 2:
                xs.append((pos, (r.x0, r.x1), t))
                break
    for d in Vv:
        r = d["rect"]
        for pos in (0.5 * (r.x0 + r.x1), r.x0, r.x1):
            t = V.find_ticks(ps, "y", pos, (r.y0, r.y1))
            if len(t) >= 2:
                ys.append((pos, (r.y0, r.y1), t))
                break
    return ps, xs, ys


def label_values(page, axis, line_pos, ticks, search=16.0):
    """Read the numeric text label next to each major tick (None if absent)."""
    vals = []
    if axis == "x":
        clip = (min(ticks) - 15, line_pos - 2, max(ticks) + 15, line_pos + search)
    else:
        clip = (line_pos - search - 20, min(ticks) - 8, line_pos + 2, max(ticks) + 8)
    allS = spans(page, (clip[0] - 5, clip[1] - 8, clip[2] + 12, clip[3] + 2))
    S = [s for s in spans(page, clip) if NUM.match(s[0])]
    # "10" followed by a superscript exponent: combine into 10**exp
    comb = []
    for s in S:
        if s[0] == "10":
            bx = s[3]
            sup = [e for e in allS if re.match(r"^[-\u2212]?\d+$", e[0]) and e is not s
                   and bx[2] - 1.5 <= e[3][0] <= bx[2] + 3 and e[2] < s[2] and abs(e[2] - s[2]) < 6
                   and (e[3][3] - e[3][1]) < (bx[3] - bx[1])]
            if sup:
                ex = float(sup[0][0].replace("\u2212", "-"))
                comb.append(("1e%d" % ex, s[1], s[2], s[3], s[4]))
                continue
        comb.append(s)
    S = comb
    for c in ticks:
        if axis == "x":
            cand = [s for s in S if abs(s[1] - c) < 6 and s[2] > line_pos]
            cand.sort(key=lambda s: abs(s[1] - c))
        else:
            cand = [s for s in S if abs(s[2] - c) < 4 and s[1] < line_pos]
            cand.sort(key=lambda s: abs(s[2] - c))
        vals.append(float(cand[0][0]) if cand else None)
    return vals


def axis_auto(page, ps, axis, line_pos, span, values=None, log=False, label=""):
    t = V.major_ticks(V.find_ticks(ps, axis, line_pos, span))
    if values is None:
        values = label_values(page, axis, line_pos, t)
        if any(v is None for v in values):
            raise RuntimeError(f"{label}: missing tick labels {values} at {np.round(t, 2)}")
    if len(values) != len(t):
        raise RuntimeError(f"{label}: {len(t)} ticks {np.round(t, 2)} vs {len(values)} values {values}")
    return V.Axis(t, values, log=log), values


def _is_tick(P, axes):
    """True for a single straight piece that is a tick mark on one of the axes."""
    if axes is None or len(P) != 2:
        return False
    xline_y, yline_x = axes
    (x0, y0), (x1, y1) = P
    if np.hypot(x1 - x0, y1 - y0) > 3.5:  # ticks are at most ~3.2 pt long
        return False
    if xline_y is not None and abs(x0 - x1) < 1e-3 and (abs(y0 - xline_y) < 0.3 or abs(y1 - xline_y) < 0.3):
        return True
    if yline_x is not None and abs(y0 - y1) < 1e-3 and (abs(x0 - yline_x) < 0.3 or abs(x1 - yline_x) < 0.3):
        return True
    return False


def stroke_curves(ps, color, rect, tol=0.06, min_items=5, dash_max_len=3.5, axes=None):
    """Polylines of one colour inside rect.

    Long drawings (>= min_items segments) are returned one per curve, with their
    vertices. Short pieces (dashes) are merged into one point set sorted by x.
    Short pieces longer than dash_max_len (legend keys) are ignored.
    """
    X0, Y0, X1, Y1 = rect
    solid, dash = [], []
    for d in ps:
        if d["type"] not in ("s", "fs") or not V.close(d.get("color"), color, tol):
            continue
        r = d["rect"]
        if r.x1 < X0 or r.x0 > X1 or r.y1 < Y0 or r.y0 > Y1:
            continue
        n = len(d["items"])
        if n >= min_items:
            solid.append(V.polyline(d))
        else:
            P = V.polyline(d)
            L = np.sum(np.hypot(*np.diff(P, axis=0).T))
            if L <= dash_max_len and not _is_tick(P, axes):
                dash.append(P)
    D = np.vstack(dash) if dash else np.zeros((0, 2))
    if len(D):
        D = D[np.argsort(D[:, 0], kind="stable")]
        # drop duplicated joint points
        keep = np.ones(len(D), bool)
        keep[1:] = np.hypot(*np.diff(D, axis=0).T) > 1e-3
        D = D[keep]
    return solid, D


def colours(ps, rect, min_items=1):
    """Stroke colours present in rect with item counts (for exploring)."""
    from collections import Counter
    c = Counter()
    X0, Y0, X1, Y1 = rect
    for d in ps:
        if d["type"] in ("s", "fs"):
            r = d["rect"]
            if r.x1 < X0 or r.x0 > X1 or r.y1 < Y0 or r.y0 > Y1:
                continue
            col = tuple(round(v, 3) for v in d["color"])
            c[col] += len(d["items"])
    return c
