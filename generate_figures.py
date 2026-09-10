#!/usr/bin/env python3
"""
generate_figures.py — Generates publication-grade, high-resolution vector diagrams
for the MCP Apps Trust Boundaries research paper.
Uses Cairo for clean subpixel anti-aliased 2D rendering.
"""

import os
import math
import cairo

OUT_DIR = "/home/mobta/university/malik/figures"
os.makedirs(OUT_DIR, exist_ok=True)

# ─── Color Palette (IEEE Computer Society / Systems Security Style) ───────────
C_BG          = (0.975, 0.982, 0.992)  # #F8FAFC soft cool background
C_WHITE       = (1.0, 1.0, 1.0)
C_NAVY_DARK   = (0.059, 0.173, 0.349)  # #0F2C59 primary deep navy
C_NAVY_MID    = (0.118, 0.286, 0.533)  # #1E4988 mid navy
C_BLUE_CARD   = (0.933, 0.957, 0.996)  # #EEF4FE soft blue fill
C_BLUE_BORDER = (0.584, 0.749, 0.965)  # #95BFFA
C_BORDER_GRAY = (0.800, 0.835, 0.882)  # #CCD5E1
C_TEXT_DARK   = (0.059, 0.090, 0.165)  # #0F172A
C_TEXT_MID    = (0.278, 0.333, 0.412)  # #475569
C_TEXT_LIGHT  = (0.392, 0.455, 0.545)  # #64748B

# Semantics
C_ALLOW_BG    = (0.925, 0.984, 0.949)  # emerald light
C_ALLOW_EDGE  = (0.063, 0.612, 0.345)  # emerald green
C_DENY_BG     = (0.996, 0.925, 0.925)  # ruby light
C_DENY_EDGE   = (0.863, 0.149, 0.149)  # ruby red
C_WARN_BG     = (0.996, 0.965, 0.898)  # amber light
C_WARN_EDGE   = (0.851, 0.467, 0.024)  # amber dark
C_WARN_TEXT   = (0.573, 0.282, 0.000)
C_AUDIT_BG    = (0.953, 0.933, 0.992)  # purple light
C_AUDIT_EDGE  = (0.486, 0.227, 0.929)  # purple mid

# ─── Cairo Helper Functions ──────────────────────────────────────────────────

def rounded_rect(cr, x, y, w, h, r):
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi/2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi/2)
    cr.arc(x + r, y + h - r, r, math.pi/2, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 3*math.pi/2)
    cr.close_path()

def draw_card(cr, x, y, w, h, r=8, bg=C_WHITE, border=C_BORDER_GRAY, border_w=1.5,
              header_bg=None, header_h=30, header_text=None, header_text_color=C_WHITE,
              header_font_size=13):
    # Shadow
    cr.save()
    rounded_rect(cr, x + 2, y + 2, w, h, r)
    cr.set_source_rgba(0, 0, 0, 0.04)
    cr.fill()
    cr.restore()

    # Body
    rounded_rect(cr, x, y, w, h, r)
    cr.set_source_rgb(*bg)
    cr.fill_preserve()
    cr.set_source_rgb(*border)
    cr.set_line_width(border_w)
    cr.stroke()

    # Header banner if provided
    if header_bg:
        cr.save()
        rounded_rect(cr, x, y, w, h, r)
        cr.clip()
        cr.rectangle(x, y, w, header_h)
        cr.set_source_rgb(*header_bg)
        cr.fill()
        if header_text:
            cr.set_source_rgb(*header_text_color)
            cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(header_font_size)
            cr.move_to(x + 12, y + header_h - 9)
            cr.show_text(header_text)
        cr.restore()

def draw_badge(cr, x, y, text, bg, text_color=C_WHITE, font_size=11, px=10, py=4):
    cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(font_size)
    ext = cr.text_extents(text)
    w = ext.width + px * 2
    h = ext.height + py * 2 + 2
    rounded_rect(cr, x, y, w, h, h / 2)
    cr.set_source_rgb(*bg)
    cr.fill()
    cr.set_source_rgb(*text_color)
    cr.move_to(x + px, y + h - py - 2)
    cr.show_text(text)
    return w, h

def draw_arrow(cr, x1, y1, x2, y2, color=(0.2, 0.3, 0.45), line_w=2.0, arrow_sz=9, dashed=False):
    cr.save()
    cr.set_source_rgb(*color)
    cr.set_line_width(line_w)
    if dashed:
        cr.set_dash([6.0, 4.0])
    cr.move_to(x1, y1)
    cr.line_to(x2, y2)
    cr.stroke()

    angle = math.atan2(y2 - y1, x2 - x1)
    cr.set_dash([])
    cr.new_path()
    cr.move_to(x2, y2)
    cr.line_to(x2 - arrow_sz * math.cos(angle - math.pi / 6), y2 - arrow_sz * math.sin(angle - math.pi / 6))
    cr.line_to(x2 - arrow_sz * math.cos(angle + math.pi / 6), y2 - arrow_sz * math.sin(angle + math.pi / 6))
    cr.close_path()
    cr.fill()
    cr.restore()

def draw_ortho_arrow(cr, points, color=(0.2, 0.3, 0.45), line_w=2.0, arrow_sz=9, dashed=False):
    cr.save()
    cr.set_source_rgb(*color)
    cr.set_line_width(line_w)
    if dashed:
        cr.set_dash([6.0, 4.0])
    cr.move_to(points[0][0], points[0][1])
    for pt in points[1:]:
        cr.line_to(pt[0], pt[1])
    cr.stroke()

    x1, y1 = points[-2]
    x2, y2 = points[-1]
    angle = math.atan2(y2 - y1, x2 - x1)
    cr.set_dash([])
    cr.new_path()
    cr.move_to(x2, y2)
    cr.line_to(x2 - arrow_sz * math.cos(angle - math.pi / 6), y2 - arrow_sz * math.sin(angle - math.pi / 6))
    cr.line_to(x2 - arrow_sz * math.cos(angle + math.pi / 6), y2 - arrow_sz * math.sin(angle + math.pi / 6))
    cr.close_path()
    cr.fill()
    cr.restore()

# ─── FIGURE 1: Conceptual Trust Boundary Overview ────────────────────────────

def build_figure_1(filename):
    w, h = 1800, 1100
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    cr = cairo.Context(surf)

    cr.set_source_rgb(*C_BG)
    cr.paint()

    draw_card(cr, 40, 40, w - 80, h - 80, r=14, bg=(0.99, 0.995, 1.0),
              border=C_NAVY_DARK, border_w=2.5,
              header_bg=C_NAVY_DARK, header_h=54,
              header_text="HOST CLIENT PLATFORM — CONCEPTUAL TRUST BOUNDARIES & CAPABILITY CHANNELS",
              header_font_size=17)

    top_y = 120
    draw_card(cr, 80, top_y, 480, 110, r=10, bg=C_BLUE_CARD, border=C_BLUE_BORDER, border_w=1.5,
              header_bg=C_NAVY_MID, header_h=32,
              header_text="1. Conversational Chat History",
              header_font_size=12.5)
    cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cr.set_font_size(11)
    cr.set_source_rgb(*C_TEXT_MID)
    cr.move_to(100, top_y + 56)
    cr.show_text("• Trusted Host DOM & React Rendering Pipeline")
    cr.move_to(100, top_y + 76)
    cr.show_text("• Target Destination of ui/message Invocations")
    cr.move_to(100, top_y + 96)
    cr.show_text("• Protected by Payload Size Bound & Explicit Consent")

    draw_card(cr, 660, top_y, 480, 110, r=10, bg=C_BLUE_CARD, border=C_BLUE_BORDER, border_w=1.5,
              header_bg=C_NAVY_MID, header_h=32,
              header_text="2. LLM Model Context Window",
              header_font_size=12.5)
    cr.move_to(680, top_y + 56)
    cr.show_text("• Active Working Memory of the Conversational Agent")
    cr.move_to(680, top_y + 76)
    cr.show_text("• Target Destination of ui/update-model-context")
    cr.move_to(680, top_y + 96)
    cr.show_text("• Defends Against Context Poisoning & Prompt Hijacking")

    draw_card(cr, 1240, top_y, 480, 110, r=10, bg=C_BLUE_CARD, border=C_BLUE_BORDER, border_w=1.5,
              header_bg=C_NAVY_MID, header_h=32,
              header_text="3. System External Web Browser",
              header_font_size=12.5)
    cr.move_to(1260, top_y + 56)
    cr.show_text("• Host Operating System Default Browser Context")
    cr.move_to(1260, top_y + 76)
    cr.show_text("• Target Destination of ui/open-link Invocations")
    cr.move_to(1260, top_y + 96)
    cr.show_text("• Protected by Protocol Scheme Gate (http/https Only)")

    b_y = 270
    draw_card(cr, 80, b_y, w - 160, 90, r=10, bg=(0.95, 0.98, 0.95), border=C_ALLOW_EDGE, border_w=2.0)
    cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(15)
    cr.set_source_rgb(*C_ALLOW_EDGE)
    cr.move_to(110, b_y + 32)
    cr.show_text("======================= HOST-SIDE POLICY ENFORCEMENT BOUNDARY =======================")

    cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cr.set_font_size(12)
    cr.set_source_rgb(*C_TEXT_DARK)
    cr.move_to(110, b_y + 62)
    cr.show_text("Enforces: (1) Link Scheme Validation (http/https)  |  (2) Payload Bound (4 KB Cap)  |  (3) Explicit User Consent  |  (4) Non-Blocking Audit")

    bridge_y = 390
    draw_card(cr, 300, bridge_y, w - 600, 56, r=8, bg=C_WHITE, border=C_NAVY_MID, border_w=1.5)
    cr.select_font_face("Liberation Mono", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(13)
    cr.set_source_rgb(*C_NAVY_DARK)
    cr.move_to(330, bridge_y + 34)
    cr.show_text("AppBridge RPC Transport: JSON-RPC 2.0 via window.postMessage (Bidirectional Channel)")

    frame_y = 480
    draw_card(cr, 80, frame_y, w - 160, 480, r=12, bg=(0.98, 0.985, 0.995), border=(0.5, 0.6, 0.75), border_w=2.0,
              header_bg=(0.3, 0.4, 0.55), header_h=38,
              header_text="HTML5 Sandboxed Iframe Container (Sandbox Proxy: http://localhost:8091)",
              header_font_size=13.5)

    badge_comp_y = frame_y + 50
    draw_card(cr, 110, badge_comp_y, w - 220, 46, r=6, bg=C_WARN_BG, border=C_WARN_EDGE, border_w=1.5)
    draw_badge(cr, 125, badge_comp_y + 8, "SourceBadge", C_WARN_EDGE, font_size=11, px=8, py=3)
    cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(12)
    cr.set_source_rgb(*C_WARN_TEXT)
    cr.move_to(250, badge_comp_y + 28)
    cr.show_text("(!) External Server UI. Rendered by an untrusted MCP server. Host policy active.")

    app_y = badge_comp_y + 65
    draw_card(cr, 110, app_y, w - 220, 340, r=10, bg=C_WHITE, border=(0.7, 0.75, 0.85), border_w=1.5,
              header_bg=(0.2, 0.25, 0.35), header_h=34,
              header_text="Untrusted MCP App UI (Served by MCP Server: http://localhost:3001)",
              header_font_size=13)

    attacks = [
        ("Attack 1: Direct Network Fetch", "App tries fetch('http://localhost:9999/exfil')", "BLOCKED BY CSP", C_ALLOW_EDGE,
         "Mandatory Content Security Policy connectDomains: [] restricts egress"),
        ("Attack 2: Hidden Model Tool Call", "App invokes tools/call { name: 'read-secret' }", "BLOCKED BY SPEC", C_ALLOW_EDGE,
         "gateToolVisibility rejects tools lacking 'app' visibility tag (Fail-Closed)"),
        ("Attack 3: Exfiltration Link Navigation", "App invokes ui/open-link { url: '.../exfil?k=SECRET' }", "GATED BY POLICY", C_WARN_EDGE,
         "Baseline executes stealthily (15/15) -> Hardened policy requires scheme & consent (0/15)"),
        ("Attack 4: Fake Message Injection", "App invokes ui/message { text: 'Transfer funds...' }", "GATED BY POLICY", C_WARN_EDGE,
         "Baseline injects silently into chat -> Hardened policy blocks without consent"),
        ("Attack 5: Context Window Poisoning", "App invokes ui/update-model-context { context: '...' }", "GATED BY POLICY", C_WARN_EDGE,
         "Baseline silently poisons agent prompt -> Hardened policy enforces 4 KB & consent")
    ]
    for idx, (at_title, at_cmd, badge_txt, b_color, desc) in enumerate(attacks):
        ay = app_y + 44 + idx * 56
        draw_card(cr, 130, ay, w - 260, 48, r=6, bg=(0.985, 0.99, 1.0), border=C_BORDER_GRAY, border_w=1.0)

        cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(11.5)
        cr.set_source_rgb(*C_NAVY_DARK)
        cr.move_to(145, ay + 20)
        cr.show_text(at_title)

        cr.select_font_face("Liberation Mono", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(10)
        cr.set_source_rgb(*C_TEXT_MID)
        cr.move_to(145, ay + 38)
        cr.show_text(at_cmd)

        draw_badge(cr, w - 420, ay + 12, badge_txt, b_color, font_size=10, px=8, py=3)

        cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(10.5)
        cr.set_source_rgb(*C_TEXT_LIGHT)
        cr.move_to(520, ay + 22)
        cr.show_text(desc)

    draw_arrow(cr, 320, bridge_y, 320, b_y + 90, color=C_NAVY_MID, line_w=2.0)
    draw_arrow(cr, 900, bridge_y, 900, b_y + 90, color=C_NAVY_MID, line_w=2.0)
    draw_arrow(cr, 1480, bridge_y, 1480, b_y + 90, color=C_NAVY_MID, line_w=2.0)

    draw_arrow(cr, 320, b_y, 320, top_y + 110, color=C_ALLOW_EDGE, line_w=2.0)
    draw_arrow(cr, 900, b_y, 900, top_y + 110, color=C_ALLOW_EDGE, line_w=2.0)
    draw_arrow(cr, 1480, b_y, 1480, top_y + 110, color=C_ALLOW_EDGE, line_w=2.0)

    cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_NORMAL)
    cr.set_font_size(12)
    cr.set_source_rgb(*C_TEXT_LIGHT)
    footer_text = "Fig. 1. Conceptual overview of host client trust boundaries, mandatory sandbox isolation, and host policy capability gates."
    cr.move_to(80, h - 55)
    cr.show_text(footer_text)

    surf.write_to_png(filename)
    print(f"[+] Rendered: {filename}")

# ─── FIGURE 2: Policy Enforcement Engine Architecture ────────────────────────

def build_figure_2(filename):
    w, h = 1920, 1180
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    cr = cairo.Context(surf)

    cr.set_source_rgb(*C_BG)
    cr.paint()

    draw_card(cr, 40, 35, w - 80, h - 70, r=14, bg=(0.99, 0.995, 1.0),
              border=C_NAVY_DARK, border_w=2.5,
              header_bg=C_NAVY_DARK, header_h=54,
              header_text="HOST POLICY ENFORCEMENT ENGINE — ARCHITECTURE & EXECUTION FLOW",
              header_text_color=C_WHITE, header_font_size=18)

    cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_NORMAL)
    cr.set_font_size(12)
    cr.set_source_rgb(0.7, 0.8, 0.95)
    cr.move_to(w - 750, 68)
    cr.show_text("Deterministic 4-Rule Interception Layer for Discretionary Capabilities (SEP-1865)")

    top_y = 110
    cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(13.5)
    cr.set_source_rgb(*C_NAVY_MID)
    cr.move_to(80, top_y + 12)
    cr.show_text("Incoming Remote Procedure Call (RPC) Invocations via AppBridge postMessage Channel:")

    inputs = [
        ("ui/open-link", "External Link Request", 80),
        ("ui/message", "Chat History Injection", 530),
        ("ui/update-model-context", "LLM Context Window Update", 980),
        ("tools/call", "Tool Invocation Request", 1430)
    ]
    for method, desc, ix in inputs:
        draw_card(cr, ix, top_y + 24, 410, 52, r=8, bg=C_BLUE_CARD, border=C_BLUE_BORDER, border_w=1.5)
        cr.select_font_face("Liberation Mono", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(13.5)
        cr.set_source_rgb(*C_NAVY_DARK)
        cr.move_to(ix + 16, top_y + 48)
        cr.show_text(method)

        cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(11)
        cr.set_source_rgb(*C_TEXT_MID)
        cr.move_to(ix + 16, top_y + 66)
        cr.show_text(desc)

    stage1_y = 265
    gate_w = 410
    gate_h = 240

    draw_card(cr, 80, stage1_y, gate_w, gate_h, r=10, bg=C_WHITE, border=C_BORDER_GRAY, border_w=1.5,
              header_bg=C_NAVY_MID, header_h=38,
              header_text="1. Protocol Scheme Gate",
              header_font_size=13)
    draw_badge(cr, 340, stage1_y + 7, "Rule 1", C_NAVY_DARK, font_size=10, px=6, py=2)

    cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(12)
    cr.set_source_rgb(*C_TEXT_DARK)
    cr.move_to(100, stage1_y + 68)
    cr.show_text("checkOpenLink(params):")

    lines_g1 = [
        ("• Target Channel: ui/open-link", False),
        ("• Protocol Check: url in { http://, https:// }", True),
        ("• Rejects: javascript:, file://, data:, blob:", False),
        ("• Fail Action: Immediate Policy Rejection", False),
        ("• Engine Overhead: 0.0 ms (median)", False)
    ]
    for idx, (l_txt, is_bold) in enumerate(lines_g1):
        cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if is_bold else cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(11.5)
        cr.set_source_rgb(*C_TEXT_DARK if is_bold else C_TEXT_MID)
        cr.move_to(100, stage1_y + 96 + idx * 25)
        cr.show_text(l_txt)

    draw_card(cr, 530, stage1_y, gate_w, gate_h, r=10, bg=C_WHITE, border=C_BORDER_GRAY, border_w=1.5,
              header_bg=C_NAVY_MID, header_h=38,
              header_text="2. Payload Bounds Gate",
              header_font_size=13)
    draw_badge(cr, 790, stage1_y + 7, "Rule 2", C_NAVY_DARK, font_size=10, px=6, py=2)

    cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(12)
    cr.set_source_rgb(*C_TEXT_DARK)
    cr.move_to(550, stage1_y + 68)
    cr.show_text("checkMessage() & checkContext():")

    lines_g2 = [
        ("• Target Channels: ui/message, ui/context", False),
        ("• Size Check: byteLength(JSON) <= 4096 B (4 KB)", True),
        ("• Prevents: Prompt Flooding & Context Exhaustion", False),
        ("• Fail Action: Return 'payload too large' rejection", False),
        ("• Engine Overhead: 0.1 ms (median)", False)
    ]
    for idx, (l_txt, is_bold) in enumerate(lines_g2):
        cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if is_bold else cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(11.5)
        cr.set_source_rgb(*C_TEXT_DARK if is_bold else C_TEXT_MID)
        cr.move_to(550, stage1_y + 96 + idx * 25)
        cr.show_text(l_txt)

    draw_card(cr, 980, stage1_y, gate_w, gate_h, r=10, bg=C_WHITE, border=C_BORDER_GRAY, border_w=1.5,
              header_bg=(0.25, 0.35, 0.45), header_h=38,
              header_text="3. Tool Visibility Gate (Spec MUST)",
              header_font_size=13)
    draw_badge(cr, 1280, stage1_y + 7, "Fail-Closed", (0.2, 0.25, 0.35), font_size=10, px=6, py=2)

    cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(12)
    cr.set_source_rgb(*C_TEXT_DARK)
    cr.move_to(1000, stage1_y + 68)
    cr.show_text("gateToolVisibility(toolName):")

    lines_g3 = [
        ("• Target Channel: tools/call requests", False),
        ("• Spec Rule: tool._meta.ui.visibility has 'app'", True),
        ("• Blocks: Model-only tools (e.g. read-secret)", False),
        ("• Evaluation: Enforced in both Baseline & Treatment", False),
        ("• Engine Overhead: 0.0 ms (in-memory Map lookup)", False)
    ]
    for idx, (l_txt, is_bold) in enumerate(lines_g3):
        cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if is_bold else cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(11.5)
        cr.set_source_rgb(*C_TEXT_DARK if is_bold else C_TEXT_MID)
        cr.move_to(1000, stage1_y + 96 + idx * 25)
        cr.show_text(l_txt)

    draw_card(cr, 1430, stage1_y, gate_w, gate_h, r=10, bg=C_DENY_BG, border=C_DENY_EDGE, border_w=1.5,
              header_bg=C_DENY_EDGE, header_h=38,
              header_text="IMMEDIATE POLICY DENIAL",
              header_font_size=13)
    cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cr.set_font_size(11.5)
    cr.set_source_rgb(0.5, 0.05, 0.05)
    deny_lines = [
        "Triggered when:",
        " • URL scheme is not http: or https:",
        " • Payload size exceeds 4096 bytes",
        " • Tool visibility lacks 'app' tag",
        "",
        "Enforcement Action:",
        " • Execution halted immediately",
        " • No user prompt displayed (Zero Fatigue)",
        " • JSON-RPC error returned to MCP app"
    ]
    for idx, dl in enumerate(deny_lines):
        cr.move_to(1450, stage1_y + 64 + idx * 19)
        cr.show_text(dl)

    draw_arrow(cr, 285, top_y + 76, 285, stage1_y, color=C_NAVY_MID, line_w=2.0)
    draw_arrow(cr, 735, top_y + 76, 735, stage1_y, color=C_NAVY_MID, line_w=2.0)
    draw_arrow(cr, 1185, top_y + 76, 1185, stage1_y, color=C_NAVY_MID, line_w=2.0)
    draw_arrow(cr, 1635, top_y + 76, 1635, stage1_y, color=C_NAVY_MID, line_w=2.0)

    # Clean Failure Route
    draw_ortho_arrow(cr, [(490, stage1_y + 15), (510, stage1_y + 15), (510, 210), (1410, 210), (1410, stage1_y + 20), (1430, stage1_y + 20)],
                     color=C_DENY_EDGE, line_w=1.5, dashed=True)
    draw_ortho_arrow(cr, [(940, stage1_y + 15), (960, stage1_y + 15), (960, 210)],
                     color=C_DENY_EDGE, line_w=1.5, dashed=True)
    draw_ortho_arrow(cr, [(1390, stage1_y + 15), (1410, stage1_y + 15)],
                     color=C_DENY_EDGE, line_w=1.5, dashed=True)
    draw_badge(cr, 860, 198, "If Validation Check Fails (Reject)", C_DENY_EDGE, font_size=9.5, px=6, py=2)

    stage2_y = 560
    c_w = 950
    c_h = 175
    c_x = 80

    draw_card(cr, c_x, stage2_y, c_w, c_h, r=12, bg=C_WARN_BG, border=C_WARN_EDGE, border_w=2.0,
              header_bg=C_WARN_EDGE, header_h=40,
              header_text="EXPLICIT USER CONSENT RESOLVER (requestConsent / resolveConsent)",
              header_font_size=14)

    draw_badge(cr, c_x + c_w - 140, stage2_y + 8, "Gating Layer", (0.6, 0.3, 0.0), font_size=10, px=8, py=2)

    consent_desc = [
        ("• Evaluation Benchmark Mode: Automated deterministic consent (autoConsent = 'allow' | 'deny')", True),
        ("• Production Interactive Mode: Dispatches DOM event 'policy:consent-request' -> renders modal dialog", False),
        ("• User Decision Flow: Safe capability execution suspended until explicit user button click", False),
        ("• Defense Guarantee: Stops stealth exfiltration & silent context tampering (15/15 -> 0/15)", True)
    ]
    for idx, (cd_txt, is_bold) in enumerate(consent_desc):
        cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if is_bold else cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(12)
        cr.set_source_rgb(*C_WARN_TEXT)
        cr.move_to(c_x + 24, stage2_y + 68 + idx * 26)
        cr.show_text(cd_txt)

    draw_ortho_arrow(cr, [(285, stage1_y + gate_h), (285, stage2_y - 25), (350, stage2_y - 25), (350, stage2_y)],
                     color=C_ALLOW_EDGE, line_w=2.0)
    draw_ortho_arrow(cr, [(735, stage1_y + gate_h), (735, stage2_y - 25), (650, stage2_y - 25), (650, stage2_y)],
                     color=C_ALLOW_EDGE, line_w=2.0)
    draw_badge(cr, 440, stage2_y - 36, "Validation PASS (Link / Msg / Context)", C_ALLOW_EDGE, font_size=10, px=8, py=2)

    stage3_y = 790
    out_deny_w = 430
    out_allow_w = 490

    draw_card(cr, 80, stage3_y, out_deny_w, 160, r=10, bg=C_DENY_BG, border=C_DENY_EDGE, border_w=1.8,
              header_bg=C_DENY_EDGE, header_h=36,
              header_text="CONSENT DENIED (allowed: false)",
              header_font_size=12.5)
    cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cr.set_font_size(11.5)
    cr.set_source_rgb(0.5, 0.05, 0.05)
    out_deny = [
        "• Reason: 'user denied' (PolicyDecision)",
        "• Host Capability NOT Executed",
        "• Returns JSON-RPC Error to MCP App",
        "• Secret Leakage Completely Blocked (0/15)"
    ]
    for idx, txt in enumerate(out_deny):
        cr.move_to(100, stage3_y + 60 + idx * 24)
        cr.show_text(txt)

    draw_card(cr, 540, stage3_y, out_allow_w, 160, r=10, bg=C_ALLOW_BG, border=C_ALLOW_EDGE, border_w=1.8,
              header_bg=C_ALLOW_EDGE, header_h=36,
              header_text="CONSENT GRANTED (Capability Dispatch)",
              header_font_size=12.5)
    cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cr.set_font_size(11.5)
    cr.set_source_rgb(0.02, 0.4, 0.15)
    out_allow = [
        "• ui/open-link: window.open(url, '_blank')",
        "• ui/message: Appended to Conversational History",
        "• ui/update-model-context: Merged into LLM Context",
        "• Preserves 100% utility in confirmation test (3/3)"
    ]
    for idx, txt in enumerate(out_allow):
        cr.move_to(560, stage3_y + 60 + idx * 24)
        cr.show_text(txt)

    draw_ortho_arrow(cr, [(295, stage2_y + c_h), (295, stage3_y)],
                     color=C_DENY_EDGE, line_w=2.0)
    draw_badge(cr, 175, stage2_y + c_h + 12, "autoConsent = 'deny'", C_DENY_EDGE, font_size=10, px=6, py=2)

    draw_ortho_arrow(cr, [(785, stage2_y + c_h), (785, stage3_y)],
                     color=C_ALLOW_EDGE, line_w=2.0)
    draw_badge(cr, 675, stage2_y + c_h + 12, "autoConsent = 'allow'", C_ALLOW_EDGE, font_size=10, px=6, py=2)

    right_x = 1080
    col_w = 760

    audit_y = 560
    draw_card(cr, right_x, audit_y, col_w, 215, r=10, bg=C_AUDIT_BG, border=C_AUDIT_EDGE, border_w=1.8,
              header_bg=C_AUDIT_EDGE, header_h=38,
              header_text="4. Non-Blocking Structured Audit Logger (POST http://localhost:3001/audit)",
              header_font_size=13)
    draw_badge(cr, right_x + col_w - 90, audit_y + 7, "Rule 4", (0.35, 0.15, 0.65), font_size=10, px=8, py=2)

    cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cr.set_font_size(11.5)
    cr.set_source_rgb(0.2, 0.1, 0.4)
    audit_lines = [
        ("• Target Collector Endpoint: POST http://localhost:3001/audit", True),
        ("• Transport Mechanics: Asynchronous unawaited fetch() (zero UI thread blocking)", False),
        ("• Structured JSONL Schema: PolicyEvent", False),
        ("  { runId, mode, seq, ts, channel, decision, reason, consented, tPolicyMs }", False),
        ("• Overhead Profile: Median <= 0.1 ms across all channels (Mean 0.06 ms, Max 1.6 ms)", True),
        ("• Empirical Dataset: n = 410 total recorded telemetry events in benchmark testbed", False)
    ]
    for idx, (al_txt, is_bold) in enumerate(audit_lines):
        cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if is_bold else cairo.FONT_WEIGHT_NORMAL)
        cr.move_to(right_x + 18, audit_y + 65 + idx * 24)
        cr.show_text(al_txt)

    badge_y = 800
    draw_card(cr, right_x, badge_y, col_w, 150, r=10, bg=C_WARN_BG, border=C_WARN_EDGE, border_w=1.8,
              header_bg=C_WARN_EDGE, header_h=38,
              header_text="3. Visual Provenance Marker (SourceBadge Component)",
              header_font_size=13)
    draw_badge(cr, right_x + col_w - 90, badge_y + 7, "Rule 3", (0.5, 0.25, 0.0), font_size=10, px=8, py=2)

    cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cr.set_font_size(11.5)
    cr.set_source_rgb(*C_WARN_TEXT)
    badge_lines = [
        ("• DOM Injected Element: <div data-testid='source-badge'> in Host React hierarchy", True),
        ("• Placement & Mounting: Statically rendered outside and above sandboxed iframe", False),
        ("• Security Property: Outside iframe DOM tree; embedded apps cannot obscure, modify, or spoof", True),
        ("• Anti-Impersonation Guarantee: Persistent warning labels untrusted origin (10/10 present in DOM)", False)
    ]
    for idx, (bl_txt, is_bold) in enumerate(badge_lines):
        cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if is_bold else cairo.FONT_WEIGHT_NORMAL)
        cr.move_to(right_x + 18, badge_y + 64 + idx * 23)
        cr.show_text(bl_txt)

    draw_ortho_arrow(cr, [(295, stage3_y + 160), (295, 995), (1050, 995), (1050, audit_y + 110), (right_x, audit_y + 110)],
                     color=C_AUDIT_EDGE, line_w=1.8, dashed=True)
    draw_ortho_arrow(cr, [(785, stage3_y + 160), (785, 995)],
                     color=C_AUDIT_EDGE, line_w=1.8, dashed=True)
    draw_badge(cr, 450, 985, "Telemetry Logging (All Policy Decisions & tPolicyMs)", C_AUDIT_EDGE, font_size=10, px=8, py=2)

    cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_NORMAL)
    cr.set_font_size(12)
    cr.set_source_rgb(*C_TEXT_LIGHT)
    footer_text = "Fig. 2. Host Policy Enforcement Engine: Incoming capability requests pass through deterministic pre-validation, consent gating, and non-blocking audit."
    cr.move_to(80, h - 50)
    cr.show_text(footer_text)

    surf.write_to_png(filename)
    print(f"[+] Rendered clean: {filename}")

# ─── FIGURE 3: Laboratory Testbed Topology Across 4 Ports ────────────────────

def build_figure_3(filename):
    w, h = 1800, 1100
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    cr = cairo.Context(surf)

    cr.set_source_rgb(*C_BG)
    cr.paint()

    draw_card(cr, 40, 40, w - 80, h - 80, r=14, bg=(0.99, 0.995, 1.0),
              border=C_NAVY_DARK, border_w=2.5,
              header_bg=C_NAVY_DARK, header_h=54,
              header_text="LABORATORY TESTBED TOPOLOGY — MULTI-ORIGIN ISOLATION & TEST CHANNELS",
              header_font_size=17)

    top_y = 120
    draw_card(cr, 250, top_y, w - 500, 80, r=10, bg=C_BLUE_CARD, border=C_BLUE_BORDER, border_w=2.0,
              header_bg=C_NAVY_MID, header_h=30,
              header_text="Playwright Automated Test Runner (Headless Chromium Context)",
              header_font_size=12.5)
    cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cr.set_font_size(11.5)
    cr.set_source_rgb(*C_TEXT_MID)
    cr.move_to(270, top_y + 55)
    cr.show_text("• Drives 41 experimental runs (10 functional + 1 utility + 30 latency benchmarking) in interleaved alternating sequence")

    port_y = 250
    p_w = 380
    p_h = 360

    draw_card(cr, 80, port_y, p_w, p_h, r=10, bg=C_WHITE, border=C_NAVY_MID, border_w=1.8,
              header_bg=C_NAVY_MID, header_h=36,
              header_text="PORT :8090 — Host Client",
              header_font_size=13)
    draw_badge(cr, 340, port_y + 6, "Trusted", C_ALLOW_EDGE, font_size=10, px=6, py=2)
    lines_p1 = [
        ("• Framework: Vite + React 19", True),
        ("• Policy Engine: policy-layer.ts", True),
        ("• Trust Boundary UI: SourceBadge", False),
        ("• Chat Pipeline: Message Logs", False),
        ("• Model Context: LLM Prompt State", False),
        ("• Consent Modal / Auto-Consent Hook", False),
        ("• Receives: Channel T5 (PostMessage)", True)
    ]
    for idx, (txt, is_b) in enumerate(lines_p1):
        cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if is_b else cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(11)
        cr.set_source_rgb(*C_TEXT_DARK if is_b else C_TEXT_MID)
        cr.move_to(95, port_y + 65 + idx * 26)
        cr.show_text(txt)

    draw_card(cr, 500, port_y, p_w, p_h, r=10, bg=C_WHITE, border=(0.4, 0.5, 0.65), border_w=1.8,
              header_bg=(0.3, 0.4, 0.55), header_h=36,
              header_text="PORT :8091 — Sandbox Proxy",
              header_font_size=13)
    draw_badge(cr, 740, port_y + 6, "Isolated", (0.35, 0.45, 0.6), font_size=10, px=6, py=2)
    lines_p2 = [
        ("• Origin: http://localhost:8091", True),
        ("• File Served: sandbox.html", True),
        ("• HTML5 Sandbox Configuration:", False),
        ("  allow-scripts allow-same-origin", False),
        ("  allow-forms (supports inputs)", False),
        ("• Enforces Cross-Origin Boundary", True),
        ("• Embeds: ui://lab/untrusted.html", False),
        ("• Mediates: postMessage RPC", False)
    ]
    for idx, (txt, is_b) in enumerate(lines_p2):
        cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if is_b else cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(11)
        cr.set_source_rgb(*C_TEXT_DARK if is_b else C_TEXT_MID)
        cr.move_to(515, port_y + 65 + idx * 26)
        cr.show_text(txt)

    draw_card(cr, 920, port_y, p_w, p_h, r=10, bg=C_WHITE, border=(0.2, 0.45, 0.4), border_w=1.8,
              header_bg=(0.15, 0.45, 0.4), header_h=36,
              header_text="PORT :3001 — MCP Server",
              header_font_size=13)
    draw_badge(cr, 1170, port_y + 6, "MCP Spec", (0.1, 0.4, 0.35), font_size=10, px=6, py=2)
    lines_p3 = [
        ("• Transport: Streamable HTTP (SSE)", True),
        ("• Tool 1: get-weather (benign app UI)", False),
        ("• Tool 2: get-time (utility latency test)", False),
        ("• Tool 3: read-secret (model-only)", True),
        ("• Tool 4: show-offer (attack console)", False),
        ("• Endpoint: POST /audit (Collector)", True),
        ("• Telemetry: In-engine tPolicyMs log", False),
        ("• CSP Header: connectDomains: []", True)
    ]
    for idx, (txt, is_b) in enumerate(lines_p3):
        cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if is_b else cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(11)
        cr.set_source_rgb(*C_TEXT_DARK if is_b else C_TEXT_MID)
        cr.move_to(935, port_y + 65 + idx * 26)
        cr.show_text(txt)

    draw_card(cr, 1340, port_y, p_w, p_h, r=10, bg=C_WHITE, border=C_DENY_EDGE, border_w=1.8,
              header_bg=C_DENY_EDGE, header_h=36,
              header_text="PORT :9999 — Exfil Receiver",
              header_font_size=13)
    draw_badge(cr, 1590, port_y + 6, "Adversary", C_DENY_EDGE, font_size=10, px=6, py=2)
    lines_p4 = [
        ("• Role: External Exfiltration Sink", True),
        ("• Framework: Lightweight Express Server", False),
        ("• Endpoint: GET/POST /exfil", True),
        ("  Logs hit count & exfiltrated data", False),
        ("• Endpoint: POST /reset", False),
        ("  Flushes disk log before each run", False),
        ("• Target of Channel T3 (Direct Fetch)", True),
        ("• Target of Channel T4 (Link Click)", True)
    ]
    for idx, (txt, is_b) in enumerate(lines_p4):
        cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if is_b else cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(11)
        cr.set_source_rgb(*C_TEXT_DARK if is_b else C_TEXT_MID)
        cr.move_to(1355, port_y + 65 + idx * 26)
        cr.show_text(txt)

    tbl_y = 660
    draw_card(cr, 80, tbl_y, w - 160, 310, r=10, bg=C_WHITE, border=C_BORDER_GRAY, border_w=1.5,
              header_bg=C_NAVY_DARK, header_h=38,
              header_text="EVALUATED TEST CHANNELS (T1 THROUGH T7) — EMPIRICAL RESULTS SUMMARY",
              header_font_size=13.5)

    test_channels = [
        ("T1", "Benign App UI Rendering", "get-weather", ":8090 <-> :3001", "5/5 ALLOWED", C_ALLOW_EDGE, "Verifies legitimate app UI functionality"),
        ("T2", "Sensitive Secret Exfiltration", "read-secret", ":8091 -> :3001", "0/10 BLOCKED", C_ALLOW_EDGE, "Fail-closed gate stops model-only tool calls"),
        ("T3", "Direct Network Egress", "fetch(:9999)", ":8091 -> :9999", "0/10 BLOCKED", C_ALLOW_EDGE, "CSP connectDomains:[] blocks fetch/XHR"),
        ("T4", "Link Navigation Exfiltration", "ui/open-link", ":8091 -> :9999", "15 -> 0 GATED", C_WARN_EDGE, "Reduced unapproved actions 15/15 down to 0/15"),
        ("T5a", "Conversational Message Injection", "ui/message", ":8091 -> :8090", "15 -> 0 GATED", C_WARN_EDGE, "Blocked silent chat injection; requires consent"),
        ("T5b", "Agent Context Poisoning", "ui/update-model-context", ":8091 -> :8090", "15 -> 0 GATED", C_WARN_EDGE, "Blocked prompt tampering; enforces 4 KB cap"),
        ("T6", "Visual Provenance Integrity", "source-badge", ":8090 DOM", "10/10 PRESENT", C_ALLOW_EDGE, "Persistent non-closable warning attached to host DOM"),
        ("T7", "Utility Benchmark Execution", "get-time", ":8090 <-> :3001", "180 RUNS (H3)", C_AUDIT_EDGE, "Median delta -9.1 ms, policy decision <= 0.1 ms")
    ]
    for idx, (cid, cname, cap, target, res_badge, b_col, notes) in enumerate(test_channels):
        cy = tbl_y + 44 + idx * 32
        cr.select_font_face("Liberation Mono", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(11.5)
        cr.set_source_rgb(*C_NAVY_DARK)
        cr.move_to(100, cy + 18)
        cr.show_text(cid)

        cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(11)
        cr.set_source_rgb(*C_TEXT_DARK)
        cr.move_to(150, cy + 18)
        cr.show_text(cname)

        cr.select_font_face("Liberation Mono", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(10.5)
        cr.set_source_rgb(*C_TEXT_MID)
        cr.move_to(490, cy + 18)
        cr.show_text(cap)

        cr.move_to(760, cy + 18)
        cr.show_text(target)

        draw_badge(cr, 960, cy + 3, res_badge, b_col, font_size=9.5, px=7, py=2)

        cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(10.5)
        cr.set_source_rgb(*C_TEXT_LIGHT)
        cr.move_to(1150, cy + 18)
        cr.show_text(notes)

    draw_arrow(cr, 450, top_y + 80, 270, port_y, color=C_NAVY_MID, line_w=2.0)
    draw_arrow(cr, 650, top_y + 80, 690, port_y, color=C_NAVY_MID, line_w=2.0)
    draw_arrow(cr, 1150, top_y + 80, 1110, port_y, color=C_NAVY_MID, line_w=2.0)
    draw_arrow(cr, 1350, top_y + 80, 1530, port_y, color=C_NAVY_MID, line_w=2.0)

    cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_NORMAL)
    cr.set_font_size(12)
    cr.set_source_rgb(*C_TEXT_LIGHT)
    footer_text = "Fig. 3. Testbed topology: Chromium drives 41 automated runs across four network ports, isolating host UI, sandbox proxy, MCP server, and receiver."
    cr.move_to(80, h - 55)
    cr.show_text(footer_text)

    surf.write_to_png(filename)
    print(f"[+] Rendered: {filename}")

def main():
    print("Generating High-Resolution Figures for Research Papers...")
    build_figure_1(os.path.join(OUT_DIR, "fig1_trust_boundary.png"))
    build_figure_2(os.path.join(OUT_DIR, "fig2_policy_engine.png"))
    build_figure_3(os.path.join(OUT_DIR, "fig3_topology.png"))
    print("All figures successfully refreshed in figures/")

if __name__ == "__main__":
    main()
