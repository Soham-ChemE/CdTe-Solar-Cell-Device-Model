"""Small toolkit for driving SCAPS 3.3.11 headless: edit .def files, build batch scripts, parse results.

All edits are plain-text edits of the SCAPS definition file, so every variant can be diffed against
its parent. Units inside .def files are SI (m, m^-3, m^2/Vs, m/s); helpers take the SI value.
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCAPS_DIR = REPO / "tools/wineprefix/drive_c/Program Files (x86)/Scaps3311"
DEFS = REPO / "scaps/defs"
SCRIPTS = REPO / "scaps/scripts"
RESULTS = REPO / "scaps/results"


# ----------------------------------------------------------------------------- .def editing
class DefFile:
    """A SCAPS problem-definition file split into header (incl. back contact), layers, and tail."""

    def __init__(self, text: str, name: str = ""):
        text = text.replace("\r", "")
        parts = text.split("\nlayer\n")
        self.head = parts[0]
        body = parts[1:]
        last, sep, tail = body[-1].partition("front contact")
        if not sep:
            raise ValueError("no front contact section")
        self.layers = body[:-1] + [last]
        self.tail = "front contact" + tail
        self.name = name

    @classmethod
    def load(cls, path: Path | str) -> "DefFile":
        p = Path(path)
        return cls(p.read_text(encoding="latin-1"), p.stem)

    def text(self) -> str:
        return self.head + "".join("\nlayer\n" + b for b in self.layers) + self.tail

    def save(self, name: str) -> Path:
        out = DEFS / f"{name}.def"
        out.write_text(self.text().replace("\n", "\r\n"), encoding="latin-1")
        return out

    # -- layer lookup
    def layer_names(self) -> list[str]:
        return [re.search(r"^name : (.*)$", b, re.M).group(1).strip() for b in self.layers]

    def idx(self, layer: int | str) -> int:
        if isinstance(layer, int):
            return layer
        names = self.layer_names()
        return names.index(layer)

    def get(self, layer: int | str, key: str) -> list[str]:
        b = self.layers[self.idx(layer)]
        m = re.search(r"^" + re.escape(key) + r"\s*:\s*(.*)$", b, re.M)
        return m.group(1).split() if m else []

    # -- parameter setters
    def set_param(self, layer: int | str, key: str, value: float) -> "DefFile":
        """Set a graded-parameter line (eps, chi, Eg, Nc, Nv, mu_n, mu_p, Na(...), Nd(...), Nt(...), K_rad).
        The value is written to the y=0, y=1 and both edge columns so the layer stays uniform."""
        i = self.idx(layer)
        b = self.layers[i]
        pat = re.compile(r"^(" + re.escape(key) + r"\s*:)(.*)$", re.M)
        m = pat.search(b)
        if not m:
            raise KeyError(f"{key} not found in layer {self.layer_names()[i]}")
        cols = m.group(2).split("\t")
        num_idx = [k for k, c in enumerate(cols) if c.strip()]
        fmt = f"{value:.6e}"
        for k in (0, 1, 2, 5, 6):
            cols[num_idx[k]] = " " + fmt
        self.layers[i] = b[: m.start(2)] + "\t".join(cols) + b[m.end(2):]
        return self

    def set_line(self, layer: int | str, key: str, value_text: str) -> "DefFile":
        i = self.idx(layer)
        b = self.layers[i]
        new, n = re.subn(r"^" + re.escape(key) + r"\s*:.*$", f"{key} : {value_text}", b, count=1, flags=re.M)
        if not n:
            raise KeyError(key)
        self.layers[i] = new
        return self

    def set_thickness(self, layer: int | str, d_m: float) -> "DefFile":
        return self.set_line(layer, "d", f"{d_m:.3e} [m]")

    def set_absorption_file(self, layer: int | str, fname: str) -> "DefFile":
        i = self.idx(layer)
        b = self.layers[i]
        b = re.sub(r"^absorptionmodel pure A material \(y=0\) : .*$",
                   "absorptionmodel pure A material (y=0) : from file", b, flags=re.M)
        b = re.sub(r"^absorptionfile pure A material \(y=0\) : .*$",
                   f"absorptionfile pure A material (y=0) : {fname}", b, flags=re.M)
        b = re.sub(r"^absorption pure B material \(y=1\), file : .*$",
                   f"absorption pure B material (y=1), file : {fname}", b, flags=re.M)
        self.layers[i] = b
        return self

    def set_absorption_sqrt(self, layer: int | str, A: float, B: float = 0.0) -> "DefFile":
        """Replace the layer's absorption with the SCAPS sqrt(hv-Eg) model, alpha = (A + B/hv) sqrt(hv-Eg).
        A in 1/(m sqrt(eV)). A = 0 switches absorption off."""
        i = self.idx(layer)
        b = self.layers[i]
        start = b.index("absorptionmodel pure A material")
        # end of the absorption section = first blank line or next section keyword after start
        m = re.search(r"\n(?:srhrecombination|interface properties|\n)", b[start:])
        end = start + (m.start() if m else len(b) - start)
        block = (
            "absorptionmodel pure A material (y=0) : coefficients A and B\n"
            f"A : {A:.3e} [/(m*sqrt(eV))]\n"
            f"B : {B:.3e} [sqrt(eV)/m]\n"
            "absorption pure B material (y=1), model : coefficients A and B\n"
            f"pure B material (y=1), A : {A:.3e} [/(m*sqrt(eV))]\n"
            f"pure B material (y=1), B : {B:.3e} [sqrt(eV)/m]"
        )
        self.layers[i] = b[:start] + block + b[end:]
        return self

    def add_defect_block(self, layer: int | str, block: str) -> "DefFile":
        """Insert a complete 'srhrecombination' block (copied from a reference .def) into a layer."""
        i = self.idx(layer)
        b = self.layers[i]
        k = b.find("\ninterface properties")
        if k < 0:                       # last (front-most) layer: no interface section follows it
            self.layers[i] = b.rstrip("\n") + "\n\n" + block.strip("\n") + "\n\n\n"
        else:
            self.layers[i] = b[:k].rstrip("\n") + "\n\n" + block.strip("\n") + "\n" + b[k:]
        return self

    def defect_blocks(self, layer: int | str) -> list[str]:
        b = self.layers[self.idx(layer)]
        out = []
        for m in re.finditer(r"srhrecombination\n\n.*?\nEt :[^\n]*", b, re.S):
            out.append(m.group(0))
        return out

    # -- structural edits
    def duplicate_layer(self, src: int | str, new_name: str, insert_at: int) -> "DefFile":
        """Copy layer `src` and insert it at position `insert_at` (0 = back/left) under a new name."""
        block = self.layers[self.idx(src)]
        block = re.sub(r"^name : .*$", f"name : {new_name}", block, count=1, flags=re.M)
        self.layers.insert(insert_at, block)
        return self

    def rename_layer(self, layer: int | str, new_name: str) -> "DefFile":
        i = self.idx(layer)
        self.layers[i] = re.sub(r"^name : .*$", f"name : {new_name}", self.layers[i], count=1, flags=re.M)
        return self

    def remove_defects(self, layer: int | str) -> "DefFile":
        """Delete every bulk 'srhrecombination' block of a layer."""
        i = self.idx(layer)
        self.layers[i] = re.sub(r"\n*srhrecombination\n\n.*?\nEt :[^\n]*\n?", "\n", self.layers[i], flags=re.S)
        return self

    def set_front_workfunction(self, phi_eV: float | None) -> "DefFile":
        """Fixed front-contact work function, or flat band when phi_eV is None."""
        t = self.tail
        if phi_eV is None:
            t = re.sub(r"^flatband : \d", "flatband : 1", t, count=1, flags=re.M)
        else:
            t = re.sub(r"^flatband : \d", "flatband : 0", t, count=1, flags=re.M)
            t = re.sub(r"^Fi_m :.*$", f"Fi_m :  {phi_eV:.4f} [eV]", t, count=1, flags=re.M)
        self.tail = t
        return self

    def set_back_workfunction(self, phi_eV: float) -> "DefFile":
        h = self.head
        h = re.sub(r"^flatband : \d", "flatband : 0", h, count=1, flags=re.M)
        h = re.sub(r"^Fi_m :.*$", f"Fi_m :   {phi_eV:.6f} [eV]", h, count=1, flags=re.M)
        self.head = h
        return self


# ----------------------------------------------------------------------------- scripts
@dataclass
class Batch:
    """Builds one SCAPS script that runs many cases in a single SCAPS launch."""

    name: str
    lines: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.lines += ["set errorhandling.overwritefile", "set quitscript.quitSCAPS"]

    def case(self, deffile: str, out: str, *, T: float = 300.0, stopV: float = 2.2, step: float = 0.01,
             sets: list[str] | None = None, generation_file: str | None = None,
             qe: tuple[float, float, float] | None = None):
        """One case. qe=(start_nm, stop_nm, step_nm) also runs a QE sweep and saves OUT.qe."""
        L = self.lines
        L.append(f"load definitionfile {deffile}")
        if generation_file:
            L.append(f"load generationfile {generation_file}")
        L += ["clear actions", f"action workingpoint.temperature {T:g}"]
        if generation_file:
            L += ["action generation_specified", "action generation_defined.fromfile"]
        L += ["action light", "action iv.doiv", "action iv.startV 0", f"action iv.stopV {stopV:g}",
              f"action iv.increment {step:g}", "action iv.stopafterVoc"]
        if qe:
            L += ["action qe.doqe", f"action qe.startlambda {qe[0]:g}", f"action qe.stoplambda {qe[1]:g}",
                  f"action qe.increment {qe[2]:g}"]
        for s in sets or []:
            L.append(s)
        # SCAPS keeps every computed curve in its I-V panel and 'save results.iv' writes the first one,
        # so the panel must be cleared before each calculation (found 2026-11-15: an uncleared batch
        # saved the first case 80 times).
        L += ["clear simulations", "calculate", f"save results.iv {out}.iv"]
        if qe:
            L.append(f"save results.qe {out}.qe")
        self.outputs.append((out, deffile))

    def write(self) -> Path:
        p = SCRIPTS / f"{self.name}.script"
        p.write_text("\n".join(self.lines) + "\n", encoding="latin-1")
        return p

    def run(self, timeout: int = 1800, prefix: str = "wineprefix", grace: float = 60.0) -> subprocess.CompletedProcess:
        """Run the script in one Wine prefix. Watchdog: SCAPS sometimes finishes every case but never exits
        (seen 2026-11-16, 0% CPU, with and without convergence errors). Once every file the script saves exists,
        is newer than the launch and has been quiet for `grace` seconds, the SCAPS process is ended so that
        run_scaps.sh copies the results instead of waiting for the timeout."""
        import time as _time
        p = self.write()
        expected = [l.split(None, 2)[2].strip() for l in self.lines if l.startswith("save results.")]
        resdir = REPO / "tools" / prefix / "drive_c/Program Files (x86)/Scaps3311/results"
        args = ["bash", str(REPO / "scripts/run_scaps.sh"), str(p)]
        t0 = _time.time() - 2
        proc = subprocess.Popen(args, env={"SCAPS_TIMEOUT": str(timeout), "SCAPS_PREFIX": prefix,
                                           "PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "HOME": str(Path.home())},
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        killed = False
        while proc.poll() is None:
            _time.sleep(5)
            if killed or not expected:
                continue
            files = [resdir / f for f in expected]
            if all(f.exists() and f.stat().st_mtime >= t0 for f in files):
                newest = max(f.stat().st_mtime for f in files)
                if _time.time() - newest > grace:
                    subprocess.run(["pkill", "-f", r"scaps3311\.exe .*" + re.escape(p.name)], capture_output=True)
                    # A killed SCAPS leaves the prefix's wineserver in a state where the next SCAPS launch hangs
                    # at start-up (seen 2026-11-16), so shut the prefix's wineserver down as well.
                    _time.sleep(3)
                    subprocess.run([str(Path.home() / "Applications/Wine Devel.app/Contents/Resources/wine/bin/wineserver"), "-k"],
                                   env={"WINEPREFIX": str(REPO / "tools" / prefix), "PATH": "/usr/bin:/bin"}, capture_output=True)
                    killed = True
        out, err = proc.communicate()
        if killed:
            out += f"\n[watchdog] SCAPS ended after all {len(expected)} outputs were written\n"
        return subprocess.CompletedProcess(args, proc.returncode, out, err)


def available_prefixes() -> list[str]:
    """Wine prefixes under tools/ that contain a SCAPS install (wineprefix, wineprefix_1, ...)."""
    out = []
    for d in sorted((REPO / "tools").glob("wineprefix*")):
        if (d / "drive_c/Program Files (x86)/Scaps3311/scaps3311.exe").exists():
            out.append(d.name)
    return out


def run_parallel(name: str, cases: list[dict], n_workers: int | None = None, timeout: int = 3600) -> list:
    """Split cases round-robin over the available SCAPS prefixes and run them concurrently.
    Each case dict holds the keyword arguments of Batch.case (deffile, out, ...). Returns the
    CompletedProcess of each worker. Outputs land in scaps/results as usual."""
    from concurrent.futures import ThreadPoolExecutor
    prefixes = available_prefixes()
    # Default 2 concurrent SCAPS copies (since 2026-11-16): with 4 DFT ranks on a 16 GB Mac, 4-5 copies drove
    # swap to 4.8 GB and SCAPS stalled under Rosetta. Pass n_workers explicitly to use more.
    n = min(n_workers or 2, len(prefixes), max(1, len(cases)))
    batches = [Batch(f"{name}_w{k}") for k in range(n)]
    for i, c in enumerate(cases):
        c = dict(c)
        batches[i % n].case(c.pop("deffile"), c.pop("out"), **c)
    with ThreadPoolExecutor(max_workers=n) as ex:
        futs = [ex.submit(b.run, timeout, prefixes[k]) for k, b in enumerate(batches)]
        return [f.result() for f in futs]


# ----------------------------------------------------------------------------- results
def read_iv(path: Path | str) -> dict:
    """Parse a SCAPS .iv result file: Voc, Jsc, FF, eta and the J-V table (V, Jtot, J_SRH, J_rad ...)."""
    t = Path(path).read_text(encoding="latin-1").replace("\r", "")
    out: dict = {}
    m = re.search(r"problem definition file :\s*(.*)$", t, re.M)
    out["deffile"] = m.group(1).strip().split("\\")[-1] if m else ""
    for key, pat in [("Voc", r"Voc\s*=\s*([-\d.eE+]+)"), ("Jsc", r"Jsc\s*=\s*([-\d.eE+]+)"),
                     ("FF", r"FF\s*=\s*([-\d.eE+]+)"), ("eta", r"eta\s*=\s*([-\d.eE+]+)")]:
        m = re.search(pat, t)
        out[key] = float(m.group(1)) if m else float("nan")
    lines = t.split("\n")
    try:
        i = next(k for k, l in enumerate(lines) if l.strip().startswith("v(V)"))
        header = lines[i].split("\t")
        rows = []
        for l in lines[i + 1:]:
            p = l.split()
            if len(p) < 2:
                if rows:
                    break
                continue
            try:
                rows.append([float(v) for v in p])
            except ValueError:
                break
        out["columns"] = [h.strip() for h in header]
        out["table"] = rows
    except StopIteration:
        out["columns"], out["table"] = [], []
    return out


def read_qe(path: Path | str) -> dict:
    """Parse a SCAPS .qe result file into wavelength (nm) and QE (%) arrays."""
    t = Path(path).read_text(encoding="latin-1").replace("\r", "")
    lines = t.split("\n")
    out = {"deffile": "", "lambda_nm": [], "qe_pct": []}
    m = re.search(r"problem definition file :\s*(.*)$", t, re.M)
    out["deffile"] = m.group(1).strip().split("\\")[-1] if m else ""
    try:
        i = next(k for k, l in enumerate(lines) if l.strip().lower().startswith(("wavelength", "lambda(nm)")))
    except StopIteration:
        return out
    for l in lines[i + 1:]:
        p = l.split()
        if len(p) < 2:
            if out["lambda_nm"]:
                break
            continue
        try:
            out["lambda_nm"].append(float(p[0])); out["qe_pct"].append(float(p[1]))
        except ValueError:
            break
    return out


def at_short_circuit(res: dict, column: str) -> float:
    cols = res.get("columns", [])
    if not res.get("table") or column not in cols:
        return float("nan")
    return res["table"][0][cols.index(column)]
