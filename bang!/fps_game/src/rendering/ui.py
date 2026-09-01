"""
ui.py - Premium HUD matching the reference screenshot.
All drawing is done in screen-space (-1..1 NDC) using GL_QUADS / GL_LINES.
"""
from OpenGL.GL import *
import time
import math


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _push_2d():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix(); glLoadIdentity()
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix(); glLoadIdentity()
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)


def _pop_2d():
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()


def _quad(x, y, w, h, r, g, b, a=1.0):
    glColor4f(r, g, b, a)
    glBegin(GL_QUADS)
    glVertex2f(x,     y)
    glVertex2f(x + w, y)
    glVertex2f(x + w, y + h)
    glVertex2f(x,     y + h)
    glEnd()


def _quad_border(x, y, w, h, r, g, b, lw=1.5):
    glColor3f(r, g, b)
    glLineWidth(lw)
    glBegin(GL_LINE_LOOP)
    glVertex2f(x,     y)
    glVertex2f(x + w, y)
    glVertex2f(x + w, y + h)
    glVertex2f(x,     y + h)
    glEnd()
    glLineWidth(1.0)


def _line(x1, y1, x2, y2, r, g, b, lw=1.5):
    glColor3f(r, g, b)
    glLineWidth(lw)
    glBegin(GL_LINES)
    glVertex2f(x1, y1); glVertex2f(x2, y2)
    glEnd()
    glLineWidth(1.0)


# ---------------------------------------------------------------------------
# Tiny bitmap-style font (line segments, ~0.012 wide, ~0.02 tall per glyph)
# ---------------------------------------------------------------------------

def _char(ch, x, y, s):
    """Render character ch at (x,y) with size s."""
    glBegin(GL_LINES)
    w, h = s, s * 1.6
    if ch == 'A':
        glVertex2f(x,      y);     glVertex2f(x+w/2,  y+h)
        glVertex2f(x+w/2,  y+h);   glVertex2f(x+w,    y)
        glVertex2f(x+w*.25,y+h*.5);glVertex2f(x+w*.75,y+h*.5)
    elif ch == 'B':
        glVertex2f(x,y);glVertex2f(x,y+h)
        glVertex2f(x,y+h);glVertex2f(x+w*.8,y+h)
        glVertex2f(x+w*.8,y+h);glVertex2f(x+w,y+h*.75)
        glVertex2f(x+w,y+h*.75);glVertex2f(x+w*.8,y+h*.5)
        glVertex2f(x+w*.8,y+h*.5);glVertex2f(x,y+h*.5)
        glVertex2f(x+w*.8,y+h*.5);glVertex2f(x+w,y+h*.25)
        glVertex2f(x+w,y+h*.25);glVertex2f(x+w*.8,y)
        glVertex2f(x+w*.8,y);glVertex2f(x,y)
    elif ch == 'C':
        glVertex2f(x+w,y+h);glVertex2f(x,y+h)
        glVertex2f(x,y+h);glVertex2f(x,y)
        glVertex2f(x,y);glVertex2f(x+w,y)
    elif ch == 'D':
        glVertex2f(x,y);glVertex2f(x,y+h)
        glVertex2f(x,y+h);glVertex2f(x+w*.7,y+h)
        glVertex2f(x+w*.7,y+h);glVertex2f(x+w,y+h*.7)
        glVertex2f(x+w,y+h*.7);glVertex2f(x+w,y+h*.3)
        glVertex2f(x+w,y+h*.3);glVertex2f(x+w*.7,y)
        glVertex2f(x+w*.7,y);glVertex2f(x,y)
    elif ch == 'E':
        glVertex2f(x,y);glVertex2f(x,y+h)
        glVertex2f(x,y+h);glVertex2f(x+w,y+h)
        glVertex2f(x,y+h*.5);glVertex2f(x+w*.8,y+h*.5)
        glVertex2f(x,y);glVertex2f(x+w,y)
    elif ch == 'G':
        glVertex2f(x+w,y+h);glVertex2f(x,y+h)
        glVertex2f(x,y+h);glVertex2f(x,y)
        glVertex2f(x,y);glVertex2f(x+w,y)
        glVertex2f(x+w,y);glVertex2f(x+w,y+h*.5)
        glVertex2f(x+w,y+h*.5);glVertex2f(x+w*.5,y+h*.5)
    elif ch == 'H':
        glVertex2f(x,y);glVertex2f(x,y+h)
        glVertex2f(x+w,y);glVertex2f(x+w,y+h)
        glVertex2f(x,y+h*.5);glVertex2f(x+w,y+h*.5)
    elif ch == 'I':
        glVertex2f(x,y);glVertex2f(x+w,y)
        glVertex2f(x+w*.5,y);glVertex2f(x+w*.5,y+h)
        glVertex2f(x,y+h);glVertex2f(x+w,y+h)
    elif ch == 'L':
        glVertex2f(x,y+h);glVertex2f(x,y)
        glVertex2f(x,y);glVertex2f(x+w,y)
    elif ch == 'M':
        glVertex2f(x,y);glVertex2f(x,y+h)
        glVertex2f(x,y+h);glVertex2f(x+w*.5,y+h*.5)
        glVertex2f(x+w*.5,y+h*.5);glVertex2f(x+w,y+h)
        glVertex2f(x+w,y+h);glVertex2f(x+w,y)
    elif ch == 'N':
        glVertex2f(x,y);glVertex2f(x,y+h)
        glVertex2f(x,y+h);glVertex2f(x+w,y)
        glVertex2f(x+w,y);glVertex2f(x+w,y+h)
    elif ch == 'O':
        glVertex2f(x,y);glVertex2f(x,y+h)
        glVertex2f(x,y+h);glVertex2f(x+w,y+h)
        glVertex2f(x+w,y+h);glVertex2f(x+w,y)
        glVertex2f(x+w,y);glVertex2f(x,y)
    elif ch == 'P':
        glVertex2f(x,y);glVertex2f(x,y+h)
        glVertex2f(x,y+h);glVertex2f(x+w,y+h)
        glVertex2f(x+w,y+h);glVertex2f(x+w,y+h*.5)
        glVertex2f(x+w,y+h*.5);glVertex2f(x,y+h*.5)
    elif ch == 'R':
        glVertex2f(x,y);glVertex2f(x,y+h)
        glVertex2f(x,y+h);glVertex2f(x+w,y+h)
        glVertex2f(x+w,y+h);glVertex2f(x+w,y+h*.5)
        glVertex2f(x+w,y+h*.5);glVertex2f(x,y+h*.5)
        glVertex2f(x,y+h*.5);glVertex2f(x+w,y)
    elif ch == 'S':
        glVertex2f(x+w,y+h);glVertex2f(x,y+h)
        glVertex2f(x,y+h);glVertex2f(x,y+h*.5)
        glVertex2f(x,y+h*.5);glVertex2f(x+w,y+h*.5)
        glVertex2f(x+w,y+h*.5);glVertex2f(x+w,y)
        glVertex2f(x+w,y);glVertex2f(x,y)
    elif ch == 'T':
        glVertex2f(x,y+h);glVertex2f(x+w,y+h)
        glVertex2f(x+w*.5,y+h);glVertex2f(x+w*.5,y)
    elif ch == 'U':
        glVertex2f(x,y+h);glVertex2f(x,y)
        glVertex2f(x,y);glVertex2f(x+w,y)
        glVertex2f(x+w,y);glVertex2f(x+w,y+h)
    elif ch == 'W':
        glVertex2f(x,y+h);glVertex2f(x+w*.25,y)
        glVertex2f(x+w*.25,y);glVertex2f(x+w*.5,y+h*.4)
        glVertex2f(x+w*.5,y+h*.4);glVertex2f(x+w*.75,y)
        glVertex2f(x+w*.75,y);glVertex2f(x+w,y+h)
    elif ch == 'Y':
        glVertex2f(x,y+h);glVertex2f(x+w*.5,y+h*.5)
        glVertex2f(x+w,y+h);glVertex2f(x+w*.5,y+h*.5)
        glVertex2f(x+w*.5,y+h*.5);glVertex2f(x+w*.5,y)
    elif ch == '0':
        glVertex2f(x,y);glVertex2f(x,y+h)
        glVertex2f(x,y+h);glVertex2f(x+w,y+h)
        glVertex2f(x+w,y+h);glVertex2f(x+w,y)
        glVertex2f(x+w,y);glVertex2f(x,y)
    elif ch == '1':
        glVertex2f(x+w*.5,y);glVertex2f(x+w*.5,y+h)
    elif ch == '2':
        glVertex2f(x,y+h);glVertex2f(x+w,y+h)
        glVertex2f(x+w,y+h);glVertex2f(x+w,y+h*.5)
        glVertex2f(x+w,y+h*.5);glVertex2f(x,y+h*.5)
        glVertex2f(x,y+h*.5);glVertex2f(x,y)
        glVertex2f(x,y);glVertex2f(x+w,y)
    elif ch == '3':
        glVertex2f(x,y+h);glVertex2f(x+w,y+h)
        glVertex2f(x+w,y+h);glVertex2f(x+w,y)
        glVertex2f(x+w,y);glVertex2f(x,y)
        glVertex2f(x,y+h*.5);glVertex2f(x+w,y+h*.5)
    elif ch == '4':
        glVertex2f(x,y+h);glVertex2f(x,y+h*.5)
        glVertex2f(x,y+h*.5);glVertex2f(x+w,y+h*.5)
        glVertex2f(x+w,y+h);glVertex2f(x+w,y)
    elif ch == '5':
        glVertex2f(x+w,y+h);glVertex2f(x,y+h)
        glVertex2f(x,y+h);glVertex2f(x,y+h*.5)
        glVertex2f(x,y+h*.5);glVertex2f(x+w,y+h*.5)
        glVertex2f(x+w,y+h*.5);glVertex2f(x+w,y)
        glVertex2f(x+w,y);glVertex2f(x,y)
    elif ch == '6':
        glVertex2f(x+w,y+h);glVertex2f(x,y+h)
        glVertex2f(x,y+h);glVertex2f(x,y)
        glVertex2f(x,y);glVertex2f(x+w,y)
        glVertex2f(x+w,y);glVertex2f(x+w,y+h*.5)
        glVertex2f(x+w,y+h*.5);glVertex2f(x,y+h*.5)
    elif ch == '7':
        glVertex2f(x,y+h);glVertex2f(x+w,y+h)
        glVertex2f(x+w,y+h);glVertex2f(x+w,y)
    elif ch == '8':
        glVertex2f(x,y);glVertex2f(x,y+h)
        glVertex2f(x,y+h);glVertex2f(x+w,y+h)
        glVertex2f(x+w,y+h);glVertex2f(x+w,y)
        glVertex2f(x+w,y);glVertex2f(x,y)
        glVertex2f(x,y+h*.5);glVertex2f(x+w,y+h*.5)
    elif ch == '9':
        glVertex2f(x,y+h*.5);glVertex2f(x,y+h)
        glVertex2f(x,y+h);glVertex2f(x+w,y+h)
        glVertex2f(x+w,y+h);glVertex2f(x+w,y)
    elif ch == '/':
        glVertex2f(x+w,y+h);glVertex2f(x,y)
    elif ch == '!':
        glVertex2f(x+w*.5,y+h*.3);glVertex2f(x+w*.5,y+h)
        glVertex2f(x+w*.5,y);glVertex2f(x+w*.5,y+h*.15)
    glEnd()


def _text(string, x, y, s, r=1, g=1, b=1, spacing=1.8):
    glColor3f(r, g, b)
    cx = x
    for ch in string.upper():
        if ch == ' ':
            cx += s * spacing * 0.6
            continue
        _char(ch, cx, y, s)
        cx += s * spacing


def _text_width(string, s, spacing=1.8):
    w = 0
    for ch in string:
        if ch == ' ':
            w += s * spacing * 0.6
        else:
            w += s * spacing
    return w


# ---------------------------------------------------------------------------
# Panel drawing helpers
# ---------------------------------------------------------------------------

def _panel(x, y, w, h, dark=(0.05,0.10,0.20), border=(0.20,0.55,0.85)):
    """Dark navy panel with bright blue border."""
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(*dark, 0.82)
    glBegin(GL_QUADS)
    glVertex2f(x, y); glVertex2f(x+w, y)
    glVertex2f(x+w, y+h); glVertex2f(x, y+h)
    glEnd()
    glDisable(GL_BLEND)
    _quad_border(x, y, w, h, *border, lw=2.0)


def _corner_bracket(x, y, w, h, size=0.012, r=0.3, g=0.8, b=1.0, lw=2.0):
    """Draw four corner L-brackets like a targeting reticle."""
    glColor3f(r, g, b); glLineWidth(lw)
    glBegin(GL_LINES)
    # BL
    glVertex2f(x, y+size);      glVertex2f(x, y)
    glVertex2f(x, y);           glVertex2f(x+size, y)
    # BR
    glVertex2f(x+w-size, y);    glVertex2f(x+w, y)
    glVertex2f(x+w, y);         glVertex2f(x+w, y+size)
    # TL
    glVertex2f(x, y+h-size);    glVertex2f(x, y+h)
    glVertex2f(x, y+h);         glVertex2f(x+size, y+h)
    # TR
    glVertex2f(x+w-size, y+h);  glVertex2f(x+w, y+h)
    glVertex2f(x+w, y+h);       glVertex2f(x+w, y+h-size)
    glEnd()
    glLineWidth(1.0)


def _heart(cx, cy, r):
    """Draw a simple heart shape using lines."""
    glLineWidth(1.5)
    glBegin(GL_LINE_LOOP)
    steps = 30
    for i in range(steps):
        t = math.pi * 2 * i / steps
        x = r * 16 * math.sin(t)**3
        y = r * (13*math.cos(t) - 5*math.cos(2*t) - 2*math.cos(3*t) - math.cos(4*t))
        # scale to NDC
        glVertex2f(cx + x * 0.0016, cy + y * 0.0016)
    glEnd()
    glLineWidth(1.0)


def _crosshair_icon(cx, cy, s, r=0.9, g=0.9, b=0.9):
    glColor3f(r, g, b); glLineWidth(1.5)
    glBegin(GL_LINES)
    glVertex2f(cx-s, cy); glVertex2f(cx+s, cy)
    glVertex2f(cx, cy-s); glVertex2f(cx, cy+s)
    glEnd()
    # circle approximation (octagon)
    glBegin(GL_LINE_LOOP)
    for i in range(8):
        a = math.pi*2*i/8
        glVertex2f(cx + s*0.7*math.cos(a), cy + s*0.7*math.sin(a))
    glEnd()
    glLineWidth(1.0)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def draw_crosshair():
    """Draw a clean tactical crosshair in the center of the screen."""
    _push_2d()
    s = 0.022
    cx, cy = 0.0, 0.0
    gap = 0.007
    glColor4f(0.3, 1.0, 0.3, 0.9)
    glLineWidth(2.0)
    glBegin(GL_LINES)
    glVertex2f(cx - s, cy); glVertex2f(cx - gap, cy)
    glVertex2f(cx + gap, cy); glVertex2f(cx + s, cy)
    glVertex2f(cx, cy - s); glVertex2f(cx, cy - gap)
    glVertex2f(cx, cy + gap); glVertex2f(cx, cy + s)
    glEnd()
    glLineWidth(1.0)
    # Corner brackets
    _corner_bracket(-gap*2, -gap*2, gap*4, gap*4, size=0.006,
                    r=0.3, g=1.0, b=0.3, lw=1.5)
    _pop_2d()


def draw_health_bar(health_percentage):
    """Top-left HP panel with heart icon, label and numeric value."""
    _push_2d()

    px, py, pw, ph = -0.98, 0.80, 0.30, 0.17
    _panel(px, py, pw, ph)

    # Heart icon
    glColor3f(0.9, 0.2, 0.2)
    _heart(px + 0.045, py + ph*0.5, 10)

    # "HP" label
    _text("HP", px+0.075, py+ph-0.045, 0.018, r=1,g=1,b=1)

    # Bar background
    bx = px + 0.075; by = py + 0.05; bw = pw - 0.095; bh = 0.030
    _quad(bx, by, bw, bh, 0.15, 0.05, 0.05)

    # Bar fill
    if health_percentage > 0.6:
        fc = (0.15, 0.85, 0.25)
    elif health_percentage > 0.3:
        fc = (0.95, 0.80, 0.10)
    else:
        fc = (0.90, 0.15, 0.15)
    _quad(bx, by, bw * health_percentage, bh, *fc)
    _quad_border(bx, by, bw, bh, 0.3, 0.8, 1.0, lw=1.5)

    # Numeric value  e.g. "100 / 100"
    hp_val = int(health_percentage * 100)
    hp_str = f"{hp_val}/100"
    tw = _text_width(hp_str, 0.013)
    tx = bx + (bw - tw) / 2
    _text(hp_str, tx, by + 0.004, 0.013, r=1,g=1,b=1)

    _pop_2d()


def draw_score(score):
    """Top-right score panel."""
    _push_2d()

    pw, ph = 0.26, 0.17
    px = 0.98 - pw; py = 0.80
    _panel(px, py, pw, ph)

    # "SCORE" label
    _text("SCORE", px+0.015, py+ph-0.045, 0.016, r=0.3, g=0.85, b=1.0)

    # Crosshair icon at right of label
    _crosshair_icon(px+pw-0.032, py+ph-0.030, 0.016)

    # Score digits (zero-padded to 4)
    score_str = f"{score:04d}"
    _text(score_str, px+0.018, py+0.030, 0.030, r=1,g=1,b=1)

    _pop_2d()


def draw_title():
    """Center-top 'TARGET PRACTICE' title banner."""
    _push_2d()

    title = "TARGET PRACTICE"
    s = 0.020
    tw = _text_width(title, s)
    pw = tw + 0.08; ph = 0.10
    px = -pw/2; py = 0.87

    _panel(px, py, pw, ph)

    # Decorative wing lines
    wing = 0.10
    _line(px - wing, py+ph*0.5, px, py+ph*0.5,   0.3,0.7,1.0, lw=2)
    _line(px+pw, py+ph*0.5, px+pw+wing, py+ph*0.5, 0.3,0.7,1.0, lw=2)

    # Title text
    tx = -tw/2
    _text(title, tx, py+ph*0.55, s, r=1,g=1,b=1)

    # Crosshair icon under title
    _crosshair_icon(0.0, py+ph*0.22, 0.010)

    _pop_2d()


def draw_controls_panel():
    """Bottom-left controls cheatsheet."""
    _push_2d()

    px, py, pw, ph = -0.98, -0.98, 0.27, 0.33
    _panel(px, py, pw, ph)

    # Header
    _text("CONTROLS", px+0.012, py+ph-0.042, 0.015, r=0.3,g=0.85,b=1.0)
    _line(px+0.010, py+ph-0.050, px+pw-0.010, py+ph-0.050, 0.2,0.5,0.8, lw=1.5)

    entries = [
        ("ArUco Marker", "Aim"),
        ("Recoil Motion", "Shoot"),
        ("Left Fist", "Reload"),
        ("ESC", "Exit"),
    ]
    ey = py + ph - 0.082
    row_h = 0.055
    for key, action in entries:
        # key box
        kw = 0.095
        _quad_border(px+0.010, ey, kw, 0.030, 0.3,0.7,1.0, lw=1.5)
        _text(key, px+0.015, ey+0.006, 0.010, r=0.9,g=0.9,b=0.9)
        _text(action, px+0.012+kw+0.012, ey+0.006, 0.013, r=1,g=1,b=1)
        ey -= row_h

    _pop_2d()


def draw_bottom_banner():
    """Bottom-center message banner."""
    _push_2d()

    msg = "DESTROY TARGETS TO SCORE POINTS!"
    s = 0.016
    tw = _text_width(msg, s)
    pw = tw + 0.08; ph = 0.058
    px = -pw/2; py = -0.98

    _panel(px, py, pw, ph,
           dark=(0.05,0.12,0.28),
           border=(0.20,0.55,0.90))

    # Small crosshair icon before text
    _crosshair_icon(px+0.030, py+ph/2, 0.012, r=0.3,g=0.85,b=1.0)
    _text(msg, px+0.052, py+ph*0.22, s, r=1,g=1,b=1)

    _pop_2d()


def draw_ammo_display(weapon_system):
    """Bottom-right ammo panel with bullet icons."""
    _push_2d()

    current_ammo, max_ammo = weapon_system.get_ammo_info()
    bw = 0.022; bh = 0.044; gap = 0.008
    row_w = max_ammo * (bw + gap) - gap
    pw = row_w + 0.04; ph = 0.11
    px = 0.98 - pw; py = -0.98

    _panel(px, py, pw, ph)

    # "AMMO" label
    _text("AMMO", px + (pw - _text_width("AMMO",0.014))/2,
          py + ph - 0.035, 0.014, r=0.3, g=0.85, b=1.0)

    # Bullet icons
    bstart_x = px + 0.020
    bstart_y = py + 0.015

    for i in range(max_ammo):
        bx = bstart_x + i * (bw + gap)
        if weapon_system.is_reloading:
            flash = int(time.time() * 8) % 2
            fc = (1.0,0.9,0.2) if flash else (0.3,0.25,0.05)
        elif i < current_ammo:
            fc = (0.95, 0.82, 0.20)   # gold
        else:
            fc = (0.20, 0.20, 0.25)   # grey

        # Casing body
        _quad(bx, bstart_y, bw, bh, *fc)
        # Tip
        tip_c = (min(fc[0]+0.1,1), min(fc[1]+0.1,1), fc[2])
        _quad(bx+bw*0.15, bstart_y+bh, bw*0.7, bh*0.3, *tip_c)
        # Border
        _quad_border(bx, bstart_y, bw, bh, 0.8,0.8,0.8, lw=1.0)

    # Reload progress bar
    if weapon_system.is_reloading:
        progress = weapon_system.get_reload_progress()
        ry = bstart_y + bh + bh*0.3 + 0.006
        rw = row_w
        _quad(bstart_x, ry, rw, 0.012, 0.1,0.1,0.1)
        _quad(bstart_x, ry, rw*progress, 0.012, 0.2,0.9,0.3)
        _quad_border(bstart_x, ry, rw, 0.012, 1,1,1, lw=1.0)

    _pop_2d()