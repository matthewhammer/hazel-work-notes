#!/usr/bin/env python3
"""The work-notes gallery's pictures (^ticket(182)): one plate per note, drawn
for what that note records, in the house style (ink on cream, hatching for
tone, a little oxblood, ochre and green), each with ids of its own since they
share a page. Writes each note's `art` into work-notes/gallery.json.

  python3 dashboard/gallery_art.py

A new note's picture: add a function here, drawn for that note, and a line
in ART."""
import json, os

DIR = os.path.dirname(os.path.realpath(__file__))
GALLERY = os.path.join(os.path.dirname(DIR), "work-notes", "gallery.json")
INK, PAPER, OX, OCHRE, GREEN = "#2b2118", "#f3ead6", "#7b2d26", "#c4902f", "#3d6b45"

def plate(sid, label, body):
    return (f'<svg viewBox="0 0 240 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{label}"><defs>'
            f'<pattern id="h{sid}" width="3.4" height="3.4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="3.4" stroke="{INK}" stroke-width="0.7"/></pattern>'
            f'<pattern id="x{sid}" width="3.4" height="3.4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><path d="M0 0V3.4M0 0H3.4" stroke="{INK}" stroke-width="0.6"/></pattern>'
            f'<pattern id="l{sid}" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(-30)"><line x1="0" y1="0" x2="0" y2="4" stroke="{INK}" stroke-width="0.4"/></pattern>'
            f'</defs><rect width="240" height="150" fill="{PAPER}"/>'
            f'<g fill="none" stroke="{INK}" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.4">'
            + body.replace("#H", f"url(#h{sid})").replace("#X", f"url(#x{sid})").replace("#L", f"url(#l{sid})") +
            f'</g><rect x="5" y="5" width="230" height="140" fill="none" stroke="{INK}" stroke-width="1"/>'
            f'<rect x="8.5" y="8.5" width="223" height="133" fill="none" stroke="{INK}" stroke-width="0.5"/></svg>')

def doll(x, y, s=1.0, shirt="#H", arms="down", back=False):
    """a paper-doll friend, feet at (x, y), about 46 tall at s=1"""
    k = lambda v: round(v * s, 1)
    arm = {"down": f"M{x-k(6)} {y-k(30)} L{x-k(13)} {y-k(16)} M{x+k(6)} {y-k(30)} L{x+k(13)} {y-k(16)}",
           "up": f"M{x-k(6)} {y-k(30)} L{x-k(12)} {y-k(46)} M{x+k(6)} {y-k(30)} L{x+k(12)} {y-k(46)}",
           "climb": f"M{x-k(6)} {y-k(30)} L{x-k(10)} {y-k(44)} M{x+k(6)} {y-k(30)} L{x+k(10)} {y-k(36)}"}[arms]
    hair = (f'<path d="M{x-k(6.5)} {y-k(38)} q{k(6.5)} {k(-9)} {k(13)} 0 v{k(-1)} q{k(-6.5)} {k(-11)} {k(-13)} 0 z" fill="{INK}" stroke="none"/>' if back else
            f'<path d="M{x-k(6.5)} {y-k(41)} q{k(6.5)} {k(-7)} {k(13)} 0" stroke-width="2"/>')
    return (f'<circle cx="{x}" cy="{y-k(40)}" r="{k(6.5)}" fill="{PAPER}"/>' + hair +
            f'<path d="M{x-k(7)} {y-k(32)} h{k(14)} l{k(2)} {k(16)} h{k(-18)} z" fill="{shirt}"/>'
            f'<path d="{arm}"/><path d="M{x-k(4)} {y-k(16)} L{x-k(5)} {y} M{x+k(4)} {y-k(16)} L{x+k(5)} {y}"/>')

def evening_1016():
    tallies = ""
    for g in range(6):
        x0, y0 = 113 + (g % 3) * 12, 52 + (g // 3) * 15
        tallies += "".join(f'<path d="M{x0 + i * 2.2} {y0} v9"/>' for i in range(4)) + f'<path d="M{x0 - 1} {y0 + 8} l9 -7"/>'
    tallies += "".join(f'<path d="M{113 + i * 2.2} 82 v9"/>' for i in range(3))
    return plate("a1810", "a frozen laptop with no battery, a crash log of tally marks, and a castle door open over a pit", (
        '<path d="M14 128 H226" stroke-width="1"/>'
        # the laptop, its screen frozen dark, icicles hanging
        '<path d="M22 112 H94 L102 124 H14 Z" fill="#L"/><rect x="27" y="62" width="62" height="49" rx="2"/>'
        '<rect x="31" y="66" width="54" height="41" fill="#X"/>'
        f'<path d="M35 66 l3 10 l3 -10 M46 66 l2 6 l2 -6 M60 66 l3 12 l3 -12 M74 66 l2 7 l2 -7" fill="{PAPER}" stroke-width="1"/>'
        # its battery, missing
        f'<rect x="43" y="36" width="27" height="14" rx="2" stroke="{OX}" stroke-dasharray="3 2"/><rect x="70" y="40.5" width="3" height="5" fill="{OX}" stroke="none"/>'
        f'<text x="56.5" y="47.5" font-family="Georgia, serif" font-size="12" font-weight="bold" text-anchor="middle" fill="{OX}" stroke="none">?</text>'
        # the crash log: a scroll of tally marks, 33 of them
        f'<path d="M108 42 H152 V112 H108 Z" fill="{PAPER}"/><path d="M108 42 q-5 0 -5 5 q0 5 5 5 M152 112 q5 0 5 -5 q0 -5 -5 -5"/>'
        f'<g stroke="{OX}" stroke-width="1.1">{tallies}</g><path d="M113 100 h32 M113 105 h24" stroke-width="0.8"/>'
        # a castle doorway, its door swung open, the pit before it glowing
        '<path d="M166 128 V72 Q186 50 206 72 V128" stroke-width="1.8"/><path d="M170 128 V73 Q186 56 202 73 V128 Z" fill="#X"/>'
        f'<path d="M176 126 V80 Q186 70 196 80 V126 Z" fill="{OCHRE}" opacity="0.6" stroke="none"/>'
        f'<path d="M166 128 V72 L152 80 V126 Z" fill="#H"/><circle cx="156" cy="104" r="1.6" fill="{INK}"/>'
        f'<ellipse cx="186" cy="132" rx="20" ry="4.5" fill="{INK}"/><path d="M170 134 q16 5 32 0" stroke="{OCHRE}" stroke-width="1"/>'
        '<path d="M212 128 V96 M216 128 V104 M220 128 V100" stroke-width="0.8"/>'))

def late_morning_1016():
    waves = "".join(f'<path d="M14 {y} ' + " ".join(f"q6 -3 12 0" for _ in range(17)) + '" stroke-width="0.9"/>' for y in (118, 126, 134))
    return plate("b1035", "a friend jumping out of deep water with a splash, a witch's crooked hut, and a game controller", (
        f'<rect x="10" y="114" width="220" height="27" fill="#L" stroke="none"/>{waves}'
        # the splash and the jump
        f'<path d="M52 116 q-8 -16 -16 -10 M60 114 q0 -20 -8 -24 M72 114 q4 -18 14 -16 M80 116 q12 -10 18 -2" stroke="{INK}" stroke-width="1.1"/>'
        f'<circle cx="38" cy="98" r="1.6" fill="{INK}"/><circle cx="96" cy="100" r="1.4" fill="{INK}"/><circle cx="50" cy="86" r="1.2" fill="{INK}"/>'
        + doll(66, 82, 1.0, f"{GREEN}", "up") +
        '<path d="M58 88 q8 4 16 0" stroke-width="0.8" stroke-dasharray="2 2"/>'
        # the witch's hut, crooked, on stilts, smoke curling
        '<path d="M150 112 V100 M186 112 V100 M168 112 V100" stroke-width="1.6"/>'
        '<path d="M146 100 L148 70 L190 66 L190 100 Z" fill="#L"/>'
        f'<path d="M140 72 L170 34 L196 70 Z" fill="{OX}" opacity="0.85"/><path d="M140 72 L170 34 L196 70" stroke-width="1.6"/>'
        '<path d="M150 70 L172 44 M160 70 L178 50 M170 69 L184 54" stroke-width="0.6"/>'
        f'<rect x="162" y="80" width="11" height="12" fill="{OCHRE}"/><path d="M167.5 80 v12 M162 86 h11" stroke-width="0.8"/>'
        '<path d="M182 46 V36 h6 V54" fill="#X"/><path d="M185 32 q-6 -5 0 -9 q6 -4 0 -9 q-5 -4 2 -7" stroke-width="0.9"/>'
        # the controller
        f'<path d="M188 128 q-12 0 -12 -8 q0 -9 12 -9 h26 q12 0 12 9 q0 8 -12 8 z" fill="{PAPER}" stroke-width="1.6"/>'
        f'<path d="M184 119.5 h8 M188 115.5 v8" stroke-width="2.4"/>'
        f'<circle cx="214" cy="116.5" r="2.3" fill="{OX}"/><circle cx="220" cy="120" r="2.3" fill="{OCHRE}"/><circle cx="208" cy="120" r="2.3" fill="{GREEN}"/><circle cx="214" cy="123.5" r="2.3" fill="{INK}"/>'))

def morning_1016():
    rungs = "".join(f'<path d="M104 {y} H140"/>' for y in range(40, 128, 12))
    return plate("c0905", "the friend seen from behind, climbing a ladder, a frog mid-jump, and a heart for a hug", (
        '<path d="M14 128 H226" stroke-width="1"/><path d="M14 128 L40 136 M60 128 L80 138 M150 128 L176 137" stroke-width="0.6"/>'
        # the ladder, and the friend on it, from behind
        '<path d="M100 132 L106 24 M144 132 L138 24" stroke-width="2.2"/>' + rungs +
        doll(122, 94, 1.15, "#H", "climb", back=True) +
        # the frog, mid-jump
        f'<path d="M30 118 q14 -34 34 -22" stroke-dasharray="2 3" stroke-width="0.9"/>'
        f'<ellipse cx="68" cy="96" rx="11" ry="7" fill="{GREEN}"/><circle cx="64" cy="89" r="3" fill="{PAPER}"/><circle cx="72" cy="89" r="3" fill="{PAPER}"/>'
        f'<circle cx="64" cy="89" r="1" fill="{INK}"/><circle cx="72" cy="89" r="1" fill="{INK}"/>'
        f'<path d="M58 100 l-8 8 l-6 -2 M78 100 l8 8 l6 -2" stroke="{GREEN}" stroke-width="1.6"/>'
        # a hug's heart
        f'<path d="M186 84 c-10 -10 -24 2 -12 14 l12 12 l12 -12 c12 -12 -2 -24 -12 -14 z" fill="{OX}"/>'
        '<path d="M172 70 q14 -10 28 0" stroke-width="0.7" stroke-dasharray="1.5 2.5"/>'
        + doll(174, 128, 0.62, f"{OCHRE}", "up") + doll(198, 128, 0.62, f"{GREEN}", "up")))

def afternoon_1015():
    return plate("d1700", "a signpost pointing three ways, a hand dragging the friend, music notes, and a crack for a crash", (
        '<path d="M14 128 H226" stroke-width="1"/>'
        # the signpost, readable boards
        '<path d="M60 130 V30" stroke-width="2.6"/>'
        f'<path d="M62 38 H104 L112 45 L104 52 H62 Z" fill="{PAPER}"/><path d="M68 45 h30" stroke-width="0.9"/>'
        f'<path d="M58 60 H20 L12 67 L20 74 H58 Z" fill="{OCHRE}"/><path d="M24 67 h28" stroke-width="0.9"/>'
        f'<path d="M62 82 H98 L106 89 L98 96 H62 Z" fill="#L"/><path d="M68 89 h24" stroke-width="0.9"/>'
        # a hand dragging the friend, its trail
        '<path d="M120 112 q20 -30 46 -38" stroke-dasharray="2 3" stroke-width="0.9"/>'
        + doll(176, 120, 1.0, f"{OX}", "down") +
        f'<path d="M168 66 q4 -12 10 -6 l2 -10 q4 -3 5 2 l0 -4 q4 -3 5 2 l0 2 q4 -2 5 3 l-2 14 q-2 6 -10 6 h-6 z" fill="{PAPER}" stroke-width="1.2"/>'
        # music, still playing
        f'<g stroke="{INK}"><ellipse cx="206" cy="58" rx="4" ry="3" fill="{INK}"/><path d="M210 58 V38 l8 4"/>'
        f'<ellipse cx="190" cy="44" rx="3.5" ry="2.6" fill="{INK}"/><ellipse cx="200" cy="40" rx="3.5" ry="2.6" fill="{INK}"/><path d="M193.5 44 V28 L203.5 24 V40"/></g>'
        # the crash
        f'<path d="M30 14 L20 30 L28 32 L16 50" stroke="{OX}" stroke-width="1.8"/>'))

def evening_1014():
    sheets = "".join(f'<rect x="{20 + i * 1.6}" y="{118 - i * 7}" width="46" height="9" fill="{PAPER}"/>' for i in range(12))
    steps = "M96 122 " + " ".join(f"h9 v-{6 + i}" for i in range(8))
    return plate("e2120", "a teetering stack of undo pages, a heap chart climbing, a floppy disk saving, and a worker's gear", (
        '<path d="M14 128 H226" stroke-width="1"/>'
        # the undo stack, every page a whole model
        + sheets + '<path d="M22 126 v-6" stroke-width="0.6"/>'
        f'<path d="M24 38 q10 -8 20 0" stroke="{OX}" stroke-width="1.2"/><path d="M44 38 l-3 -5 M44 38 l-5 1" stroke="{OX}" stroke-width="1.2"/>'
        # the heap, growing per edit
        '<path d="M92 34 V124 H174" stroke-width="1.2"/>'
        f'<path d="{steps}" stroke="{OX}" stroke-width="1.8"/><path d="{steps} V124 H96 Z" fill="#H" stroke="none" opacity="0.5"/>'
        # the autosave
        f'<path d="M184 96 h30 l6 6 v26 h-36 z" fill="{PAPER}"/><rect x="190" y="96" width="18" height="10" fill="#L"/>'
        f'<rect x="189" y="112" width="26" height="14" fill="{OCHRE}"/><path d="M193 117 h18 M193 121 h12" stroke-width="0.8"/>'
        # the worker
        f'<g transform="translate(200 52)"><circle r="13" fill="{GREEN}"/>'
        + "".join(f'<rect x="-3" y="-19" width="6" height="7" fill="{GREEN}" transform="rotate({a})"/>' for a in range(0, 360, 45)) +
        f'<circle r="5" fill="{PAPER}"/></g>'))

def deep_links_1014():
    return plate("f1903", "a browser's address bar holding a chain link, and two review comments, one checked, one questioned", (
        # the browser and its address bar
        f'<rect x="20" y="20" width="200" height="66" rx="4" fill="{PAPER}"/><path d="M20 32 H220" stroke-width="1"/>'
        f'<circle cx="28" cy="26" r="2" fill="{OX}" stroke="none"/><circle cx="35" cy="26" r="2" fill="{OCHRE}" stroke="none"/><circle cx="42" cy="26" r="2" fill="{GREEN}" stroke="none"/>'
        '<rect x="30" y="38" width="180" height="13" rx="6.5"/><path d="M62 44.5 h60 M128 44.5 h22 M156 44.5 h40" stroke-width="0.9" stroke-dasharray="4 2"/>'
        f'<g stroke="{OCHRE}" stroke-width="2"><rect x="36" y="40.5" width="12" height="8" rx="4" transform="rotate(-30 42 44.5)"/><rect x="44" y="40.5" width="12" height="8" rx="4" transform="rotate(-30 50 44.5)"/></g>'
        '<rect x="30" y="58" width="56" height="22" fill="#L"/><path d="M96 62 h110 M96 68 h96 M96 74 h104" stroke-width="0.8"/>'
        f'<path d="M150 58 v20" stroke="{OX}" stroke-width="1.4"/>'
        # the review's comments
        f'<path d="M24 100 h86 v26 h-60 l-10 8 v-8 h-16 z" fill="{PAPER}"/><path d="M32 108 h52 M32 115 h40" stroke-width="0.8"/>'
        f'<path d="M90 110 l5 6 l10 -12" stroke="{GREEN}" stroke-width="2.4"/>'
        f'<path d="M126 100 h90 v26 h-16 v8 l-10 -8 h-64 z" fill="{PAPER}"/><path d="M134 108 h46 M134 115 h56" stroke-width="0.8"/>'
        f'<text x="203" y="119" font-family="Georgia, serif" font-size="16" font-weight="bold" text-anchor="middle" fill="{OX}" stroke="none">?</text>'))

def audit_1014():
    bars = "".join(f'<rect x="{22 + i * 13}" y="{118 - 10 - i * 9}" width="10" height="{10 + i * 9}" fill="#H"/>' for i in range(7))
    cells = "".join(f'<rect x="{150 + c * 16}" y="{44 + r * 12}" width="16" height="12"' + (f' fill="{OX}" opacity="0.8"' if (r, c) in {(0, 2), (2, 1), (3, 3), (4, 0)} else "") + '/>' for r in range(5) for c in range(4))
    return plate("g1209", "a heap growing with every slider edit, and a magnifying glass over a table with four cells flagged", (
        '<path d="M14 128 H226" stroke-width="1"/>' + bars +
        f'<path d="M24 50 L104 26" stroke="{OX}" stroke-width="1.6"/><path d="M104 26 l-7 -1 M104 26 l-5 5" stroke="{OX}" stroke-width="1.6"/>'
        # the slider it grew under
        '<path d="M22 136 H118" stroke-width="2"/>'
        f'<circle cx="96" cy="136" r="5" fill="{OCHRE}"/>'
        # the tables, four flagged
        + cells +
        f'<circle cx="196" cy="88" r="20" fill="{PAPER}" fill-opacity="0.35" stroke-width="2.2"/><path d="M210 103 L224 120" stroke-width="5"/>'
        '<path d="M184 80 q6 -6 14 -4" stroke-width="0.8"/>'))

def morning_1014():
    return plate("h0911", "a green check for CI, a laptop on a hand truck, and a small dashboard with its rows", (
        '<path d="M14 128 H226" stroke-width="1"/>'
        # CI, green again
        f'<circle cx="52" cy="62" r="30" fill="{GREEN}" fill-opacity="0.25" stroke="{GREEN}" stroke-width="2.4"/>'
        f'<path d="M36 62 l11 12 l22 -26" stroke="{GREEN}" stroke-width="5"/>'
        # moving the laptop
        '<path d="M100 40 V122 H136" stroke-width="2.4"/><circle cx="108" cy="126" r="6" fill="#X"/>'
        f'<rect x="104" y="98" width="30" height="22" fill="{OCHRE}"/><path d="M104 104 h30 M119 98 v6" stroke-width="0.8"/>'
        '<rect x="104" y="88" width="32" height="10" rx="2" fill="#L"/><path d="M104 93 h32" stroke-width="0.6"/>'
        '<path d="M100 40 l-8 -6" stroke-width="2.4"/>'
        # the dashboard, published each minute
        f'<rect x="152" y="30" width="72" height="88" rx="3" fill="{PAPER}"/><path d="M152 42 H224" stroke-width="1"/>'
        f'<rect x="157" y="34" width="22" height="5" fill="{OX}" stroke="none"/>'
        + "".join(f'<path d="M158 {52 + i * 10} h{30 + (i * 13) % 26} M{200} {52 + i * 10} h14" stroke-width="0.9"/>' for i in range(6)) +
        f'<circle cx="214" cy="36" r="4" stroke-width="0.9"/><path d="M214 33.5 V36 h2" stroke-width="0.8"/>'))

def night_1016():
    stars = "".join(f'<path d="M{x} {y-3} v6 M{x-3} {y} h6" stroke-width="0.9"/>' for x, y in ((60, 22), (88, 36), (140, 18), (214, 30), (30, 46)))
    return plate("i0050", "the laptop asleep under a moon with no browser, while a cloud of GitHub's computers sends down pictures and a ladder", (
        f'<rect x="10" y="10" width="220" height="130" fill="#L" stroke="none" opacity="0.5"/>' + stars +
        # the moon
        f'<path d="M40 16 a14 14 0 1 0 14 22 a11 11 0 1 1 -14 -22 z" fill="{OCHRE}"/>'
        # the laptop, shut, asleep, no browser
        '<path d="M14 128 H226" stroke-width="1"/>'
        f'<path d="M22 126 H88 L94 120 H28 Z" fill="{PAPER}"/><path d="M28 120 L34 112 H88 L94 120" fill="#H"/>'
        '<text x="66" y="104" font-family="Georgia, serif" font-size="10" font-style="italic" fill="#2b2118" stroke="none">z</text>'
        '<text x="74" y="94" font-family="Georgia, serif" font-size="13" font-style="italic" fill="#2b2118" stroke="none">z</text>'
        f'<g transform="translate(36 78)"><rect width="24" height="18" rx="2" fill="{PAPER}"/><path d="M0 5 h24" stroke-width="1"/>'
        f'<circle cx="12" cy="11" r="10" stroke="{OX}" stroke-width="2"/><path d="M5 18 L19 4" stroke="{OX}" stroke-width="2"/></g>'
        # GitHub's computers, a cloud at work
        f'<path d="M128 58 q-14 0 -14 -12 q0 -12 14 -12 q4 -12 20 -12 q14 0 18 10 q16 -2 18 12 q12 2 10 14 z" fill="{PAPER}" stroke-width="1.6"/>'
        f'<g transform="translate(150 44)"><circle r="7" fill="{GREEN}"/>' + "".join(f'<rect x="-2" y="-10" width="4" height="5" fill="{GREEN}" transform="rotate({a})"/>' for a in range(0, 360, 60)) + f'<circle r="2.5" fill="{PAPER}"/></g>'
        # pictures falling from it, and a ladder with the friend climbing
        f'<g stroke-width="1.1"><rect x="124" y="70" width="16" height="12" fill="{PAPER}" transform="rotate(-10 132 76)"/><path d="M126 80 l4 -5 l4 4 l3 -3 l3 4" transform="rotate(-10 132 76)"/>'
        f'<rect x="150" y="86" width="16" height="12" fill="{PAPER}" transform="rotate(8 158 92)"/><circle cx="155" cy="90" r="2" fill="{OCHRE}" stroke="none"/>'
        f'<rect x="132" y="104" width="16" height="12" fill="{PAPER}" transform="rotate(-4 140 110)"/><path d="M134 113 h12" /></g>'
        '<path d="M190 128 L196 64 M214 128 L208 64" stroke-width="1.8"/>' + "".join(f'<path d="M{191 + i * 0.4} {120 - i * 9} H{213 - i * 0.4}"/>' for i in range(7))
        + doll(203, 106, 0.55, f"{OX}", "climb", back=True)))

ART = {
    "work-notes/2026/10/17/2026-10-17T0050-0600.html": night_1016,
    "work-notes/2026/10/16/2026-10-16T1810-0600.html": evening_1016,
    "work-notes/2026/10/16/2026-10-16T1035-0600.html": late_morning_1016,
    "work-notes/2026/10/16/2026-10-16T0905-0600.html": morning_1016,
    "work-notes/2026/10/15/2026-10-15T1700-0600.html": afternoon_1015,
    "work-notes/2026/10/14/2026-10-14T2120-0600.html": evening_1014,
    "work-notes/2026/10/14/2026-10-14T1903-0600.html": deep_links_1014,
    "work-notes/2026/10/14/2026-10-14T1209-0600.html": audit_1014,
    "work-notes/2026/10/14/2026-10-14T0911-0600.html": morning_1014,
}

if __name__ == "__main__":
    entries = json.load(open(GALLERY, encoding="utf-8"))
    for e in entries:
        if e["path"] in ART:
            e["art"] = ART[e["path"]]()
    json.dump(entries, open(GALLERY, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{GALLERY}: {sum(1 for e in entries if e['path'] in ART)} pictures drawn, of {len(entries)} notes")
