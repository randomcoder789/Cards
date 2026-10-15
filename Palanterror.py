import json
import math
import os
import random
import time
import tkinter as tk
from engine import Game
from cards import (CARDS, PRIV, TIERS, PRESETS, DEFAULTS, STORY, RULES, START, KIND_ORDER, DECK_MIN, DECK_MAX,
                   fmt_ram, copy_limit, deck_problem)

BG, PANEL, PANEL2, LINE = "#07080c", "#0e1118", "#161b26", "#252d3d"
DIM, FG, HI = "#6f7b93", "#c9d1e0", "#f5f8ff"
CYAN, RED, AMBER, GREEN = "#2fd5e6", "#ff3350", "#ffb02e", "#44dd88"
ICE_COL = "#ff4b63"
KINDS = {"EXEC": ("executable", RED), "DAEMON": ("daemon", CYAN), "OPT": ("optimizer", GREEN), "EXPLOIT": ("exploit", AMBER)}
SAVE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "save.json")

OPTS = [
    ("ice", "ICE strength", list(range(60, 161, 10)), "{}%"),
    ("trace", "trace speed", list(range(50, 201, 10)), "{}%"),
    ("ram", "starting RAM", [6, 8, 10, 12, 14, 16], "{} GB"),
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
    if cfg["preset"] in PRESETS:
        cfg.update(PRESETS[cfg["preset"]])
    stats = {"best": 0, "wins": 0, "runs": 0}
    if isinstance(data.get("stats"), dict):
        stats.update({k: v for k, v in data["stats"].items() if k in stats and isinstance(v, int)})
    return cfg, stats, load_decks(data)


def load_decks(data):
    raw = data.get("decks")
    slots = []
    if isinstance(raw, dict) and isinstance(raw.get("slots"), list):
        for s in raw["slots"][:3]:
            if isinstance(s, list) and all(isinstance(n, str) and n in CARDS for n in s):
                slots.append(list(s))
    while len(slots) < 3:
        slots.append(list(START))
    active = raw.get("active", 0) if isinstance(raw, dict) else 0
    return {"slots": slots, "active": active if active in (0, 1, 2) else 0}


def font(size=10, bold=False):
    return ("Consolas", size, "bold" if bold else "normal")


def ui_font(size=10, bold=False):
    return ("Bahnschrift", size, "bold" if bold else "normal")


def blend(a, b, t):
    pa = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    pb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(pa, pb))


def label(parent, text="", fg=FG, size=10, bold=False, **kw):
    return tk.Label(parent, text=text, fg=fg, bg=kw.pop("bg", BG), font=ui_font(size, bold), **kw)


def button(parent, text, cmd, fg=CYAN, size=11, **kw):
    b = tk.Button(parent, text=text, command=cmd, bg=PANEL, fg=fg, bd=0, font=ui_font(size, True), takefocus=0,
                  activebackground=fg, activeforeground=BG, disabledforeground=DIM, highlightthickness=1,
                  highlightbackground=fg, cursor="hand2", **kw)
    b.bind("<Enter>", lambda e: b.config(bg=blend(fg, BG, 0.82)) if str(b["state"]) == "normal" else None)
    b.bind("<Leave>", lambda e: b.config(bg=PANEL))
    return b


def canvas(parent, w, h, bg=BG):
    return tk.Canvas(parent, width=w, height=h, bg=bg, highlightthickness=0)


def cut_box(x1, y1, x2, y2, cut=10):
    return [x1 + cut, y1, x2, y1, x2, y2 - cut, x2 - cut, y2, x1, y2, x1, y1 + cut]


def panel(c, x1, y1, x2, y2, edge=LINE, fill=PANEL, accent=CYAN):
    c.create_polygon(cut_box(x1, y1, x2, y2), fill=fill, outline=edge)
    c.create_line(x1 + 14, y1, x1 + 54, y1, fill=accent, width=2)
    c.create_line(x2 - 54, y2, x2 - 14, y2, fill=accent, width=2)


def neon(c, kind, coords, col, w=2, fill="", **kw):
    make = getattr(c, "create_" + kind)
    halo = blend(col, BG, 0.75)
    if kind == "line":
        make(*coords, fill=halo, width=w + 3, **kw)
        make(*coords, fill=col, width=w, **kw)
    else:
        make(*coords, outline=halo, fill="", width=w + 3, **kw)
        make(*coords, outline=col, fill=fill, width=w, **kw)


def glyph(c, kind, x, y, col):
    if kind == "EXEC":
        c.create_line(x - 14, y - 10, x - 2, y, x - 14, y + 10, fill=col, width=3)
        c.create_line(x + 2, y + 10, x + 16, y + 10, fill=col, width=3)
    elif kind == "DAEMON":
        pts = []
        for k in range(6):
            a = k * math.pi / 3 + math.pi / 6
            pts += [x + math.cos(a) * 15, y + math.sin(a) * 15]
        c.create_polygon(pts, outline=col, fill="", width=2)
        c.create_oval(x - 4, y - 4, x + 4, y + 4, fill=col, outline="")
    elif kind == "OPT":
        for off, knob in ((-9, -7), (0, 6), (9, -1)):
            c.create_line(x - 15, y + off, x + 15, y + off, fill=blend(col, PANEL, 0.55), width=2)
            c.create_rectangle(x + knob - 3, y + off - 4, x + knob + 3, y + off + 4, fill=col, outline="")
    else:
        c.create_polygon(x + 4, y - 16, x - 9, y + 2, x - 1, y + 2, x - 5, y + 16, x + 10, y - 3, x + 2, y - 3,
                         fill=col, outline="")


class Rain:
    def __init__(self, c, w, h, cols, tint, fade=0.85):
        self.c, self.h = c, h
        self.cols = []
        for i in range(cols):
            x = 24 + i * (w - 48) / (cols - 1)
            text = "\n".join(random.choice("01ABCDEF") for _ in range(random.randint(8, 18)))
            item = c.create_text(x, 0, text=text, anchor="s", fill=blend(tint, BG, fade), font=font(10))
            self.cols.append([item, random.uniform(0, h), random.uniform(1.5, 4.5), x])

    def step(self):
        for col in self.cols:
            col[1] += col[2]
            if col[1] > self.h + 260:
                col[1] = -random.randint(0, 200)
            self.c.coords(col[0], col[3], col[1])


class App:
    def __init__(self, root):
        self.root = root
        root.title("Palanterror")
        root.configure(bg=BG)
        root.geometry("1200x700")
        root.resizable(False, False)
        self.stage = tk.Frame(root, bg=BG)
        self.stage.place(x=0, y=0, relwidth=1, relheight=1)
        self.cfg, self.stats, self.decks = load()
        self.g: Game = Game(dict(self.cfg), list(self.decks["slots"][self.decks["active"]]))
        self.gen, self.mode, self.busy, self.clock = 0, "title", False, 0
        self.shake = self.hurt = self.flash = 0
        self.xp = None
        self.hover = -1
        self.parts, self.card_actions, self.pulse = [], [], False
        self.ice_floats, self.hud_floats = [], []
        self.card_painters = {}
        root.bind("<Key>", self.on_key)
        root.bind("<Button-1>", lambda event: self.advance() if self.mode == "pager" and event.widget.winfo_exists() else None)
        self.tick()
        self.show_title()

    def save(self):
        try:
            with open(SAVE, "w") as f:
                json.dump({"settings": self.cfg, "stats": self.stats, "decks": self.decks}, f)
        except OSError:
            pass

    def clear(self):
        self.gen += 1
        for w in self.stage.winfo_children():
            w.destroy()
        self.xp = None
        self.stage.place(x=0, y=0, relwidth=1, relheight=1)

    def loop(self, fn, ms=33):
        gen = self.gen

        def run():
            if gen != self.gen:
                return
            fn()
            self.root.after(ms, run)

        run()

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
        self.mode = "title"
        self.clear()
        c = tk.Canvas(self.stage, width=1200, height=700, bg=BG, highlightthickness=0)
        c.pack()
        rain = Rain(c, 1200, 700, 34, CYAN, 0.9)
        nodes = [(90 + i * 204 + random.randint(-50, 50), 70 + j * 190 + random.randint(-40, 40)) for i in range(6) for j in range(4)]
        edges = []
        for a in nodes:
            near = sorted(nodes, key=lambda b: (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)[1:3]
            for b in near:
                edges.append((a[0], a[1], b[0], b[1]))
                c.create_line(a[0], a[1], b[0], b[1], fill=blend(LINE, BG, 0.25))
        for x, y in nodes:
            c.create_rectangle(x - 4, y - 4, x + 4, y + 4, fill=BG, outline=blend(DIM, BG, 0.3))
        packets = [[c.create_oval(0, 0, 6, 6, fill=CYAN, outline=""), random.choice(edges), random.random(),
                    random.uniform(0.004, 0.012)] for _ in range(16)]
        panel(c, 300, 170, 900, 360, edge=LINE, fill=BG)
        back = c.create_text(597, 245, text="PALANTERROR", fill=CYAN, font=ui_font(54, True))
        front = c.create_text(603, 245, text="PALANTERROR", fill=RED, font=ui_font(54, True))
        title = c.create_text(600, 245, text="PALANTERROR", fill=HI, font=ui_font(54, True))
        c.create_text(600, 308, text="glitch protocol  //  infiltration", fill=CYAN, font=font(14))
        c.create_text(600, 336, text="break in. take the right file. get out.", fill=DIM, font=font(11))
        menu = (("new run", self.new_run), ("deck builder", self.show_decks),
                ("how to play", lambda: self.show_pages(RULES, self.show_title)),
                ("settings", self.show_settings), ("quit", self.root.destroy))
        for i, (text, cmd) in enumerate(menu):
            c.create_window(600, 410 + i * 50, window=button(c, text, cmd, width=18, pady=3))
        deck = self.decks["slots"][self.decks["active"]]
        c.create_text(600, 640, text=f"active deck: deck {self.decks['active'] + 1}  ({len(deck)} cards)",
                      fill=CYAN, font=font(10))
        s = self.stats
        c.create_text(600, 665, text=f"best run: {s['best']}/5 layers     wins: {s['wins']}     runs: {s['runs']}",
                      fill=DIM, font=font(10))

        def spin():
            rain.step()
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
            c.itemconfig(back, text=word)
            c.itemconfig(front, text=word)
            spread = random.randint(5, 12) if glitch else 3
            c.coords(back, 600 - spread, 245)
            c.coords(front, 600 + spread, 245)

        self.loop(spin)

    def new_run(self):
        problem = deck_problem(self.decks["slots"][self.decks["active"]])
        if problem:
            self.show_decks(f"the active deck can't start a run: {problem}")
        elif self.cfg["story"]:
            self.show_pages(STORY, self.begin_run)
        else:
            self.begin_run()

    def show_pages(self, pages, then):
        self.mode, self.pages, self.then, self.page = "pager", pages, then, 0
        self.clear()
        self.box = tk.Text(self.stage, bg=BG, fg=FG, font=font(13), bd=0, highlightthickness=0, wrap="word",
                           padx=110, pady=100, cursor="arrow", spacing1=5, state="disabled")
        self.box.pack(fill="both", expand=True)
        self.hint = label(self.stage, fg=CYAN)
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
        self.mode = "settings"
        self.clear()
        label(self.stage, "settings", HI, 22, True).pack(pady=(36, 4))
        label(self.stage, "choose a difficulty, or tune everything yourself", DIM, 11).pack()
        grid = tk.Frame(self.stage, bg=BG)
        grid.pack(pady=20)
        self.vals, self.fmts = {}, {}
        rows = [("preset", "difficulty", ["easy", "normal", "hard", "custom"], "{}")] + OPTS
        for r, (key, title, vals, fmt) in enumerate(rows):
            on = "normal" if len(vals) > 1 else "disabled"
            label(grid, title, FG, 11, anchor="w", width=20).grid(row=r, column=0, pady=5, sticky="w")
            button(grid, "<", lambda k=key, v=vals: self.step(k, v, -1), size=10, width=3, state=on).grid(row=r, column=1)
            self.vals[key] = label(grid, "", HI, 11, True, width=12)
            self.vals[key].grid(row=r, column=2)
            button(grid, ">", lambda k=key, v=vals: self.step(k, v, 1), size=10, width=3, state=on).grid(row=r, column=3)
            self.fmts[key] = fmt
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

    def cur_deck(self):
        return self.decks["slots"][self.decks["active"]]

    def collection(self):
        want = self.dk["filter"]
        names = [n for n in CARDS if want == "all" or CARDS[n]["kind"] == want]
        return sorted(names, key=lambda n: (KIND_ORDER.index(CARDS[n]["kind"]), CARDS[n]["ram"], n))

    def deck_rows(self):
        return sorted(set(self.cur_deck()), key=lambda n: (KIND_ORDER.index(CARDS[n]["kind"]), CARDS[n]["ram"], n))

    def show_decks(self, note=""):
        self.mode = "decks"
        self.clear()
        self.dk = {"filter": "all", "scroll": 0, "hover": None, "note": note}
        self.hits = []
        c = canvas(self.stage, 1200, 700)
        c.pack()
        self.dc = c
        c.bind("<Motion>", self.deck_motion)
        c.bind("<Button-1>", lambda e: self.deck_click(e, 1))
        c.bind("<Button-3>", lambda e: self.deck_click(e, 3))
        c.bind("<MouseWheel>", lambda e: self.deck_wheel(-1 if e.delta > 0 else 1))
        c.bind("<Button-4>", lambda e: self.deck_wheel(-1))
        c.bind("<Button-5>", lambda e: self.deck_wheel(1))
        self.paint_decks()

    def hit(self, box, left, right=None):
        self.hits.append((box, left, right))

    def deck_click(self, e, b):
        for (x1, y1, x2, y2), left, right in reversed(self.hits):
            if x1 <= e.x <= x2 and y1 <= e.y <= y2:
                fn = left if b == 1 else right
                if fn:
                    fn()
                return

    def deck_wheel(self, d):
        self.dk["scroll"] += d * 3
        self.paint_decks()

    def deck_motion(self, e):
        name = None
        if 46 <= e.x <= 714 and 126 <= e.y < 126 + 17 * 24:
            names = self.collection()[self.dk["scroll"]:]
            r = (e.y - 126) // 24
            name = names[r] if r < len(names) else None
        elif 756 <= e.x <= 1154 and 150 <= e.y < 150 + 19 * 20:
            rows = self.deck_rows()
            r = (e.y - 150) // 20
            name = rows[r] if r < len(rows) else None
        if name != self.dk["hover"]:
            self.dk["hover"] = name
            self.paint_decks()

    def dbtn(self, box, text, fn, col=CYAN, on=False):
        x1, y1, x2, y2 = box
        self.dc.create_rectangle(box, outline=col, fill=blend(col, BG, 0.7) if on else PANEL)
        self.dc.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=text, fill=HI if on else col, font=ui_font(10, True))
        self.hit(box, fn)

    def deck_add(self, name):
        deck, limit = self.cur_deck(), copy_limit(name)
        if len(deck) >= DECK_MAX:
            self.dk["note"] = "the deck is full"
        elif deck.count(name) >= limit:
            self.dk["note"] = f"{name}: only {limit} allowed in a deck"
        else:
            deck.append(name)
            self.dk["note"] = ""
        self.save()
        self.paint_decks()

    def deck_remove(self, name):
        deck = self.cur_deck()
        if name in deck:
            deck.remove(name)
            self.dk["note"] = ""
            self.save()
            self.paint_decks()

    def deck_clear(self):
        self.cur_deck().clear()
        self.dk["note"] = ""
        self.save()
        self.paint_decks()

    def deck_reset(self):
        self.cur_deck()[:] = START
        self.dk["note"] = ""
        self.save()
        self.paint_decks()

    def pick_slot(self, i):
        self.decks["active"] = i
        self.dk["note"] = ""
        self.save()
        self.paint_decks()

    def pick_filter(self, key):
        self.dk["filter"], self.dk["scroll"] = key, 0
        self.paint_decks()

    def leave_decks(self):
        self.save()
        self.show_title()

    def paint_decks(self):
        c, dk, deck = self.dc, self.dk, self.cur_deck()
        c.delete("all")
        self.hits = []
        c.create_text(40, 34, text="deck builder", anchor="w", fill=HI, font=ui_font(20, True))
        c.create_text(40, 62, text="left click adds a card, right click removes one. the active deck is used for new runs.",
                      anchor="w", fill=DIM, font=font(10))
        for i in range(3):
            on = i == self.decks["active"]
            self.dbtn((690 + i * 158, 22, 840 + i * 158, 52), f"deck {i + 1}  ({len(self.decks['slots'][i])})",
                      lambda i=i: self.pick_slot(i), CYAN, on)
        chips = [("all", "all", CYAN)] + [(k, KINDS[k][0], KINDS[k][1]) for k in KIND_ORDER]
        for i, (key, text, col) in enumerate(chips):
            self.dbtn((40 + i * 118, 82, 148 + i * 118, 108), text, lambda k=key: self.pick_filter(k), col, dk["filter"] == key)
        panel(c, 40, 118, 722, 548)
        names, vis = self.collection(), 17
        dk["scroll"] = max(0, min(dk["scroll"], max(0, len(names) - vis)))
        for r, name in enumerate(names[dk["scroll"]:dk["scroll"] + vis]):
            y, card = 126 + r * 24, CARDS[name]
            col, count = KINDS[card["kind"]][1], deck.count(name)
            if name == dk["hover"]:
                c.create_rectangle(46, y, 700, y + 22, fill=PANEL2, outline="")
            c.create_rectangle(48, y + 3, 52, y + 19, fill=col, outline="")
            c.create_text(62, y + 11, text=name, anchor="w", fill=HI if count else FG, font=font(10, True))
            c.create_text(336, y + 11, text=fmt_ram(card["ram"]) if card["ram"] else "free", anchor="e", fill=AMBER, font=font(10))
            if card["req"]:
                c.create_text(350, y + 11, text=PRIV[card["req"]].lower() + "+", anchor="w", fill=DIM, font=font(9))
            text = card["text"] if len(card["text"]) < 28 else card["text"][:25] + "..."
            c.create_text(420, y + 11, text=text, anchor="w", fill=DIM, font=font(9))
            c.create_text(694, y + 11, text=f"{count}/{copy_limit(name)}", anchor="e", fill=CYAN if count else DIM, font=font(10, True))
            self.hit((46, y, 700, y + 22), lambda n=name: self.deck_add(n), lambda n=name: self.deck_remove(n))
        if len(names) > vis:
            c.create_rectangle(708, 128, 712, 536, fill=PANEL2, outline="")
            top = 128 + 408 * dk["scroll"] / len(names)
            c.create_rectangle(708, top, 712, top + 408 * vis / len(names), fill=CYAN, outline="")
        panel(c, 750, 118, 1160, 548)
        c.create_text(766, 134, text=f"deck {self.decks['active'] + 1}", anchor="w", fill=CYAN, font=font(11, True))
        rows = self.deck_rows()
        for r, name in enumerate(rows[:19]):
            y, card = 150 + r * 20, CARDS[name]
            if name == dk["hover"]:
                c.create_rectangle(756, y, 1154, y + 19, fill=PANEL2, outline="")
            c.create_rectangle(758, y + 3, 762, y + 16, fill=KINDS[card["kind"]][1], outline="")
            c.create_text(772, y + 10, text=name, anchor="w", fill=FG, font=font(10))
            c.create_text(1060, y + 10, text=fmt_ram(card["ram"]) if card["ram"] else "free", anchor="e", fill=AMBER, font=font(9))
            c.create_text(1144, y + 10, text=f"x{deck.count(name)}", anchor="e", fill=HI, font=font(10, True))
            self.hit((756, y, 1154, y + 19), lambda n=name: self.deck_remove(n), lambda n=name: self.deck_remove(n))
        if len(rows) > 19:
            c.create_text(772, 534, text=f"+{len(rows) - 19} more", anchor="w", fill=DIM, font=font(9))
        problem = deck_problem(deck)
        avg = sum(CARDS[n]["ram"] for n in deck) / len(deck) if deck else 0
        c.create_text(40, 568, text=f"cards {len(deck)}   (min {DECK_MIN}, max {DECK_MAX})", anchor="w",
                      fill=RED if problem else FG, font=font(11, True))
        c.create_text(330, 568, text=f"average cost {avg / 1000:.2f} GB", anchor="w", fill=FG, font=font(11))
        x = 580
        for k in KIND_ORDER:
            n = sum(1 for d in deck if CARDS[d]["kind"] == k)
            c.create_rectangle(x, 562, x + 10, 574, fill=KINDS[k][1], outline="")
            c.create_text(x + 16, 568, text=str(n), anchor="w", fill=FG, font=font(11))
            x += 64
        if dk["note"] or problem:
            c.create_text(40, 596, text=dk["note"] or problem, anchor="w", fill=RED, font=font(10, True))
        else:
            c.create_text(40, 596, text="deck is ready to run", anchor="w", fill=GREEN, font=font(10, True))
        if dk["hover"]:
            card = CARDS[dk["hover"]]
            c.create_text(40, 624, text=f"{dk['hover']}   {KINDS[card['kind']][0]}   {fmt_ram(card['ram']) if card['ram'] else 'free'}"
                          + (f"   needs {PRIV[card['req']].lower()}" if card["req"] else ""), anchor="w", fill=HI, font=font(10, True))
            c.create_text(40, 644, text=card["text"], anchor="w", fill=FG, font=font(10))
        self.dbtn((780, 656, 900, 686), "clear", self.deck_clear, RED)
        self.dbtn((910, 656, 1030, 686), "starter deck", self.deck_reset, AMBER)
        self.dbtn((1040, 656, 1160, 686), "done", self.leave_decks, CYAN, True)

    def begin_run(self):
        self.gen += 1
        self.g = Game(dict(self.cfg), list(self.decks["slots"][self.decks["active"]]))
        self.stats["runs"] += 1
        self.save()
        self.logged, self.logq, self.log_busy = 0, [], False
        self.shown = {"integrity": 100.0, "trace": 0.0, "ice": float(self.g.ice_hp)}
        self.shake = self.hurt = self.flash = 0
        self.parts, self.busy, self.mode = [], False, "game"
        self.ice_floats, self.hud_floats = [], []
        self.pulse = False
        self.build_game()
        self.refresh_ui()
        self.transition("uplink established", self.queue_log, TIERS[0]["story"])

    def build_game(self):
        self.clear()
        head = tk.Frame(self.stage, bg=BG)
        head.pack(fill="x", padx=16, pady=(10, 4))
        label(head, "PALANTERROR", HI, 16, True).pack(side="left")
        self.banner = label(head, "", CYAN, 11, True)
        self.banner.pack(side="left", padx=24)
        button(head, "menu", self.show_title, fg=DIM, size=9, padx=8).pack(side="right")
        self.tierlbl = label(head, "", CYAN, 11)
        self.tierlbl.pack(side="right", padx=14)
        self.hud = canvas(self.stage, 1168, 100)
        self.hud.pack(padx=16, pady=4)
        mid = tk.Frame(self.stage, bg=BG)
        mid.pack(fill="x", padx=16)
        self.ice = canvas(mid, 520, 250)
        self.ice.pack(side="left")
        self.logbox = tk.Frame(mid, bg=PANEL, highlightthickness=1, highlightbackground=LINE)
        self.logbox.pack(side="left", fill="both", expand=True, padx=(10, 0))
        label(self.logbox, "> palanterror.log", DIM, 9, bg=PANEL, anchor="w").pack(fill="x", padx=12, pady=(6, 0))
        self.log = tk.Text(self.logbox, bg=PANEL, fg=FG, font=font(10), wrap="word", state="disabled", bd=0, height=14,
                           highlightthickness=0, padx=12, pady=6, cursor="arrow")
        self.log.pack(fill="both", expand=True)
        for tag, col in (("sys", DIM), ("ok", GREEN), ("bad", RED), ("cmd", HI)):
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

    def caption(self, x, y, w, name, text, color):
        c = self.hud
        c.create_text(x, y, text=name, anchor="w", fill=DIM, font=font(9))
        c.create_text(x + w, y, text=text, anchor="e", fill=color, font=font(9, True))

    def bar(self, x, y, w, frac, color, n=25, h=12):
        gap = 2
        seg = (w - gap * (n - 1)) / n
        lit = round(min(1, max(0, frac)) * n)
        for i in range(n):
            x1 = x + i * (seg + gap)
            self.hud.create_rectangle(x1, y, x1 + seg, y + h, fill=color if i < lit else PANEL2, outline="")

    def draw_hud(self):
        g, c = self.g, self.hud
        c.delete("all")
        panel(c, 1, 1, 1167, 99, RED if self.pulse else LINE)
        hp, tr = self.shown["integrity"], self.shown["trace"]
        hp_col = RED if self.hurt or hp < 25 else AMBER if hp < 50 else GREEN
        tr_col = RED if tr >= 80 else AMBER if tr >= 50 else CYAN
        self.caption(16, 16, 350, "integrity", f"{max(0, round(hp))}%", hp_col)
        self.bar(16, 26, 350, hp / 100, hp_col)
        self.caption(400, 16, 350, "trace", f"{round(tr)}%", tr_col)
        self.bar(400, 26, 350, tr / 100, tr_col)
        limit = g.limit
        over = g.used > limit
        self.caption(784, 16, 360, "ram", f"{fmt_ram(g.used)}/{fmt_ram(limit)}" + ("  over limit" if over else ""),
                     RED if over else AMBER)
        n = max(g.base_ram, limit) // 250
        slot = (360 - (n - 1)) / n
        for i in range(n):
            x, lo = 784 + i * (slot + 1), i * 250
            if lo >= limit:
                c.create_rectangle(x, 26, x + slot, 38, outline=RED, fill=BG)
                continue
            fill = CYAN if lo < g.daemon_ram else (RED if over else AMBER) if lo < g.used else PANEL2
            c.create_rectangle(x, 26, x + slot, 38, fill=fill, outline="")
        x = 16
        for i, p in enumerate(PRIV):
            w = len(p) * 8 + 14
            now = i == g.priv
            c.create_rectangle(x, 54, x + w, 72, outline=CYAN if i <= g.priv else LINE, fill=CYAN if now else PANEL)
            c.create_text(x + w / 2, 63, text=p.lower(), fill=BG if now else CYAN if i < g.priv else DIM, font=font(9, now))
            x += w + 6
        c.create_text(400, 63, text="signature", anchor="w", fill=DIM, font=font(9))
        for i in range(3):
            lit = i < g.streak
            c.create_rectangle(484 + i * 20, 56, 498 + i * 20, 70, outline=RED if g.flagged else AMBER,
                               fill=(RED if g.flagged else AMBER) if lit else PANEL)
        c.create_text(556, 63, text="FLAGGED  trace x3" if g.flagged else "clean", anchor="w",
                      fill=RED if g.flagged else FG, font=font(9, g.flagged))
        c.create_text(784, 63, text=f"shield {g.shield}", anchor="w", fill=AMBER if g.shield else DIM, font=font(10, True))
        c.create_text(870, 63, text=f"layer {g.tier + 1}/5    turn {g.turn}", anchor="w", fill=FG, font=font(10))
        c.create_text(16, 86, text=f"deck {len(g.deck)}   discard {len(g.discard)}   played {g.played}", anchor="w",
                      fill=DIM, font=font(9))
        c.create_text(400, 86, text=f"next sweep +{g.sweep_gain}% trace", anchor="w", fill=RED if g.flagged else DIM, font=font(9))
        if g.stunned:
            c.create_text(784, 86, text="ICE stunned", anchor="w", fill=GREEN, font=font(9, True))
        for x, y, text, color, life in self.hud_floats:
            c.create_text(x, y, text=text, fill=color, font=font(14, True))

    def art(self, c, tier, col, down):
        t, cx, cy = self.clock / 30, 125, 130
        if tier == 0:
            neon(c, "rectangle", (cx - 68, cy + 6, cx + 68, cy + 46), col, fill=PANEL)
            for k in range(4):
                lit = not down and (self.clock // 8 + k) % 4 == 0
                c.create_rectangle(cx - 50 + k * 22, cy + 22, cx - 40 + k * 22, cy + 30, outline=col, fill=col if lit else PANEL)
            for s in (-1, 1):
                neon(c, "line", (cx + s * 52, cy + 6, cx + s * 60, cy - 50), col)
            if not down:
                for k in range(3):
                    if k < self.clock // 7 % 4:
                        r = 16 + k * 14
                        c.create_arc(cx - r, cy - 22 - r, cx + r, cy - 22 + r, start=55, extent=70, style="arc", outline=col, width=2)
        elif tier == 1:
            for sx in (-66, 50):
                neon(c, "rectangle", (cx + sx, cy - 56, cx + sx + 16, cy + 46), col, fill=PANEL)
            for k in range(4):
                y = cy - 40 + k * 22
                c.create_line(cx - 50, y, cx + 50, y, fill=blend(col, BG, 0.4), width=2)
            if not down:
                y = cy - 46 + (math.sin(t * 1.6) + 1) * 46
                c.create_line(cx - 50, y, cx + 50, y, fill=HI)
            neon(c, "rectangle", (cx - 13, cy + 2, cx + 13, cy + 28), col, fill=PANEL)
            neon(c, "arc", (cx - 9, cy - 16, cx + 9, cy + 6), col, start=0, extent=180, style="arc")
        elif tier == 2:
            dx, dy = (0, 0) if down else (math.sin(t * 1.3) * 20, math.cos(t * 0.9) * 8)
            neon(c, "oval", (cx - 76, cy - 40, cx + 76, cy + 40), col)
            neon(c, "oval", (cx - 26 + dx, cy - 26 + dy, cx + 26 + dx, cy + 26 + dy), col)
            c.create_oval(cx - 10 + dx, cy - 10 + dy, cx + 10 + dx, cy + 10 + dy, fill=col if down else RED, outline="")
            if not down:
                for k in (-1, 0, 1):
                    tx, ty = cx + k * 44 + math.sin(t * 2) * 26, cy + 88
                    c.create_line(cx + dx, cy + dy, tx, ty, fill=blend(col, BG, 0.45), dash=(3, 3))
                    f = (t * 0.8 + k * 0.3) % 1
                    px, py = cx + dx + (tx - cx - dx) * f, cy + dy + (ty - cy - dy) * f
                    c.create_rectangle(px - 2, py - 2, px + 2, py + 2, fill=HI, outline="")
        elif tier == 3:
            spin = 0 if down else t * 40
            for k, (r, ext) in enumerate(((68, 70), (52, 90), (36, 120))):
                way = 1 if k % 2 == 0 else -1
                for j in range(3):
                    c.create_arc(cx - r, cy - r, cx + r, cy + r, start=spin * way + j * 120 + k * 15, extent=ext,
                                 style="arc", outline=col, width=3)
            neon(c, "oval", (cx - 24, cy - 13, cx + 24, cy + 13), col, fill=PANEL)
            iris = 7 if down else 7 + 2 * math.sin(t * 2)
            c.create_oval(cx - iris, cy - iris, cx + iris, cy + iris, fill=col if down else RED, outline="")
        else:
            pts = []
            shift = 0 if down else random.uniform(-2, 2)
            for k in range(12):
                r, a = (68 if k % 2 == 0 else 30), k * math.pi / 6 + (0 if down else t * 0.4)
                pts += [cx + math.cos(a) * r + shift, cy + math.sin(a) * r - shift]
            if not down and self.clock % 23 < 3:
                c.create_polygon([p + 4 for p in pts], fill="", outline=CYAN, width=1)
            neon(c, "polygon", pts, col)
            for s in (-1, 1):
                c.create_polygon(cx + s * 22, cy - 6, cx + s * 6, cy - 2, cx + s * 22, cy + 4,
                                 fill=col if down else RED, outline="")
        if down:
            c.create_line(cx - 60, cy - 60, cx + 60, cy + 60, fill=RED, width=2)
            c.create_line(cx - 60, cy + 60, cx + 60, cy - 60, fill=RED, width=2)

    def draw_ice(self):
        g, c = self.g, self.ice
        c.delete("all")
        panel(c, 1, 1, 519, 249, RED if self.pulse else LINE)
        for x in range(30, 519, 30):
            c.create_line(x, 4, x, 246, fill="#10141d")
        for y in range(30, 249, 30):
            c.create_line(4, y, 516, y, fill="#10141d")
        t = TIERS[g.tier]
        down = g.ice_hp <= 0
        col = DIM if down else HI if self.flash % 4 >= 2 else ICE_COL
        c.create_text(16, 16, text=t["name"].lower(), anchor="w", fill=CYAN, font=font(10, True))
        for i in range(5):
            c.create_rectangle(424 + i * 16, 10, 434 + i * 16, 20, outline=CYAN, fill=CYAN if i <= g.tier else PANEL)
        self.art(c, g.tier, col, down)
        c.create_text(250, 58, text=t["ice"].lower(), anchor="w", fill=DIM if down else HI, font=font(12, True))
        hp = max(0, self.shown["ice"])
        c.create_text(250, 92, text="integrity", anchor="w", fill=DIM, font=font(9))
        c.create_text(500, 92, text=f"{round(hp)}/{g.ice_max}", anchor="e", fill=ICE_COL, font=font(9, True))
        segs = 20
        lit = math.ceil(segs * hp / g.ice_max) if hp > 0 else 0
        for i in range(segs):
            x = 250 + i * 12.5
            c.create_rectangle(x, 102, x + 10, 114, fill=ICE_COL if i < lit else PANEL2, outline="")
        ok = g.priv >= t["min"]
        c.create_text(250, 138, text=f"strike  ~{g.ice_atk}", anchor="w", fill=FG, font=font(10))
        c.create_text(250, 160, text=f"needs   {PRIV[t['min']].lower()}" + ("" if ok else "  (damage halved)"),
                      anchor="w", fill=FG if ok else RED, font=font(10))
        c.create_text(250, 176, text=t["blurb"], anchor="nw", width=250, fill=DIM, font=font(9))
        c.create_text(250, 210, text="objective: " + t["goal"], anchor="nw", width=250, fill=CYAN, font=font(9, True))
        for particle in self.parts:
            x, y, color = particle[0], particle[1], particle[5]
            c.create_rectangle(x, y, x + 3, y + 3, fill=color, outline="")
        for x, y, text, color, life in self.ice_floats:
            c.create_text(x, y, text=text, fill=color, font=font(16, True))

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
            tk.Button(self.dframe, text=f"{d}  {fmt_ram(CARDS[d]['ram'])}  x", bg=PANEL, fg=CYAN, bd=0, font=font(9), takefocus=0,
                      highlightthickness=1, highlightbackground=blend(CYAN, BG, 0.5), activebackground=LINE,
                      activeforeground=HI, cursor="hand2", command=lambda n=d: self.uninstall(n)).pack(side="left", padx=5)

    def card(self, name, n, handler, note="", dim=False, risky=False):
        c = CARDS[name]
        kind, col = KINDS[c["kind"]]
        tint = DIM if dim else col
        w, h = 140, 196
        cv = tk.Canvas(self.hframe, width=w, height=h, bg=BG, highlightthickness=0, cursor="arrow" if dim else "hand2")
        cv.pack(side="left", padx=4)

        def paint(mode=""):
            cv.delete("all")
            edge = {"hot": HI, "go": GREEN, "bad": RED}.get(mode) or (AMBER if risky else blend(tint, BG, 0.55))
            cv.create_polygon(cut_box(1, 1, w - 1, h - 1, 12), fill=PANEL2 if mode == "hot" else PANEL, outline=edge,
                              width=2 if mode or risky else 1)
            cv.create_rectangle(14, 2, w - 2, 6, fill=tint, outline="")
            cv.create_text(10, 19, text=kind, anchor="w", fill=tint, font=font(8, True))
            cv.create_text(w - 10, 19, text=f"[{n}]", anchor="e", fill=DIM, font=font(8))
            cv.create_text(10, 30, text=name, anchor="nw", width=124, fill=DIM if dim else HI, font=font(8 if len(name) > 14 else 9, True))
            cv.create_text(10, 54, text=fmt_ram(c["ram"]) if c["ram"] else "free", anchor="w",
                           fill=DIM if dim else AMBER, font=font(9, True))
            cv.create_rectangle(10, 64, 70, 67, fill=PANEL2, outline="")
            cv.create_rectangle(10, 64, 10 + 60 * min(1, c["ram"] / 4000), 67, fill=DIM if dim else AMBER, outline="")
            if c["req"]:
                cv.create_text(w - 10, 54, text=PRIV[c["req"]].lower() + "+", anchor="e", fill=DIM if dim else FG, font=font(8))
            glyph(cv, c["kind"], w // 2, 88, tint)
            cv.create_text(10, 106, text=c["text"], anchor="nw", width=122, fill=DIM if dim else FG, font=font(9))
            if note:
                cv.create_text(w // 2, h - 12, text="! " + note.lower(), fill=RED if dim else AMBER, font=font(8, True))

        self.card_painters[cv] = paint
        cv.bind("<Button-1>", lambda e: handler(cv))
        if not dim:
            cv.bind("<Enter>", lambda e: paint("hot"))
            cv.bind("<Leave>", lambda e: paint())
        paint()
        self.card_actions.append(lambda: handler(cv))

    def draw_hand(self):
        g = self.g
        for w in self.hframe.winfo_children():
            w.destroy()
        self.card_actions = []
        if g.state == "play":
            for i, name in enumerate(g.hand):
                why = g.locked(name)
                risky = why is None and g.used + CARDS[name]["ram"] > g.limit
                self.card(name, i + 1, lambda w, i=i: self.click_card(i, w),
                          why or ("kernel panic risk" if risky else ""), why is not None, risky)
        elif g.state == "reward" and g.rewards:
            label(self.hframe, "clean copy.\ntake one tool\nwith you:", CYAN, 11, True, justify="left").pack(side="left", padx=14)
            for name in g.rewards:
                self.card(name, len(self.card_actions) + 1,
                          lambda widget, n=name: self.pick(n) if widget.winfo_exists() else None)
        elif g.state == "extract":
            label(self.hframe, "compare the target with every file.\nname, signer AND size must all match.\n"
                  "anything else is malware.\nclick a row, or press its number.", CYAN, 11, justify="left").pack(padx=14, pady=50)

    def refresh_ui(self):
        g = self.g
        self.tierlbl.config(text=TIERS[g.tier]["name"].lower())
        self.endbtn.config(state="normal" if g.state == "play" else "disabled")
        if g.state == "extract" and not self.xp:
            self.root.update_idletasks()
            self.xp = canvas(self.mid, 10, 10)
            self.xp.place(x=self.logbox.winfo_x(), y=self.logbox.winfo_y(), width=self.logbox.winfo_width(),
                          height=self.logbox.winfo_height())
            self.xp.bind("<Motion>", lambda e: setattr(self, "hover", self.row_at(e.y)))
            self.xp.bind("<Leave>", lambda event: setattr(self, "hover", -1) if event.widget.winfo_exists() else None)
            self.xp.bind("<Button-1>", lambda e: self.extract_click(self.row_at(e.y)))
            self.hover = -1
            self.ext_total = int(self.cfg["timer"]) + g.take_time()
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
        w, h = c.winfo_width(), c.winfo_height()
        left = max(0, self.ext_end - time.monotonic())
        real = p["files"][p["answer"]]
        c.delete("all")
        panel(c, 1, 1, w - 1, h - 1, AMBER, PANEL, AMBER)
        c.create_text(14, 18, text="extraction  //  verify before you copy", anchor="w", fill=AMBER, font=font(11, True))
        tcol = RED if left < 5 else AMBER if left < 10 else GREEN
        c.create_text(w - 14, 18, text=f"{left:.1f}s", anchor="e", fill=tcol, font=font(11, True))
        c.create_text(14, 44, text="target", anchor="w", fill=DIM, font=font(9))
        c.create_text(64, 44, text=real["name"], anchor="w", fill=HI, font=font(10, True))
        c.create_text(310, 44, text=real["host"], anchor="w", fill=HI, font=font(10, True))
        c.create_text(460, 44, text=f"{real['size']} KB", anchor="w", fill=HI, font=font(10, True))
        c.create_rectangle(14, 58, w - 14, 66, outline=LINE, fill=BG)
        c.create_rectangle(15, 59, 15 + (w - 30) * left / self.ext_total, 65, outline="", fill=tcol)
        for x, name in ((64, "file"), (310, "signer"), (460, "size")):
            c.create_text(x, 86, text=name, anchor="w", fill=DIM, font=font(9))
        for i, f in enumerate(p["files"]):
            y = 100 + i * 18
            bad, ruled = i in p["bad"], i in p["ruled"]
            hot = i == self.hover and not bad and not ruled
            c.create_rectangle(8, y, w - 8, y + 16, fill=LINE if hot else PANEL2 if i % 2 else PANEL, outline="")
            col = RED if bad else DIM if ruled else HI if hot else FG
            c.create_text(14, y + 8, text=f"[{i + 1}]", anchor="w", fill=DIM, font=font(9))
            c.create_rectangle(44, y + 3, 52, y + 13, outline=col)
            c.create_text(64, y + 8, text=f["name"], anchor="w", fill=col, font=font(10))
            c.create_text(310, y + 8, text=f["host"], anchor="w", fill=col, font=font(10))
            c.create_text(460, y + 8, text=f"{f['size']} KB", anchor="w", fill=col, font=font(10))
            if ruled:
                c.create_line(60, y + 8, 540, y + 8, fill=DIM)
                c.create_text(w - 14, y + 8, text="RULED OUT", anchor="e", fill=GREEN, font=font(9, True))
            if bad:
                c.create_text(w - 14, y + 8, text="INFECTED", anchor="e", fill=RED, font=font(9, True))

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
        if self.mode != "game" or self.g is None:
            return
        g = self.g
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
        self.ice_floats = [[x, y - 1.2, t, c, life - 1] for x, y, t, c, life in self.ice_floats if life > 0]
        if self.hud_floats:
            self.hud_floats = [[x, y - 0.8, t, c, life - 1] for x, y, t, c, life in self.hud_floats if life > 0]
            moved = True
        if moved:
            self.draw_hud()
        if self.clock % 2 == 0 or self.parts or self.flash or self.ice_floats:
            self.draw_ice()
        pulse = (g.trace >= 70 or g.integrity < 30) and self.clock % 30 < 15
        if pulse != self.pulse:
            self.pulse = pulse
            self.draw_hud()
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
                self.spawn(10, ICE_COL)
                self.ice_floats.append([random.randint(105, 145), 90, f"-{e[1]}", HI, 28])
            elif e[0] == "breach":
                self.flash = 16
                self.spawn(40, FG)
            elif e[0] == "hurt":
                self.hurt = 10
                self.hud_floats.append([random.randint(250, 330), 42, f"-{e[1]}", RED, 26])
                if self.cfg["shake"]:
                    self.shake = max(self.shake, min(10, 2 + e[1] // 2))
            elif e[0] == "heal":
                self.hud_floats.append([random.randint(250, 330), 42, f"+{e[1]}", GREEN, 26])
            elif e[0] in ("panic", "infected", "late"):
                if self.cfg["shake"]:
                    self.shake = 14
                self.spawn(30, RED)
                self.banner.config(text={"panic": "KERNEL PANIC", "infected": "MALWARE EXECUTED", "late": "TIME OUT"}[e[0]], fg=RED)
                self.root.after(1500, lambda: gen == self.gen and self.banner.config(text=""))
            elif e[0] == "clean":
                self.spawn(30, GREEN)
                self.banner.config(text="CLEAN COPY", fg=GREEN)
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
        painter = self.card_painters.get(widget)
        if painter:
            painter("bad" if locked else "go")

        def go():
            self.g.play(i)
            self.busy = False
            self.after_action()

        self.later(180 if locked else 130, go)

    def end(self):
        if self.busy or self.mode != "game" or self.g.state != "play":
            return
        self.busy = True
        self.banner.config(text="ice is sweeping the network ...", fg=CYAN)

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
            for i in range(int(32 * n / steps)):
                bar.create_rectangle(i * 10, 0, i * 10 + 8, 10, fill=CYAN, outline="")
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
        gen = self.gen
        self.mode, self.busy = "over", False
        st["best"] = max(st["best"], g.tier + won)
        st["wins"] += won
        self.save()
        ov = tk.Frame(self.stage, bg=BG)
        ov.place(x=0, y=0, relwidth=1, relheight=1)
        bg = tk.Canvas(ov, width=1200, height=700, bg=BG, highlightthickness=0)
        bg.place(x=0, y=0)
        rain = Rain(bg, 1200, 700, 40, GREEN if won else RED, 0.82)
        self.loop(rain.step, 40)
        tone = GREEN if won else RED
        box = tk.Frame(ov, bg=PANEL, highlightthickness=1, highlightbackground=tone, padx=40, pady=30)
        box.place(relx=0.5, rely=0.45, anchor="center")
        title = label(box, "", tone, 24, True, justify="left", bg=PANEL)
        title.pack(anchor="w")
        body = label(box, "", FG, 12, justify="left", wraplength=640, bg=PANEL)
        body.pack(anchor="w", pady=14)
        row = tk.Frame(box, bg=PANEL)
        stats = (f"layers cleared: {g.tier + won}/5    turns: {g.turn}    cards played: {g.played}    "
                 f"panics: {g.panics}\ntrace: {g.trace}%    difficulty: {self.cfg['preset']}")
        head = "EXTRACTION COMPLETE" if won else "CONNECTION LOST"
        text = (("The Lantern publishes at dawn. Every name on the list will have a lawyer by morning.\n\n" if won
                 else g.reason + "\n\n") + stats)

        def show_buttons():
            row.pack(anchor="w")
            button(row, "reboot  [r]", self.begin_run, padx=14).pack(side="left", padx=(0, 10))
            button(row, "menu", self.show_title, fg=DIM, padx=14).pack(side="left")

        self.type(head, self.adder(title), lambda: self.type(text, self.adder(body), show_buttons, delay=14), delay=24)

    def on_key(self, e):
        if e.keysym in ("Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R", "Caps_Lock"):
            return
        if self.mode == "decks":
            if e.keysym == "Escape":
                self.leave_decks()
        elif self.mode == "pager":
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