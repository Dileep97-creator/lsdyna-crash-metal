"""
Fixed-format LS-DYNA keyword deck writer.

Every card in an LS-DYNA keyword file is a set of fixed-width fields
(8 x 10 characters in the standard format). Hand-editing those is where
most deck errors come from, so every model in this repository is emitted
through this one module. If a card layout changes between solver
releases, it gets fixed here once instead of in fifty .k files.

Tested with plain CPython, no third-party dependencies.
"""

from __future__ import annotations

W = 10          # standard field width
NFIELD = 8      # fields per card line
MAXLEN = W * NFIELD


class CardError(ValueError):
    pass


def _fmt_float(v: float, w: int = W) -> str:
    """Shortest representation of v that fits in w chars and still reads
    as a real number to the solver."""
    if v == 0.0:
        return "0.0"
    for prec in range(9, 0, -1):
        s = f"{v:.{prec}g}"
        if "e" in s:
            # normalise 1e-06 -> 1.0e-6 style, still valid Fortran input
            mant, exp = s.split("e")
            if "." not in mant:
                mant += ".0"
            s = f"{mant}e{int(exp)}"
        elif "." not in s:
            s += ".0"
        if len(s) <= w:
            return s
    raise CardError(f"cannot fit float {v!r} in {w} columns")


def fmt(v, w: int = W) -> str:
    """Format one field, right-justified, exactly w characters."""
    if v is None or v == "":
        return " " * w
    if isinstance(v, bool):
        v = int(v)
    if isinstance(v, int):
        s = str(v)
    elif isinstance(v, float):
        # one column is reserved as a separator: a float that fills the field
        # exactly runs into the number before it, which is still legal fixed
        # format but unreadable and impossible to debug by eye
        s = _fmt_float(v, w - 1)
    else:
        s = str(v)
    if len(s) > w:
        raise CardError(f"field {v!r} is {len(s)} chars, field width is {w}")
    return s.rjust(w)


def card(*values) -> str:
    """Build one data card. Trailing blank fields are trimmed - LS-DYNA
    treats missing trailing fields as zero/default."""
    if len(values) > NFIELD:
        raise CardError(f"{len(values)} fields on one card, max is {NFIELD}")
    return "".join(fmt(v) for v in values).rstrip()


def comment(*names) -> str:
    """`$#` header line lining up with the fields below it. Purely
    cosmetic, but it is what makes a deck readable in a text editor."""
    out = "$#"
    first = True
    for n in names:
        out += str(n).rjust(W - 2 if first else W)
        first = False
    return out


class Deck:
    """Accumulates keyword blocks and writes a .k file."""

    def __init__(self, title: str = "", include: bool = False):
        """include=True writes a file meant to be pulled in with *INCLUDE.

        Such a file must not carry *KEYWORD or *END. An *END inside an
        included file terminates input reading, and everything after the
        *INCLUDE in the parent deck is silently dropped - no sections, no
        materials, no contacts. The solver then reports thousands of
        "invalid material" errors on elements that were read perfectly
        well, which points nowhere near the actual cause.
        """
        self.include_file = include
        self.lines: list[str] = []
        if include:
            if title:
                self.lines.append("$ " + title[:78])
        else:
            self.lines.append("*KEYWORD")
            if title:
                self.lines += ["*TITLE", title[:80]]

    # -- low level -------------------------------------------------------
    def raw(self, *lines: str) -> "Deck":
        self.lines.extend(lines)
        return self

    def note(self, text: str) -> "Deck":
        for ln in text.strip("\n").split("\n"):
            self.lines.append("$ " + ln)
        return self

    def kw(self, name: str, *cards) -> "Deck":
        """Emit a keyword followed by its cards.

        Each element of *cards is either a pre-built string, or a
        (header_tuple, values_tuple) pair, or a bare values tuple.
        """
        self.lines.append("*" + name.upper().lstrip("*"))
        return self.cards(*cards)

    def cards(self, *cards) -> "Deck":
        """Emit cards only - used after a *..._TITLE keyword whose title
        line has already been written."""
        for c in cards:
            if isinstance(c, str):
                self.lines.append(c)
            elif (isinstance(c, tuple) and len(c) == 2
                  and isinstance(c[0], (list, tuple))
                  and isinstance(c[1], (list, tuple))):
                self.lines.append(comment(*c[0]))
                self.lines.append(card(*c[1]))
            else:
                self.lines.append(card(*c))
        return self

    # -- common blocks ---------------------------------------------------
    def include(self, path: str) -> "Deck":
        return self.kw("INCLUDE", path)

    def part(self, pid: int, secid: int, mid: int, title: str,
             hgid: int = 0) -> "Deck":
        return self.kw(
            "PART", title[:80],
            (("pid", "secid", "mid", "eosid", "hgid", "grav", "adpopt", "tmid"),
             (pid, secid, mid, 0, hgid, 0, 0, 0)))

    def define_curve(self, lcid: int, xy, sfa: float = 1.0, sfo: float = 1.0,
                     title: str = "") -> "Deck":
        self.lines.append("*DEFINE_CURVE_TITLE")
        self.lines.append((title or f"curve {lcid}")[:80])
        self.lines.append(comment("lcid", "sidr", "sfa", "sfo",
                                  "offa", "offo", "dattyp", "lcint"))
        self.lines.append(card(lcid, 0, sfa, sfo, 0.0, 0.0, 0, 0))
        for x, y in xy:
            self.lines.append(fmt(float(x), 20) + fmt(float(y), 20))
        return self

    def end(self) -> "Deck":
        if not self.include_file:
            self.lines.append("*END")
        return self

    def write(self, path) -> str:
        if not self.include_file and (not self.lines or self.lines[-1] != "*END"):
            self.end()
        text = "\n".join(self.lines) + "\n"
        with open(path, "w") as fh:
            fh.write(text)
        return text


# ---------------------------------------------------------------------
# Reusable control / database blocks. Every solver deck in this repo
# starts from these so the QA settings are identical across studies.
# ---------------------------------------------------------------------

def control_explicit_crash(endtim: float, dt2ms: float = -1.0e-6,
                           tssfac: float = 0.9) -> list[str]:
    d = Deck()
    d.lines = []
    d.kw("CONTROL_TERMINATION",
         (("endtim", "endcyc", "dtmin", "endeng", "endmas", "nosol"),
          (endtim, 0, 0.0, 0.0, 0.0, 0)))
    d.kw("CONTROL_TIMESTEP",
         (("dtinit", "tssfac", "isdo", "tslimt", "dt2ms", "lctm", "erode", "ms1st"),
          (0.0, tssfac, 0, 0.0, dt2ms, 0, 1, 0)))
    d.kw("CONTROL_ENERGY",
         (("hgen", "rwen", "slnten", "rylen", "irgen"),
          (2, 2, 2, 2, 2)))
    d.kw("CONTROL_HOURGLASS",
         (("ihq", "qh"), (4, 0.05)))
    d.kw("CONTROL_SHELL",
         (("wrpang", "esort", "irnxx", "istupd", "theory", "bwc", "miter", "proj"),
          (20.0, 1, -1, 1, 2, 2, 1, 0)))
    # *CONTROL_CONTACT takes TWO mandatory cards. Omitting the second one
    # does not raise "missing card" - the reader swallows the next keyword
    # line as data, then desynchronises and blames whatever follows.
    d.kw("CONTROL_CONTACT",
         (("slsfac", "rwpnal", "islchk", "shlthk", "penopt", "thkchg", "orien", "enmass"),
          (0.1, 0.0, 2, 1, 4, 1, 1, 0)),
         (("usrstr", "usrfrc", "nsbcs", "interm", "xpene", "ssthk", "ecdt", "tiedprj"),
          (0, 0, 0, 0, 4.0, 0, 0, 0)))
    d.kw("CONTROL_ACCURACY",
         (("osu", "inn", "pidosu", "iacc"), (1, 4, 0, 1)))
    return d.lines


def database_standard(dt_ascii: float, dt_d3plot: float) -> list[str]:
    d = Deck()
    d.lines = []
    hdr = ("dt", "binary", "lcur", "ioopt")
    for name in ("GLSTAT", "MATSUM", "RCFORC", "SLEOUT", "NODOUT",
                 "ELOUT", "SECFORC", "SPCFORC", "RWFORC", "BNDOUT"):
        d.kw("DATABASE_" + name, ((hdr), (dt_ascii, 3, 0, 1)))
    d.kw("DATABASE_BINARY_D3PLOT",
         (("dt", "lcdt", "beam", "npltc", "psetid"),
          (dt_d3plot, 0, 0, 0, 0)))
    d.kw("DATABASE_EXTENT_BINARY",
         (("neiph", "neips", "maxint", "strflg", "sigflg", "epsflg", "rltflg", "engflg"),
          (0, 0, -3, 1, 1, 1, 1, 1)),
         (("cmpflg", "ieverp", "beamip", "dcomp", "shge", "stssz", "n3thdt", "ialemat"),
          (0, 1, 0, 1, 2, 3, 2, 1)))
    return d.lines
