import random
import tkinter as tk
from engine import Game
from cards import CARDS, PRIV, TIERS

BG, PANEL, LINE = "#0d110e", "#141a15", "#2b382d"
DIM, FG, HI = "#6b8468", "#bcd7b4", "#eaf6e4"
AMBER, RED, TEAL = "#e2a83e", "#dc5f4f", "#62b5b0"
KINDS = {"EXEC": ("executable", RED), "DAEMON": ("daemon", TEAL), "OPT": ("optimizer", FG), "EXPLOIT": ("exploit", AMBER)}

ART = [
    " .----------.\n | [o]  [o] |\n | ======== |\n '----------'",
    " |^|      |^|\n | |______| |\n | |      | |\n |_|      |_|",
    "   .-~~~~~-.\n  ( ( (@) ) )\n   '-~~~~~-'",
    " .----------.\n |  (    )  |\n |   \\_|_/   |\n '----------'",
    "    /\\_/\\\n   ( X.X )\n    > ^ <\n   /|   |\\",
]

INTRO = [
    "PALANTERROR PREDICTIVE POLICING NETWORK\nrestricted access - authorised staff only\n\n"
    "> opening uplink ............ ok\n> routing through 4 proxies . ok\n"
    "> rig fingerprint ........... scrubbed\n> session ................... GUEST\n\nsomebody is going to notice.",

    "THE JOB\n\nPalanterror watches every phone, camera and bus pass in the city and predicts\n"
    "who will commit a crime before they do. People have already been arrested\nfor things they hadn't done yet.\n\n"
    "Deep in the air-gapped vault sits the EXODUS_PAYLOAD: the list of who it\nflagged, and why. Your client wants it. You want to get paid.\n\n"
    "Five layers stand in the way. Get in, get it, get out.",

    "HOW THE RIG WORKS\n\n"
    "RAM        8 GB a turn. Daemons stay installed and keep eating RAM\n           until you uninstall them (click the chip under the log).\n"
    "PANIC      go over your RAM and the rig crashes: -10 integrity, trace\n           spike, daemons wiped, turn over.\n"
    "TRACE      climbs every turn. At 100% you are locked out.\n"
    "SIGNATURE  three executables in a row and trace gain triples. Daemons\n           and optimizers reset it.\n"
    "CLEARANCE  guest > user > operator > root. Some cards and layers need more.\n\n"
    "keys: 1-9 play a card, space ends your turn",
]


def font(size=10, bold=False):
    return ("Consolas", size, "bold" if bold else "normal")


def label(parent, text="", fg=FG, size=10, bold=False, **kw):
    return tk.Label(parent, text=text, fg=fg, bg=kw.pop("bg", BG), font=font(size, bold), **kw)


def canvas(parent, w, h):
    return tk.Canvas(parent, width=w, height=h, bg=PANEL, highlightthickness=1, highlightbackground=LINE)


class App:
    def __init__(self, root):
        self.root = root
        root.title("Palanterror")
        root.configure(bg=BG)
        root.geometry("1200x700")
        root.resizable(False, False)
        self.stage = tk.Frame(root, bg=BG)
        self.stage.place(x=0, y=0, relwidth=1, relheight=1)
        self._game: Game | None = None
        self.gen, self.mode, self.busy, self.ticking = 0, "intro", False, False
        self.shake = self.hurt = self.flash = 0
        self.card_actions = []
        self.logged, self.logq, self.log_busy = 0, [], False
        root.bind("<Key>", self.on_key)
        root.bind("<Button-1>", lambda _: self.mode == "intro" and self.advance())
        self.start_intro()

    @property
    def g(self) -> Game:
        if self._game is None:
            raise RuntimeError("Game has not started")
        return self._game

    @g.setter
    def g(self, game: Game) -> None:
        self._game = game

    def clear(self):
        for w in self.stage.winfo_children():
            w.destroy()

    def type(self, text, put, done=None, delay=12, skippable=False):
        gen = self.gen
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
            self.root.after(wait, lambda: step(end))

        step()

    def start_intro(self):
        self.mode, self.page = "intro", 0
        self.clear()
        self.box = tk.Text(self.stage, bg=BG, fg=FG, font=font(13), bd=0, highlightthickness=0, wrap="word",
                                                      padx=110, pady=100, cursor="arrow", spacing1=5, state="disabled")
        self.box.pack(fill="both", expand=True)
        self.hint = label(self.stage)
        self.hint.place(relx=0.5, rely=0.94, anchor="center")
        self.show_page()

    def put_intro(self, s):
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
        self.type(INTRO[self.page], self.put_intro, self.page_done, skippable=True)

    def page_done(self):
        self.typing = False
        self.blink(True)

    def blink(self, on):
        gen = self.gen
        word = "press any key to begin" if self.page == len(INTRO) - 1 else "press any key"
        self.hint.config(text=f"[ {word} ]" if on else "")
        self.root.after(550, lambda: gen == self.gen and self.blink(not on))

    def advance(self):
        if self.typing:
            self.skip = True
        elif self.page < len(INTRO) - 1:
            self.page += 1
            self.show_page()
        else:
            self.begin_run()

    def begin_run(self):
        self.gen += 1
        self.g = Game()
        self.shown = {"integrity": 100.0, "trace": 0.0, "ice": float(self.g.ice_hp)}
        self.logged, self.logq, self.log_busy = 0, [], False
        self.shake = self.hurt = self.flash = 0
        self.busy, self.mode = False, "game"
        self.build_game()
        self.refresh_ui()
        self.queue_log()
        self.transition("uplink established", lambda: None)
        if not self.ticking:
            self.ticking = True
            self.tick()

    def build_game(self):
        self.clear()
        self.stage.place(x=0, y=0, relwidth=1, relheight=1)
        head = tk.Frame(self.stage, bg=BG)
        head.pack(fill="x", padx=16, pady=(12, 4))
        label(head, "PALANTERROR", HI, 16, True).pack(side="left")
        self.banner = label(head, "", AMBER, 11, True)
        self.banner.pack(side="left", padx=24)
        self.tierlbl = label(head, "", AMBER, 11)
        self.tierlbl.pack(side="right")
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
        self.dframe = tk.Frame(self.stage, bg=BG)
        self.dframe.pack(fill="x", padx=16, pady=(8, 4))
        bottom = tk.Frame(self.stage, bg=BG)
        bottom.pack(fill="x", padx=16, pady=4)
        self.hframe = tk.Frame(bottom, bg=BG)
        self.hframe.pack(side="left")
        self.endbtn = tk.Button(bottom, text="end turn\n[space]", command=self.end, bg=PANEL, fg=AMBER, bd=0,
                                        activebackground=AMBER, activeforeground=BG, font=font(11, True), width=10, height=4,
                                highlightthickness=1, highlightbackground=AMBER, cursor="hand2")
        self.endbtn.pack(side="right", anchor="s")

    def meter(self, x, y, w, name, frac, text, color):
        self.hud.create_text(x, y, text=name, anchor="w", fill=DIM, font=font(9))
        self.hud.create_text(x + w, y, text=text, anchor="e", fill=color, font=font(9, True))
        self.hud.create_rectangle(x, y + 9, x + w, y + 21, outline=LINE, fill=BG)
        if frac > 0:
            self.hud.create_rectangle(x + 1, y + 10, x + 1 + (w - 2) * min(1, frac), y + 20, outline="", fill=color)

    def draw_hud(self):
        c = self.hud
        g = self.g
        c.delete("all")
        hp, tr = self.shown["integrity"], self.shown["trace"]
        self.meter(16, 14, 350, "integrity", hp / 100, f"{max(0, round(hp))}%",
                                      RED if self.hurt or hp < 25 else AMBER if hp < 50 else FG)
        self.meter(400, 14, 350, "trace", tr / 100, f"{round(tr)}%", RED if tr >= 80 else AMBER if tr >= 50 else FG)
        over = g.used > g.ram_cap
        c.create_text(784, 14, text="ram", anchor="w", fill=DIM, font=font(9))
        c.create_text(1144, 14, text=f"{g.used}/{g.ram_cap} GB" + ("  over limit" if over else ""), anchor="e",
                                            fill=RED if over else AMBER, font=font(9, True))
        slot = (360 - 21) / 8
        for i in range(g.base_ram):
            x = 784 + i * (slot + 3)
            if i >= g.ram_cap:
                c.create_rectangle(x, 23, x + slot, 35, outline=RED, fill=BG)
                c.create_line(x, 23, x + slot, 35, fill=RED)
                continue
            fill = TEAL if i < g.used else BG
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

    def draw_ice(self):
        c = self.ice
        g = self.g
        c.delete("all")
        t = TIERS[g.tier]
        down = g.ice_hp <= 0
        col = DIM if down else RED if self.flash % 4 >= 2 else FG
        ox = random.randint(-5, 5) if self.flash else 0
        c.create_text(16, 16, text=t["name"].lower(), anchor="w", fill=AMBER, font=font(10, True))
        for i in range(5):
            c.create_rectangle(424 + i * 16, 10, 434 + i * 16, 20, outline=AMBER, fill=AMBER if i <= g.tier else PANEL)
        c.create_text(30 + ox, 70, text=ART[g.tier], anchor="nw", fill=col, font=font(14), justify="left")
        c.create_text(250, 58, text=t["ice"].lower(), anchor="w", fill=DIM if down else HI, font=font(12, True))
        hp = max(0, self.shown["ice"])
        c.create_text(250, 92, text="integrity", anchor="w", fill=DIM, font=font(9))
        c.create_text(500, 92, text=f"{round(hp)}/{g.ice_max}", anchor="e", fill=RED, font=font(9, True))
        c.create_rectangle(250, 102, 500, 114, outline=LINE, fill=BG)
        if hp > 0:
            c.create_rectangle(251, 103, 251 + 248 * hp / g.ice_max, 113, outline="", fill=RED)
        ok = g.priv >= t["min"]
        c.create_text(250, 140, text=f"strike  ~{g.ice_atk}", anchor="w", fill=FG, font=font(10))
        c.create_text(250, 162, text=f"needs   {PRIV[t['min']].lower()}" + ("" if ok else "  (damage halved)"),
                              anchor="w", fill=FG if ok else RED, font=font(10))
        c.create_text(250, 196, text=t["blurb"], anchor="nw", width=250, fill=DIM, font=font(9))

    def draw_daemons(self):
        for w in self.dframe.winfo_children():
            w.destroy()
        label(self.dframe, "daemons:", DIM, 9).pack(side="left")
        if not self.g.daemons:
            label(self.dframe, "none running", DIM, 9).pack(side="left", padx=8)
        for d in self.g.daemons:
            tk.Button(self.dframe, text=f"{d}  {CARDS[d]['ram']} GB  x", bg=PANEL, fg=TEAL, bd=0, font=font(9),
                                            highlightthickness=1, highlightbackground=LINE, activebackground=LINE, cursor="hand2",
                      command=lambda n=d: self.uninstall(n)).pack(side="left", padx=5)

    def card(self, name, n, handler, note="", dim=False, risky=False):
        c = CARDS[name]
        kind, col = KINDS[c["kind"]]
        edge = AMBER if risky else LINE
        f = tk.Frame(self.hframe, bg=PANEL, width=136, height=190, highlightthickness=1, highlightbackground=edge)
        f.pack_propagate(False)
        f.pack(side="left", padx=4)
        kids: list[tk.Widget] = [f, tk.Frame(f, bg=DIM if dim else col, height=4)]
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
            w.config({"cursor": "arrow" if dim else "hand2"})
            w.bind("<Button-1>", lambda _: handler(f))
            if not dim:
                w.bind("<Enter>", lambda _: f.config(highlightbackground=HI))
                w.bind("<Leave>", lambda _: f.config(highlightbackground=edge))
        self.card_actions.append(lambda: handler(f))

    def draw_hand(self):
        g = self.g
        for w in self.hframe.winfo_children():
            w.destroy()
        self.card_actions = []
        if g.state == "play":
            for i, name in enumerate(g.hand):
                why = g.locked(name)
                card = CARDS[name]
                projected = max(0, g.used + card["ram"] - card.get("free", 0))
                cap = min(g.ram_cap, card.get("lock", g.ram_cap))
                risky = why is None and projected > cap
                self.card(name, i + 1, lambda w, i=i: self.click_card(i, w),
                          why or ("kernel panic risk" if risky else ""), why is not None, risky)
        elif g.state == "reward":
            label(self.hframe, "layer breached.\ntake one tool\nwith you:", AMBER, 11, True, justify="left").pack(side="left", padx=14)
            for i, name in enumerate(g.rewards):
                self.card(name, i + 1, lambda _, n=name: self.pick(n))

    def refresh_ui(self):
        self.tierlbl.config(text=TIERS[self.g.tier]["name"].lower())
        self.endbtn.config(state="normal" if self.g.state == "play" else "disabled")
        self.draw_hud()
        self.draw_ice()
        self.draw_daemons()
        self.draw_hand()

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
        g = self.g
        moved = False
        for key, target in (("integrity", g.integrity), ("trace", g.trace), ("ice", g.ice_hp)):
            d = target - self.shown[key]
            if d:
                step = max(0.8, abs(d) * 0.15)
                self.shown[key] = target if abs(d) <= step else self.shown[key] + step * (1 if d > 0 else -1)
                moved = True
        if self.hurt or self.flash:
            self.hurt, self.flash, moved = max(0, self.hurt - 1), max(0, self.flash - 1), True
        if moved:
            self.draw_hud()
            self.draw_ice()
        if self.shake:
            s, self.shake = self.shake, self.shake - 1
            dx, dy = (random.randint(-s, s), random.randint(-s, s)) if self.shake else (0, 0)
            self.stage.place(x=dx, y=dy, relwidth=1, relheight=1)
        self.root.after(33, self.tick)

    def after_action(self):
        g = self.g
        events, g.events = g.events, []
        for e in events:
            if e[0] == "ice_hit":
                self.flash = 8
            elif e[0] == "breach":
                self.flash = 16
            elif e[0] == "hurt":
                self.hurt = 10
                self.shake = max(self.shake, min(10, 2 + e[1] // 2))
            elif e[0] == "panic":
                self.shake = 14
                self.banner.config(text="KERNEL PANIC", fg=RED)
                generation = self.gen
                self.root.after(1500, lambda: generation == self.gen and self.banner.config(text=""))
        self.queue_log()
        self.refresh_ui()
        if g.state in ("won", "lost"):
            self.busy = True
            self.root.after(1400, self.finish)

    def later(self, ms, fn):
        generation = self.gen
        self.root.after(ms, lambda: generation == self.gen and fn())

    def click_card(self, i, widget):
        if self.busy or self.mode != "game" or self.g.state != "play" or i >= len(self.g.hand):
            return
        locked = self.g.locked(self.g.hand[i]) is not None
        self.busy = True
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
            self.g.pick_reward(name)
            self.shown["ice"] = 0.0
            self.after_action()

        self.transition("breaching " + TIERS[self.g.tier + 1]["name"].lower(), go)

    def transition(self, text, done, steps=28):
        generation = self.gen
        self.busy = True
        ov = tk.Frame(self.stage, bg=BG)
        ov.place(x=0, y=0, relwidth=1, relheight=1)
        lbl = label(ov, text, HI, 16, True)
        lbl.place(relx=0.5, rely=0.44, anchor="center")
        bar = tk.Canvas(ov, width=320, height=10, bg=BG, highlightthickness=1, highlightbackground=LINE)
        bar.place(relx=0.5, rely=0.52, anchor="center")

        def step(n=0):
            if generation != self.gen:
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
        g = self.g
        self.mode = "over"
        won = g.state == "won"
        ov = tk.Frame(self.stage, bg=BG)
        ov.place(x=0, y=0, relwidth=1, relheight=1)
        box = tk.Frame(ov, bg=BG)
        box.place(relx=0.5, rely=0.45, anchor="center")
        title = label(box, "", FG if won else RED, 24, True, justify="left")
        title.pack(anchor="w")
        body = label(box, "", FG, 12, justify="left", wraplength=640)
        body.pack(anchor="w", pady=14)
        btn = tk.Button(box, text="reboot  [r]", command=self.begin_run, bg=PANEL, fg=AMBER, bd=0, font=font(12, True),
                                                highlightthickness=1, highlightbackground=AMBER, activebackground=AMBER, cursor="hand2", padx=14, pady=4)
        stats = f"layers cleared: {g.tier + won}/5    turns: {g.turn}    trace: {g.trace}%"
        head = "EXTRACTION COMPLETE" if won else "CONNECTION LOST"
        text = ("The EXODUS_PAYLOAD is on your drive and the tunnel is closing behind you.\n"
                                "By morning, every name on that list will have a lawyer.\n\n" if won else g.reason + "\n\n") + stats
        add = lambda lab: (lambda s: lab.config(text=lab.cget("text") + s))
        self.type(head, add(title), lambda: self.type(text, add(body), lambda: btn.pack(anchor="w"), delay=14), delay=24)

    def on_key(self, e):
        if e.keysym in ("Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R", "Caps_Lock"):
            return
        if self.mode == "intro":
            self.advance()
        elif self.busy:
            return
        elif self.mode == "over":
            if e.char.lower() == "r":
                self.begin_run()
        elif e.char.isdigit() and e.char != "0":
            if int(e.char) - 1 < len(self.card_actions):
                self.card_actions[int(e.char) - 1]()
        elif e.char == " ":
            self.end()

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
