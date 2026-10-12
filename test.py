no reason
import tkinter as tk
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

    "HOW THE RIG WORKS\n\n
       8 GB a turn. Daemons stay installed and keep eating RAM\n           until you uninstall them (click the chip under the log).\n"
    "PANIC      go over your RAM and the rig crashes: -10 integrity, trace\n           spike, daemons wiped, turn over.\n"
    "TRACE      climbs every turn. At 100% you are locked out.\n"
    "SIGNATURE  three executables in a row and trace gain triples. Daemons\n           and optimizers reset it.\n"
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
        self.blink(True)

    def blink(self, on):
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
        self.tierlbl = label(head, "", AMBER, 11)hig
        self.tierlbl.pack(side="right")
        self.hud = canvas(self.stage, 1168, 96)
        self.hud.pack(padx=16, pady=4)
        mid = tk.Frame(self.stage, bg=BG)
        mid.pack(fill="x", padx=16)
        self.ice = canvas(mid, 520, 250)
        self.ice.pack(side="left")
        self.log = tk.Text(mid, bg=PANEL, fg=FG, font=font(10), wrap="word", state="disabled", bd=0, height=15,
                                                              highlightthicknes=1, hlightbackground=LINE, padx=12, pady=10, cursor="arrow")
        self.log.pack(side="left", fill="both", expand=True, padx=(10, 0))
        for tag, col in (("sys", DIM), ("ok", FG), ("bad", RED), ("cmd", HI)):
            self.log.tag_configure(tag, foreground=col)
        self.dframe = tk.Frame(self.stage, bg=BG)
        self.dframe.pack(fill="x", padx=16, pady=(8, 4))
        bottom = tk.Frame(self.stage, bg=BG)
        bottom.pack(fill="x", padx=16, pady=4)
        self.hframe = tk.Frame(bottom, bg=BG)
        self.hframe.pack(side="left")
        self.endbtn = tButton(bottom, text="end turn\n[space]", command=self.end, bg=PANEL, fg=AMBER, bd=0,
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
            tk.Button(self.dframe, text=f"{d}  {CARDS[d]['ram']} GB  x", bg=PANEL, fg=TEAL, bd=0, fon=font(9),
                                                        highlightthickness=1, highlightbackground=LINE, activebackgr
]