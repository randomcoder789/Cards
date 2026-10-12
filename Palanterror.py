import json
import math
import os
import random
import time
import tkinter as tk
from typing import List, Optional
from engine import Game
from cards import CARDS, PRIV, TIERS, PRESETS, DEFAULTS, STORY, RULES

BG, PANEL, LINE = "#dce2dc", "#eef0e9", "#9da99e"
DIM, FG, HI = "#53625a", "#28362f", "#14211b"
AMBER, RED, TEAL = "#a8581a", "#a53b34", "#206d70"
KINDS = {"EXEC": ("executable", RED), "DAEMON": ("daemon", TEAL), "OPT": ("optimizer", FG), "EXPLOIT": ("exploit", AMBER)}
SAVE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "save.json")

OPTS = [
    ("ice", "ICE strength", list(range(60, 161, 10)), "{}%"),
    ("trace", "trace speed", list(range(50, 201, 10)), "{}%"),
    ("ram", "starting RAM", [8], "{} GB"),
    ("hand", "hand size", [4, 5, 6], "{}"),
    ("timer", "extraction timer", [8, 10, 12, 15, 20, 25, 30, 40], "{} s"),
    ("extract", "extraction check", [True, False], None),
    ("shake", "screen shake", [True, False], None),
    ("typing", "text speed", ["slow", "normal", "instant"], "{}"),
    ("story", "story intro", [True, False], None),
]
BALANCE = ("ice", "trace", "ram", "hand", "timer")


def load():
    data = {}
    try:
        with open(SAVE) as f:
            data = json.load(f)
    except (OSError, ValueError):
        pass
    if not isinstance(data, dict):
        data = {}
    cfg = dict(DEFAULTS)
    saved = data.get("settings", {})
    if isinstance(saved, dict):
        cfg.update({k: v for k, v in saved.items() if k in DEFAULTS})
    for key, _, vals, _ in OPTS:
        if cfg[key] not in vals:
            cfg[key] = DEFAULTS[key]
    if cfg["preset"] not in ("easy", "normal", "hard", "custom"):
        cfg["preset"] = "normal"
    stats = {"best": 0, "wins": 0, "runs": 0}
    if isinstance(data.get("stats"), dict):
        stats.update({k: v for k, v in data["stats"].items() if k in stats and isinstance(v, int)})
    return cfg, stats


def font(size=10, bold=False):
    return ("Consolas", size, "bold" if bold else "normal")


def ui_font(size=10, bold=False):
    return ("Bahnschrift", size, "bold" if bold else "normal")


def label(parent, text="", fg=FG, size=10, bold=False, **kw):
    return tk.Label(parent, text=text, fg=fg, bg=kw.pop("bg", BG), font=ui_font(size, bold), **kw)


def button(parent, text, cmd, fg=AMBER, size=11, **kw):
    return tk.Button(parent, text=text, command=cmd, bg=PANEL, fg=fg, bd=0, font=ui_font(size, True), takefocus=0,
                     activebackground=fg, activeforeground=BG, highlightthickness=1, highlightbackground=fg,
                     cursor="hand2", **kw)


def canvas(parent, w, h, bg=PANEL, border=LINE):
    return tk.Canvas(parent, width=w, height=h, bg=bg, highlightthickness=1, highlightbackground=border)


class App:
    def __init__(self, root):
        self.root = root
        root.title("Palanterror")
        root.configure(bg=BG)
        root.geometry("1200x700")
        root.resizable(False, False)
        self.stage = tk.Frame(root, bg=BG)
        self.stage.place(x=0, y=0, relwidth=1, relheight=1)
        self.cfg, self.stats = load()
        self._game: Optional[Game] = None
        self.gen, self.mode, self.busy, self.clock = 0, "title", False, 0
        self.shake = self.hurt = self.flash = 0
        self.xp: Optional[tk.Canvas] = None
        self.parts, self.card_actions, self.pulse = [], [], False
        root.bind("<Key>", self.on_key)
        root.bind("<Button-1>", lambda _event: self.mode == "pager" and self.advance())
        self.tick()
        self.show_title()

    @property
    def g(self) -> Game:
        if self._game is None:
            raise RuntimeError("Game has not started")
        return self._game

    @g.setter
    def g(self, game: Game) -> None:
        self._game = game

    def save(self):
        try:
            with open(SAVE, "w") as f:
                json.dump({"settings": self.cfg, "stats": self.stats}, f)
        except OSError:
            pass

    def clear(self):
        for w in self.stage.winfo_children():
            w.destroy()
        self.xp = None
        self.stage.place(x=0, y=0, relwidth=1, relheight=1)

    def type(self, text, put, done=None, delay=12, skippable=False):
        gen = self.gen
        if self.cfg["typing"] == "instant":
            put(text)
            if done:
                done()
            return
        scale = 1.7 if self.cfg["typing"] == "slow" else 1

        def step(i=0):
            if gen != self.gen:
                return
            if i >= len(text):
                if done:
                    done()
                return
            end = len(text) if skippable and self.skip else i + 2
            put(text[i:end])
            wait = 130 if "\n" in text[i:end] else delay + random.randint(0, 8)
            self.root.after(int(wait * scale), lambda: step(end))

        step()

    def adder(self, lab):
        return lambda s: lab.config(text=lab.cget("text") + s)

    def later(self, ms, fn):
        gen = self.gen
        self.root.after(ms, lambda: gen == self.gen and fn())

    def show_title(self):
        self.gen += 1
        self.mode = "title"
        self.clear()
        c = tk.Canvas(self.stage, width=1200, height=700, bg=BG, highlightthickness=0)
        c.pack()
        nodes = [(90 + i * 204 + random.randint(-50, 50), 70 + j * 190 + random.randint(-40, 40)) for i in range(6) for j in range(4)]
        edges = []
        for a in nodes:
            near = sorted(nodes, key=lambda b: (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)[1:3]
            for b in near:
                edges.append((a[0], a[1], b[0], b[1]))
                c.create_line(a[0], a[1], b[0], b[1], fill=LINE)
        for x, y in nodes:
            c.create_rectangle(x - 4, y - 4, x + 4, y + 4, fill=BG, outline=DIM)
        packets = [[c.create_oval(0, 0, 6, 6, fill=TEAL, outline=""), random.choice(edges), random.random(),
                    random.uniform(0.004, 0.012)] for _ in range(16)]
        shadow = c.create_text(604, 254, text="PALANTERROR", fill="#b8c0b6", font=ui_font(54, True))
        title = c.create_text(600, 250, text="PALANTERROR", fill=HI, font=ui_font(54, True))
        c.create_text(600, 308, text="glitch protocol  //  infiltration", fill=AMBER, font=font(14))
        c.create_text(600, 336, text="break in. take the right file. get out.", fill=DIM, font=font(11))
        for i, (text, cmd) in enumerate((("new run", self.new_run), ("how to play", lambda: self.show_pages(RULES, self.show_title)),
                                         ("settings", self.show_settings), ("quit", self.root.destroy))):
            c.create_window(600, 410 + i * 54, window=button(c, text, cmd, width=18, pady=5))
        s = self.stats
        c.create_text(600, 660, text=f"best run: {s['best']}/5 layers     wins: {s['wins']}     runs: {s['runs']}",
                      fill=DIM, font=font(10))
        self.title_loop(c, packets, title, shadow, self.gen)

    def title_loop(self, c, packets, title, shadow, gen):
        if gen != self.gen:
            return
        for p in packets:
            p[2] += p[3]
            if p[2] > 1:
                p[1], p[2] = random.choice([q[1] for q in packets]), 0
            x1, y1, x2, y2 = p[1]
            x, y = x1 + (x2 - x1) * p[2], y1 + (y2 - y1) * p[2]
            c.coords(p[0], x - 3, y - 3, x + 3, y + 3)
        glitch = random.random() < 0.03
        word = "".join(random.choice("#%$&?") if glitch and random.random() < 0.25 else ch for ch in "PALANTERROR")
        c.itemconfig(title, text=word, fill=RED if glitch else HI)
        c.coords(shadow, 604 + (random.randint(-6, 6) if glitch else 0), 254)
        self.root.after(33, lambda: self.title_loop(c, packets, title, shadow, gen))

    def new_run(self):
        if self.cfg["story"]:
            self.show_pages(STORY, self.begin_run)
        else:
            self.begin_run()

    def show_pages(self, pages, then):
        self.gen += 1
        self.mode, self.pages, self.then, self.page = "pager", pages, then, 0
        self.clear()
        self.box = tk.Text(self.stage, bg=BG, fg=FG, font=ui_font(13), bd=0, highlightthickness=0, wrap="word",
                           padx=110, pady=100, cursor="arrow", spacing1=5, state="disabled")
        self.box.pack(fill="both", expand=True)
        self.hint = label(self.stage)
        self.hint.place(relx=0.5, rely=0.93, anchor="center")
        self.show_page()

    def put_page(self, s):
        self.box.config(state="normal")
        self.box.insert("end", s)
        self.box.config(state="disabled")

    def show_page(self):
        self.gen += 1
        self.skip, self.typing = False, True
        self.hint.config(text="")
        self.box.config(state="normal")
        self.box.delete("1.0", "end")
        self.box.config(state="disabled")
        self.type(self.pages[self.page], self.put_page, self.page_done, skippable=True)

    def page_done(self):
        self.typing = False
        self.blink(True)

    def blink(self, on):
        gen = self.gen
        word = "press any key  (esc skips)" if self.page < len(self.pages) - 1 else "press any key to continue"
        self.hint.config(text=f"[ {word} ]" if on else "")
        self.root.after(550, lambda: gen == self.gen and self.blink(not on))

    def advance(self):
        if self.typing:
            self.skip = True
        elif self.page < len(self.pages) - 1:
            self.page += 1
            self.show_page()
        else:
            self.then()

    def show_settings(self):
        self.gen += 1
        self.mode = "settings"
        self.clear()
        label(self.stage, "settings", HI, 22, True).pack(pady=(36, 4))
        label(self.stage, "choose a difficulty, or tune everything yourself", DIM, 11).pack()
        grid = tk.Frame(self.stage, bg=BG)
        grid.pack(pady=20)
        self.vals = {}
        rows = [("preset", "difficulty", ["easy", "normal", "hard", "custom"], "{}")] + OPTS
        for r, (key, title, vals, _fmt) in enumerate(rows):
            label(grid, title, FG, 11, anchor="w", width=20).grid(row=r, column=0, pady=5, sticky="w")
            button(grid, "<", lambda k=key, v=vals: self.step(k, v, -1), size=10, width=3, state="normal" if len(vals) > 1 else "disabled").grid(row=r, column=1)
            self.vals[key] = label(grid, "", HI, 11, True, width=12)
            self.vals[key].grid(row=r, column=2)
            button(grid, ">", lambda k=key, v=vals: self.step(k, v, 1), size=10, width=3, state="normal" if len(vals) > 1 else "disabled").grid(row=r, column=3)
        self.fmts = {k: f for k, _, _, f in rows}
        button(self.stage, "back", self.leave_settings, width=14).pack(pady=8)
        self.draw_settings()

    def draw_settings(self):
        for key, lab in self.vals.items():
            v, fmt = self.cfg[key], self.fmts[key]
            lab.config(text=("on" if v else "off") if fmt is None else fmt.format(v))

    def step(self, key, vals, d):
        self.cfg[key] = vals[(vals.index(self.cfg[key]) + d) % len(vals)]
        if key == "preset" and self.cfg["preset"] in PRESETS:
            self.cfg.update(PRESETS[self.cfg["preset"]])
        elif key in BALANCE:
            match = [n for n, p in PRESETS.items() if all(self.cfg[k] == v for k, v in p.items())]
            self.cfg["preset"] = match[0] if match else "custom"
        self.draw_settings()

    def leave_settings(self):
        self.save()
        self.show_title()

    def begin_run(self):
        self.gen += 1
        self.g = Game(dict(self.cfg))
        self.stats["runs"] += 1
        self.save()
        self.logged, self.logq, self.log_busy = 0, [], False
        self.shown = {"integrity": 100.0, "trace": 0.0, "ice": float(self.g.ice_hp)}
        self.shake = self.hurt = self.flash = 0
        self.parts, self.busy, self.mode = [], False, "game"
        self.pulse = False
        self.build_game()
        self.refresh_ui()
        self.transition("uplink established", self.queue_log, TIERS[0]["story"])

    def build_game(self):
        self.clear()
        head = tk.Frame(self.stage, bg=BG)
        head.pack(fill="x", padx=16, pady=(10, 4))
        label(head, "PALANTERROR", HI, 16, True).pack(side="left")
        self.banner = label(head, "", AMBER, 11, True)
        self.banner.pack(side="left", padx=24)
        button(head, "menu", self.show_title, fg=DIM, size=9, padx=8).pack(side="right")
        self.tierlbl = label(head, "", AMBER, 11)
        self.tierlbl.pack(side="right", padx=14)
        self.hud = canvas(self.stage, 1168, 96)
        self.hud.pack(padx=16, pady=4)
        mid = tk.Frame(self.stage, bg=BG)
        mid.pack(fill="x", padx=16)
        self.ice = canvas(mid, 520, 250)
        self.ice.pack(side="left")
        self.log = tk.Text(mid, bg=PANEL, fg=FG, font=font(10), wrap="word", state="disabled", bd=0, height=15,
                           highlightthickness=1, highlightbackground=LINE, padx=12, pady=10, cursor="arrow")
        self.log.pack(side="left", fill="both", expand=True, padx=(10, 0))
        for tag, col in (("sys", DIM), ("ok", FG), ("bad", RED), ("cmd", HI)):
            self.log.tag_configure(tag, foreground=col)
        self.mid = mid
        self.dframe = tk.Frame(self.stage, bg=BG)
        self.dframe.pack(fill="x", padx=16, pady=(8, 4))
        bottom = tk.Frame(self.stage, bg=BG)
        bottom.pack(fill="x", padx=16, pady=4)
        self.hframe = tk.Frame(bottom, bg=BG)
        self.hframe.pack(side="left")
        self.endbtn = button(bottom, "end turn\n[space]", self.end, width=10, height=4)
        self.endbtn.pack(side="right", anchor="s")

    def meter(self, x, y, w, name, frac, text, color):
        c = self.hud
        c.create_text(x, y, text=name, anchor="w", fill=DIM, font=font(9))
        c.create_text(x + w, y, text=text, anchor="e", fill=color, font=font(9, True))
        c.create_rectangle(x, y + 9, x + w, y + 21, outline=LINE, fill=BG)
        if frac > 0:
            c.create_rectangle(x + 1, y + 10, x + 1 + (w - 2) * min(1, frac), y + 20, outline="", fill=color)

    def draw_hud(self):
        g, c = self.g, self.hud
        c.delete("all")
        hp, tr = self.shown["integrity"], self.shown["trace"]
        self.meter(16, 14, 350, "integrity", hp / 100, f"{max(0, round(hp))}%",
                   RED if self.hurt or hp < 25 else AMBER if hp < 50 else FG)
        self.meter(400, 14, 350, "trace", tr / 100, f"{round(tr)}%", RED if tr >= 80 else AMBER if tr >= 50 else FG)
        over = g.used > g.ram_cap
        c.create_text(784, 14, text="ram", anchor="w", fill=DIM, font=font(9))
        c.create_text(1144, 14, text=f"{g.used}/{g.ram_cap} GB" + ("  over limit" if over else ""), anchor="e",
                      fill=RED if over else AMBER, font=font(9, True))
        n = g.base_ram
        slot = (360 - 3 * (n - 1)) / n
        for i in range(n):
            x = 784 + i * (slot + 3)
            if i >= g.ram_cap:
                c.create_rectangle(x, 23, x + slot, 35, outline=RED, fill=BG)
                c.create_line(x, 23, x + slot, 35, fill=RED)
                continue
            fill = TEAL if i < g.daemon_ram else (RED if over else AMBER) if i < g.used else BG
            c.create_rectangle(x, 23, x + slot, 35, fill=fill, outline=fill if fill != BG else LINE)
        x = 16
        for i, p in enumerate(PRIV):
            text = f"[{p.lower()}]" if i == g.priv else p.lower()
            c.create_text(x, 68, text=text, anchor="w", font=font(10, i == g.priv),
                          fill=HI if i == g.priv else FG if i < g.priv else DIM)
            x += len(text) * 8 + 22
        sig = "signature FLAGGED  trace x3" if g.flagged else f"signature clean  ({g.streak}/3)"
        c.create_text(400, 68, text=sig, anchor="w", fill=RED if g.flagged else FG, font=font(10))
        c.create_text(784, 68, text=f"shield {g.shield}    turn {g.turn}    deck {len(g.deck)}", anchor="w",
                      fill=FG, font=font(10))

    def art(self, c, tier, col, dim):
        t, cx, cy = self.clock / 30, 125, 125
        w = {"outline": col, "width": 2}
        if tier == 0:
            c.create_rectangle(cx - 70, cy - 22, cx + 70, cy + 28, **w)
            for k in range(4):
                lit = not dim and (self.clock // 8 + k) % 4 == 0
                c.create_rectangle(cx - 50 + k * 22, cy - 4, cx - 40 + k * 22, cy + 6, outline=col, fill=col if lit else PANEL)
            for s in (-1, 1):
                c.create_line(cx + s * 50, cy - 22, cx + s * 62, cy - 62, fill=col, width=2)
                c.create_oval(cx + s * 62 - 4, cy - 66, cx + s * 62 + 4, cy - 58, outline=col)
        elif tier == 1:
            for sx in (-62, 46):
                c.create_rectangle(cx + sx, cy - 52, cx + sx + 16, cy + 42, **w)
            lift = 0 if dim else 12 * (1 + math.sin(t * 2))
            for k in range(3):
                c.create_line(cx - 46, cy - 36 + k * 14 + lift, cx + 46, cy - 36 + k * 14 + lift, fill=col, width=2)
            c.create_rectangle(cx - 13, cy + 4, cx + 13, cy + 28, fill=PANEL, **w)
            c.create_arc(cx - 9, cy - 14, cx + 9, cy + 8, start=0, extent=180, style="arc", **w)
        elif tier == 2:
            dx, dy = (0, 0) if dim else (math.sin(t * 1.3) * 20, math.cos(t * 0.9) * 8)
            c.create_oval(cx - 74, cy - 38, cx + 74, cy + 38, **w)
            c.create_oval(cx - 26 + dx, cy - 26 + dy, cx + 26 + dx, cy + 26 + dy, **w)
            c.create_oval(cx - 10 + dx, cy - 10 + dy, cx + 10 + dx, cy + 10 + dy, fill=col if dim else RED, outline="")
            if not dim:
                c.create_line(cx + dx, cy + dy, cx + math.sin(t * 2) * 62, cy + 76, fill=col, dash=(3, 3))
        elif tier == 3:
            c.create_oval(cx - 66, cy - 66, cx + 66, cy + 66, **w)
            c.create_oval(cx - 48, cy - 48, cx + 48, cy + 48, outline=col)
            for k in range(6):
                a = (0 if dim else t * 0.6) + k * math.pi / 3
                c.create_line(cx, cy, cx + math.cos(a) * 48, cy + math.sin(a) * 48, fill=col, width=2)
            c.create_oval(cx - 10, cy - 10, cx + 10, cy + 10, fill=col, outline="")
        else:
            pts = []
            for k in range(12):
                r, a = (66 if k % 2 == 0 else 30), k * math.pi / 6 + (0 if dim else t * 0.4)
                j = 0 if dim else random.uniform(-2, 2)
                pts += [cx + math.cos(a) * r + j, cy + math.sin(a) * r - j]
            c.create_polygon(pts, fill="", **w)
            for s in (-1, 1):
                c.create_oval(cx + s * 12 - 5, cy - 5, cx + s * 12 + 5, cy + 5, fill=col if dim else RED, outline="")
        if dim:
            c.create_line(cx - 60, cy - 60, cx + 60, cy + 60, fill=RED, width=2)
            c.create_line(cx - 60, cy + 60, cx + 60, cy - 60, fill=RED, width=2)

    def draw_ice(self):
        g, c = self.g, self.ice
        c.delete("all")
        for y in range(2, 250, 5):
            c.create_line(0, y, 520, y, fill="#d7ddd5")
        t = TIERS[g.tier]
        down = g.ice_hp <= 0
        col = DIM if down else RED if self.flash % 4 >= 2 else FG
        c.create_text(16, 16, text=t["name"].lower(), anchor="w", fill=AMBER, font=font(10, True))
        for i in range(5):
            c.create_rectangle(424 + i * 16, 10, 434 + i * 16, 20, outline=AMBER, fill=AMBER if i <= g.tier else PANEL)
        self.art(c, g.tier, col, down)
        c.create_text(250, 58, text=t["ice"].lower(), anchor="w", fill=DIM if down else HI, font=font(12, True))
        hp = max(0, self.shown["ice"])
        c.create_text(250, 92, text="integrity", anchor="w", fill=DIM, font=font(9))
        c.create_text(500, 92, text=f"{round(hp)}/{g.ice_max}", anchor="e", fill=RED, font=font(9, True))
        c.create_rectangle(250, 102, 500, 114, outline=LINE, fill=BG)
        if hp > 0:
            c.create_rectangle(251, 103, 251 + 248 * hp / g.ice_max, 113, outline="", fill=RED)
        ok = g.priv >= t["min"]
        c.create_text(250, 138, text=f"strike  ~{g.ice_atk}", anchor="w", fill=FG, font=font(10))
        c.create_text(250, 160, text=f"needs   {PRIV[t['min']].lower()}" + ("" if ok else "  (damage halved)"),
                      anchor="w", fill=FG if ok else RED, font=font(10))
        c.create_text(250, 176, text=t["blurb"], anchor="nw", width=250, fill=DIM, font=font(9))
        c.create_text(250, 210, text="objective: " + t["goal"], anchor="nw", width=250, fill=AMBER, font=font(9, True))
        for x, y, _, _, _life, color in self.parts:
            c.create_rectangle(x, y, x + 3, y + 3, fill=color, outline="")

    def spawn(self, n, color, x=125, y=125):
        for _ in range(n):
            a, s = random.uniform(0, math.tau), random.uniform(1.5, 5)
            self.parts.append([x, y, math.cos(a) * s, math.sin(a) * s - 1, random.randint(10, 24), color])

    def draw_daemons(self):
        for w in self.dframe.winfo_children():
            w.destroy()
        label(self.dframe, "daemons:", DIM, 9).pack(side="left")
        if not self.g.daemons:
            label(self.dframe, "none running", DIM, 9).pack(side="left", padx=8)
        for d in self.g.daemons:
            tk.Button(self.dframe, text=f"{d}  {CARDS[d]['ram']} GB  x", bg=PANEL, fg=TEAL, bd=0, font=font(9), takefocus=0,
                      highlightthickness=1, highlightbackground=LINE, activebackground=LINE, cursor="hand2",
                      command=lambda n=d: self.uninstall(n)).pack(side="left", padx=5)

    def card(self, name, n, handler, note="", dim=False, risky=False):
        c = CARDS[name]
        kind, col = KINDS[c["kind"]]
        edge = AMBER if risky else LINE
        f = tk.Frame(self.hframe, bg=PANEL, width=136, height=190, highlightthickness=1, highlightbackground=edge)
        f.pack_propagate(False)
        f.pack(side="left", padx=4)
        kids: List[tk.Widget] = [f, tk.Frame(f, bg=DIM if dim else col, height=4)]
        kids[1].pack(fill="x")
        rows = [(name, DIM if dim else HI, 9, True), (f"[{n}] {kind}", DIM, 8, False),
                (f"{c['ram']} GB  ·  {PRIV[c['req']].lower()}", DIM if dim else AMBER, 9, False),
                (c["text"], DIM if dim else FG, 9, False)]
        if note:
            rows.append(("! " + note.lower(), RED if dim else AMBER, 8, True))
        for text, fg, size, bold in rows:
            kids.append(label(f, text, fg, size, bold, bg=PANEL, wraplength=124, justify="left", anchor="w"))
            kids[-1].pack(anchor="w", padx=6, pady=(7 if text == c["text"] else 2, 0))
        for w in kids:
            w.config(cursor="arrow" if dim else "hand2")
            w.bind("<Button-1>", lambda _event: handler(f))
            if not dim:
                w.bind("<Enter>", lambda _event: f.config(highlightbackground=HI))
                w.bind("<Leave>", lambda _event: f.config(highlightbackground=edge))
        self.card_actions.append(lambda: handler(f))

    def draw_hand(self):
        g = self.g
        for w in self.hframe.winfo_children():
            w.destroy()
        self.card_actions = []
        if g.state == "play":
            for i, name in enumerate(g.hand):
                why = g.locked(name)
                risky = why is None and g.used + CARDS[name]["ram"] > g.ram_cap
                self.card(name, i + 1, lambda w, i=i: self.click_card(i, w),
                          why or ("kernel panic risk" if risky else ""), why is not None, risky)
        elif g.state == "reward" and g.rewards:
            label(self.hframe, "clean copy.\ntake one tool\nwith you:", AMBER, 11, True, justify="left").pack(side="left", padx=14)
            for name in g.rewards:
                self.card(name, len(self.card_actions) + 1, lambda w, n=name: self.pick(n))
        elif g.state == "extract":
            label(self.hframe, "compare the target with every file.\nname, signer AND size must all match.\n"
                  "anything else is malware.\nclick a row, or press its number.", AMBER, 11, justify="left").pack(padx=14, pady=50)

    def refresh_ui(self):
        g = self.g
        self.tierlbl.config(text=TIERS[g.tier]["name"].lower())
        self.endbtn.config(state="normal" if g.state == "play" else "disabled")
        if g.state == "extract" and not self.xp:
            self.root.update_idletasks()
            self.xp = canvas(self.mid, 10, 10)
            self.xp.place(x=self.log.winfo_x(), y=self.log.winfo_y(), width=self.log.winfo_width(), height=self.log.winfo_height())
            self.xp.bind("<Motion>", lambda e: setattr(self, "hover", self.row_at(e.y)))
            self.xp.bind("<Leave>", lambda _event: setattr(self, "hover", -1))
            self.xp.bind("<Button-1>", lambda e: self.extract_click(self.row_at(e.y)))
            self.hover = -1
            self.ext_total = int(self.cfg["timer"])
            self.ext_end = time.monotonic() + self.ext_total
        elif g.state != "extract" and self.xp:
            self.xp.destroy()
            self.xp = None
        self.draw_hud()
        self.draw_ice()
        self.draw_daemons()
        self.draw_hand()

    def row_at(self, y):
        puzzle = self.g.puzzle
        if puzzle is None or y < 100:
            return -1
        i = (y - 100) // 18
        return i if 0 <= i < len(puzzle["files"]) else -1

    def draw_extract(self):
        c, p = self.xp, self.g.puzzle
        if c is None or p is None:
            return
        left = max(0, self.ext_end - time.monotonic())
        real = p["files"][p["answer"]]
        c.delete("all")
        c.create_text(14, 16, text="extraction  //  verify before you copy", anchor="w", fill=AMBER, font=font(11, True))
        tcol = RED if left < 5 else AMBER if left < 10 else FG
        c.create_text(624, 16, text=f"{left:.1f}s", anchor="e", fill=tcol, font=font(11, True))
        c.create_text(14, 42, text="target", anchor="w", fill=DIM, font=font(9))
        c.create_text(64, 42, text=real["name"], anchor="w", fill=HI, font=font(10, True))
        c.create_text(310, 42, text=real["host"], anchor="w", fill=HI, font=font(10, True))
        c.create_text(460, 42, text=f"{real['size']} KB", anchor="w", fill=HI, font=font(10, True))
        c.create_rectangle(14, 58, 624, 66, outline=LINE, fill=BG)
        c.create_rectangle(15, 59, 15 + 608 * left / self.ext_total, 65, outline="", fill=tcol)
        for x, name in ((64, "file"), (310, "signer"), (460, "size")):
            c.create_text(x, 86, text=name, anchor="w", fill=DIM, font=font(9))
        for i, f in enumerate(p["files"]):
            y, bad = 100 + i * 18, i in p["bad"]
            c.create_rectangle(8, y, 632, y + 16, fill=LINE if i == self.hover and not bad else PANEL, outline="")
            col = RED if bad else HI if i == self.hover else FG
            c.create_text(14, y + 8, text=f"[{i + 1}]", anchor="w", fill=DIM, font=font(9))
            c.create_text(64, y + 8, text=f["name"], anchor="w", fill=col, font=font(10))
            c.create_text(310, y + 8, text=f["host"], anchor="w", fill=col, font=font(10))
            c.create_text(460, y + 8, text=f"{f['size']} KB", anchor="w", fill=col, font=font(10))
            if bad:
                c.create_text(624, y + 8, text="INFECTED", anchor="e", fill=RED, font=font(9, True))

    def extract_click(self, i):
        if self.busy or self.mode != "game" or self.g.state != "extract":
            return
        self.g.extract_pick(i)
        self.after_action()

    def queue_log(self):
        new = self.g.log_total - self.logged
        if new > 0:
            self.logq += self.g.log[-new:]
        self.logged = self.g.log_total
        self.pump_log()

    def pump_log(self):
        if self.log_busy or not self.logq:
            return
        self.log_busy = True
        msg, tag = self.logq.pop(0)

        def put(s):
            self.log.config(state="normal")
            self.log.insert("end", s, tag)
            self.log.config(state="disabled")
            self.log.see("end")

        def done():
            self.log_busy = False
            self.pump_log()

        self.type(msg + "\n", put, done, delay=6)

    def tick(self):
        self.root.after(33, self.tick)
        if self.mode != "game" or self._game is None:
            return
        g = self._game
        self.clock += 1
        moved = False
        for key, target in (("integrity", g.integrity), ("trace", g.trace), ("ice", g.ice_hp)):
            d = target - self.shown[key]
            if d:
                step = max(0.8, abs(d) * 0.15)
                self.shown[key] = target if abs(d) <= step else self.shown[key] + step * (1 if d > 0 else -1)
                moved = True
        if self.hurt or self.flash:
            self.hurt, self.flash, moved = max(0, self.hurt - 1), max(0, self.flash - 1), True
        self.parts = [[p[0] + p[2], p[1] + p[3], p[2], p[3] + 0.3, p[4] - 1, p[5]] for p in self.parts if p[4] > 0]
        if moved:
            self.draw_hud()
        if self.clock % 2 == 0 or self.parts or self.flash:
            self.draw_ice()
        pulse = (g.trace >= 70 or g.integrity < 30) and self.clock % 30 < 15
        if pulse != self.pulse:
            self.pulse = pulse
            self.hud.config(highlightbackground=RED if pulse else LINE)
        if self.shake:
            s, self.shake = self.shake, self.shake - 1
            dx, dy = (random.randint(-s, s), random.randint(-s, s)) if self.shake else (0, 0)
            self.stage.place(x=dx, y=dy, relwidth=1, relheight=1)
        if self.xp:
            self.draw_extract()
            if time.monotonic() >= self.ext_end:
                g.extract_timeout()
                self.after_action()

    def after_action(self):
        g, gen = self.g, self.gen
        events, g.events = g.events, []
        for e in events:
            if e[0] == "ice_hit":
                self.flash = 8
                self.spawn(10, RED)
            elif e[0] == "breach":
                self.flash = 16
                self.spawn(40, FG)
            elif e[0] == "hurt":
                self.hurt = 10
                if self.cfg["shake"]:
                    self.shake = max(self.shake, min(10, 2 + e[1] // 2))
            elif e[0] in ("panic", "infected", "late"):
                if self.cfg["shake"]:
                    self.shake = 14
                self.spawn(30, RED)
                self.banner.config(text={"panic": "KERNEL PANIC", "infected": "MALWARE EXECUTED", "late": "TIME OUT"}[e[0]], fg=RED)
                self.root.after(1500, lambda: gen == self.gen and self.banner.config(text=""))
            elif e[0] == "clean":
                self.spawn(30, TEAL)
                self.banner.config(text="CLEAN COPY", fg=TEAL)
                self.root.after(1500, lambda: gen == self.gen and self.banner.config(text=""))
        self.queue_log()
        self.refresh_ui()
        if g.state in ("won", "lost"):
            self.busy = True
            self.root.after(1400, lambda: gen == self.gen and self.finish())
        elif g.state == "reward" and not g.rewards:
            self.pick(None)

    def click_card(self, i, widget):
        if self.busy or self.mode != "game" or self.g.state != "play" or i >= len(self.g.hand):
            return
        self.busy = True
        locked = self.g.locked(self.g.hand[i]) is not None
        widget.config(highlightbackground=RED if locked else AMBER)

        def go():
            self.g.play(i)
            self.busy = False
            self.after_action()

        self.later(180 if locked else 130, go)

    def end(self):
        if self.busy or self.mode != "game" or self.g.state != "play":
            return
        self.busy = True
        self.banner.config(text="ice is sweeping the network ...", fg=AMBER)

        def go():
            self.banner.config(text="")
            self.g.end_turn()
            self.busy = False
            self.after_action()

        self.later(600, go)

    def uninstall(self, name):
        if not self.busy and self.mode == "game":
            self.g.uninstall(name)
            self.after_action()

    def pick(self, name):
        if self.busy or self.mode != "game" or self.g.state != "reward":
            return

        def go():
            self.g.advance(name)
            self.shown["ice"] = 0.0
            self.after_action()

        nxt = TIERS[self.g.tier + 1]
        self.transition("breaching " + nxt["name"].lower(), go, nxt["story"])

    def transition(self, text, done, sub=""):
        gen, steps = self.gen, 64 if sub else 28
        self.busy = True
        ov = tk.Frame(self.stage, bg=BG)
        ov.place(x=0, y=0, relwidth=1, relheight=1)
        lbl = label(ov, text, HI, 16, True)
        lbl.place(relx=0.5, rely=0.38, anchor="center")
        bar = tk.Canvas(ov, width=320, height=10, bg=BG, highlightthickness=1, highlightbackground=LINE)
        bar.place(relx=0.5, rely=0.46, anchor="center")
        story = label(ov, "", FG, 12, justify="center", wraplength=620)
        story.place(relx=0.5, rely=0.58, anchor="center")
        self.type(sub, self.adder(story), delay=10)

        def step(n=0):
            if gen != self.gen:
                return
            bar.delete("all")
            bar.create_rectangle(0, 0, 320 * n / steps, 10, fill=FG, outline="")
            lbl.config(text=text + "." * (n % 4))
            if n < steps:
                self.root.after(40, lambda: step(n + 1))
            else:
                ov.destroy()
                self.busy = False
                done()

        step()

    def finish(self):
        g, st = self.g, self.stats
        won = g.state == "won"
        self.mode, self.busy = "over", False
        st["best"] = max(st["best"], g.tier + won)
        st["wins"] += won
        self.save()
        ov = tk.Frame(self.stage, bg=BG)
        ov.place(x=0, y=0, relwidth=1, relheight=1)
        box = tk.Frame(ov, bg=BG)
        box.place(relx=0.5, rely=0.45, anchor="center")
        title = label(box, "", FG if won else RED, 24, True, justify="left")
        title.pack(anchor="w")
        body = label(box, "", FG, 12, justify="left", wraplength=640)
        body.pack(anchor="w", pady=14)
        row = tk.Frame(box, bg=BG)
        stats = f"layers cleared: {g.tier + won}/5    turns: {g.turn}    trace: {g.trace}%    difficulty: {self.cfg['preset']}"
        head = "EXTRACTION COMPLETE" if won else "CONNECTION LOST"
        text = ("The Lantern publishes at dawn. Every name on the list will have a lawyer by morning.\n\n" if won
                else g.reason + "\n\n") + stats

        def show_buttons():
            row.pack(anchor="w")
            button(row, "reboot  [r]", self.begin_run, padx=14).pack(side="left", padx=(0, 10))
            button(row, "menu", self.show_title, fg=DIM, padx=14).pack(side="left")

        self.type(head, self.adder(title), lambda: self.type(text, self.adder(body), show_buttons, delay=14), delay=24)

    def on_key(self, e):
        if e.keysym in ("Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R", "Caps_Lock"):
            return
        if self.mode == "pager":
            self.then() if e.keysym == "Escape" else self.advance()
        elif self.mode != "game" and self.mode != "over" or self.busy:
            return
        elif self.mode == "over":
            if e.char.lower() == "r":
                self.begin_run()
        elif e.char.isdigit() and e.char != "0":
            k = int(e.char) - 1
            if self.g.state == "extract":
                self.extract_click(k)
            elif k < len(self.card_actions):
                self.card_actions[k]()
        elif e.char == " ":
            self.end()


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()