import random
from cards import CARDS, TIERS, START, TARGETS, fmt_ram


def mutate(s):
    i = random.randrange(len(s) - 1)
    out = s[:i] + s[i + 1] + s[i] + s[i + 2:]
    return out if out != s else s + "x"


def make_puzzle(tier, scans=0):
    name, ext, host, size = TARGETS[tier]
    real = {"name": f"{name}.{ext}", "host": host, "size": size}
    tricks = [
        lambda: {"name": f"{name}.{ext}.exe", "host": host, "size": size},
        lambda: {"name": f"{mutate(name)}.{ext}", "host": host, "size": size},
        lambda: {"name": real["name"], "host": mutate(host), "size": size},
        lambda: {"name": real["name"], "host": host, "size": random.choice([size * 9, max(1, size // 9)])},
        lambda: {"name": f"{name}.{random.choice(['scr', 'bat', 'vbs'])}", "host": host, "size": size},
        lambda: {"name": real["name"], "host": "unsigned", "size": size},
    ]
    want = 3 + tier
    picks = random.sample(tricks, min(want, len(tricks)))
    picks += [random.choice(tricks) for _ in range(want - len(picks))]
    files = [real] + [t() for t in picks]
    random.shuffle(files)
    answer = files.index(real)
    wrong = [i for i in range(len(files)) if i != answer]
    random.shuffle(wrong)
    ruled = set(wrong[:min(scans, len(wrong) - 1)])
    return {"files": files, "answer": answer, "bad": set(), "ruled": ruled}


class Game:
    def __init__(self, cfg, deck=None):
        self.cfg = cfg
        self.integrity = 100
        self.base_ram = self.ram_cap = cfg["ram"] * 1000
        self.trace = 0
        self.priv = 0
        self.tier = 0
        self.turn = 1
        self.deck = list(deck or START)
        random.shuffle(self.deck)
        self.hand, self.discard, self.daemons = [], [], []
        self.spent = self.freed = self.shield = self.streak = 0
        self.stunned = self.scans = self.bonus_time = self.surge = 0
        self.played = self.panics = 0
        self.log, self.log_total, self.events = [], 0, []
        self.state, self.reason, self.rewards, self.puzzle = "play", "", [], None
        self.say("Rig online. Palanterror is watching.")
        self.load_tier()
        self.begin_turn()

    def say(self, msg, tag="sys"):
        self.log.append((msg, tag))
        self.log_total += 1
        self.log = self.log[-60:]

    def total(self, key):
        return sum(CARDS[d].get(key, 0) for d in self.daemons)

    @property
    def daemon_ram(self):
        return sum(CARDS[d]["ram"] for d in self.daemons)

    @property
    def limit(self):
        return self.ram_cap + self.surge + self.total("bonus_ram")

    @property
    def used(self):
        return max(0, self.daemon_ram + self.spent - self.freed)

    @property
    def flagged(self):
        return self.streak >= 3

    @property
    def sweep_gain(self):
        gain = 2 + self.tier
        if self.flagged:
            gain *= 3
        gain -= self.total("vpn")
        return max(1, round(gain * self.cfg["trace"] / 100))

    def settle(self):
        self.freed = max(0, min(self.freed, self.daemon_ram + self.spent))

    def load_tier(self):
        t = TIERS[self.tier]
        k = self.cfg["ice"] / 100
        self.ice_hp = self.ice_max = round(t["hp"] * k)
        self.ice_atk = max(1, round(t["atk"] * k))
        self.ram_cap = self.base_ram
        self.stunned = 0
        self.say("Entering " + t["name"])
        self.say(t["blurb"])

    def draw(self, n):
        for _ in range(n):
            if not self.deck:
                self.deck, self.discard = self.discard, []
                random.shuffle(self.deck)
            if not self.deck:
                return
            self.hand.append(self.deck.pop())

    def mend(self, n):
        healed = max(0, min(n, 100 - self.integrity))
        if healed:
            self.integrity += healed
            self.events.append(("heal", healed))
        return healed

    def begin_turn(self):
        self.spent = self.freed = self.surge = 0
        gain = self.total("shield")
        if gain:
            self.shield += gain
            self.say(f"Daemons generate {gain} shield.", "ok")
        mend = self.total("regen")
        healed = self.mend(mend)
        if healed:
            self.say(f"Daemons patch {healed} integrity.", "ok")
        self.draw(self.cfg["hand"] - len(self.hand) + self.total("extra_draw"))

    def locked(self, name):
        c = CARDS[name]
        if self.state != "play":
            return "OFFLINE"
        if self.priv < c["req"]:
            return "NEEDS CLEARANCE"
        if name == "AIR_GAP_BRIDGE" and self.tier != 3:
            return "TIER 3 ONLY"
        if name in self.daemons:
            return "ALREADY RUNNING"
        if c.get("hp_cost", 0) >= self.integrity:
            return "INTEGRITY TOO LOW"
        return None

    def play(self, i):
        if self.state != "play" or not 0 <= i < len(self.hand):
            return
        name = self.hand[i]
        c = CARDS[name]
        why = self.locked(name)
        if why:
            self.say(f"{name} refused: {why.lower()}.", "bad")
            return
        self.hand.pop(i)
        self.played += 1
        kind = c["kind"]
        if kind == "DAEMON":
            self.daemons.append(name)
        else:
            self.spent += c["ram"]
            self.discard.append(name)
        if kind in ("DAEMON", "OPT"):
            self.streak = 0
        self.say(f"> {name}", "cmd")
        if kind == "EXEC":
            if not c.get("quiet"):
                self.streak += 1
                if self.streak == 3:
                    self.say("Heuristics flagged your signature. Trace x3 until you mask traffic.", "bad")
            if self.tier == 2 and not self.daemons:
                self.say("Active sniffer caught unmasked traffic. +2% trace.", "bad")
                self.add_trace(2)
        if "dmg" in c:
            dmg = c["dmg"] + c.get("per_daemon", 0) * len(self.daemons)
            for _ in range(c.get("hits", 1)):
                if self.ice_hp > 0:
                    self.hit(dmg, c.get("pierce", False))
        if "leech" in c and self.mend(c["leech"]):
            self.say(f"Siphoned {c['leech']} integrity.", "ok")
        if "hp_cost" in c:
            self.integrity -= c["hp_cost"]
            self.events.append(("hurt", c["hp_cost"]))
            self.say(f"Backlash. -{c['hp_cost']} integrity.", "bad")
        if "trace" in c:
            self.add_trace(c["trace"])
        if "free" in c:
            got = min(c["free"], self.daemon_ram + self.spent - self.freed)
            self.freed += got
            if got:
                self.say(f"Freed {fmt_ram(got)}.", "ok")
            else:
                self.say("Nothing in use to free.")
        if "block" in c:
            self.shield += c["block"]
            self.say(f"Shield up: +{c['block']}.", "ok")
        if "wipe" in c:
            self.trace = max(0, self.trace - c["wipe"])
            self.say(f"Logs scrubbed: -{c['wipe']}% trace.", "ok")
        if "heal" in c:
            self.say(f"System restored: +{self.mend(c['heal'])} integrity.", "ok")
        if "surge" in c:
            self.surge += c["surge"]
            self.say(f"Overclocked: RAM limit +{fmt_ram(c['surge'])} this turn.", "ok")
        if "weaken" in c:
            self.ice_atk = max(1, self.ice_atk - c["weaken"])
            self.say(f"ICE strike weakened to {self.ice_atk}.", "ok")
        if "stun" in c:
            self.stunned += c["stun"]
            self.say("ICE is tied up. Its next strike will miss.", "ok")
        if "scan" in c:
            self.scans += c["scan"]
            self.say("Checksum tool loaded for the next extraction.", "ok")
        if "time" in c:
            self.bonus_time += c["time"]
            self.say(f"+{c['time']}s banked for the next extraction.", "ok")
        if "draw" in c:
            self.draw(c["draw"])
        if c.get("cycle"):
            old, self.hand = self.hand, []
            self.draw(len(old))
            self.discard += old
            self.say("Hand swapped.", "ok")
        if c.get("reset"):
            self.streak = 0
            self.say("Signature scrambled.", "ok")
        if "grant" in c and self.priv < c["grant"]:
            self.priv = c["grant"]
            self.say("Clearance escalated.", "ok")
        if "lock" in c:
            self.ram_cap = min(self.ram_cap, c["lock"])
            self.say(f"Hardware strain: RAM locked to {fmt_ram(c['lock'])}.", "bad")
        if self.state != "play":
            return
        if self.integrity <= 0:
            self.lose("Integrity hit 0%. Your rig is fried.")
            return
        if self.used > self.limit:
            self.panic()
        if self.state == "play":
            self.check_clear()

    def hit(self, dmg, pierce=False):
        if not pierce and self.priv < TIERS[self.tier]["min"]:
            dmg = max(1, dmg // 2)
            self.say("Clearance too low. Damage halved.", "bad")
        self.ice_hp = max(0, self.ice_hp - dmg)
        self.say(f"ICE takes {dmg} damage.", "ok")
        self.events.append(("ice_hit", dmg))

    def add_trace(self, n):
        self.trace = min(100, self.trace + n)
        if self.trace >= 100 and self.state in ("play", "reward", "extract"):
            self.lose("Trace hit 100%. Global subnet blackout.")

    def panic(self):
        self.say("KERNEL PANIC. Daemons wiped, -10 integrity, trace spike.", "bad")
        self.panics += 1
        self.integrity -= 10
        self.events += [("panic",), ("hurt", 10)]
        self.daemons = []
        self.settle()
        self.add_trace(8)
        if self.integrity <= 0:
            self.lose("Integrity hit 0%. Your rig is fried.")
        elif self.state == "play" and self.ice_hp > 0:
            self.end_turn()

    def end_turn(self):
        if self.state != "play":
            return
        self.discard += self.hand
        self.hand = []
        burn = self.total("burn")
        if burn:
            self.say(f"Daemons chew through the ICE for {burn}.", "ok")
            self.hit(burn)
            if self.ice_hp <= 0:
                self.check_clear()
                return
        if self.stunned:
            self.stunned -= 1
            self.say("ICE is stunned. No strike this turn.", "ok")
        else:
            atk = max(0, self.ice_atk + random.randint(-1, 2) - self.total("dull"))
            blocked = min(self.shield, atk)
            dmg = atk - blocked
            if dmg:
                self.integrity -= dmg
                self.events.append(("hurt", dmg))
            self.say(f"ICE strikes for {atk}. {blocked} blocked, {dmg} through.", "bad" if dmg else "ok")
        self.shield = 0
        gain = self.sweep_gain
        self.say(f"Security sweep. +{gain}% trace.", "bad")
        self.add_trace(gain)
        if self.state != "play":
            return
        if self.integrity <= 0:
            self.lose("Integrity hit 0%. Your rig is fried.")
            return
        self.turn += 1
        self.begin_turn()

    def check_clear(self):
        if self.ice_hp > 0:
            return
        self.events.append(("breach",))
        if self.cfg["extract"]:
            self.state = "extract"
            self.puzzle = make_puzzle(self.tier, self.scans)
            self.scans = 0
            self.say("Layer breached. Find the real file. Name, signer and size must all match.", "ok")
            if self.puzzle["ruled"]:
                self.say(f"Checksum tool ruled out {len(self.puzzle['ruled'])} files.", "ok")
        else:
            self.layer_done()

    def layer_done(self):
        if self.tier == 4:
            self.state = "won"
            self.say("The payload is away. You are out.", "ok")
            return
        self.state = "reward"
        pool = [n for n in CARDS if n != "AIR_GAP_BRIDGE" or self.tier + 1 == 3]
        self.rewards = random.sample(pool, 3)
        self.say("Pick a tool to take with you.", "ok")

    def take_time(self):
        extra, self.bonus_time = self.bonus_time, 0
        return extra

    def extract_pick(self, i):
        if self.state != "extract" or self.puzzle is None:
            return
        p = self.puzzle
        if i in p["bad"] or i in p["ruled"] or not 0 <= i < len(p["files"]):
            return
        if i == p["answer"]:
            self.say("Name, signer and size all check out. Clean copy.", "ok")
            self.events.append(("clean",))
            self.layer_done()
            return
        p["bad"].add(i)
        self.integrity -= 12
        self.events += [("infected",), ("hurt", 12)]
        lost = None
        pool = [(src, n) for src in (self.deck, self.discard, self.hand) for n in range(len(src))]
        if len(pool) > 8:
            src, n = random.choice(pool)
            lost = src.pop(n)
        self.say("MALWARE. -12 integrity, +8% trace." + (f" {lost} was corrupted." if lost else ""), "bad")
        self.add_trace(8)
        if self.state == "extract" and self.integrity <= 0:
            self.lose("Malware fried your rig.")

    def extract_timeout(self):
        if self.state != "extract":
            return
        self.integrity -= 15
        self.events += [("late",), ("hurt", 15)]
        self.say("Out of time. The sweep caught you: -15 integrity, +10% trace.", "bad")
        self.add_trace(10)
        if self.state != "extract":
            return
        if self.integrity <= 0:
            self.lose("Integrity hit 0% while the sweep closed in.")
        elif self.tier == 4:
            self.lose("The payload never reached the dropbox.")
        else:
            self.rewards = []
            self.state = "reward"

    def advance(self, name=None):
        if self.state != "reward":
            return
        if name:
            self.discard.append(name)
        self.tier += 1
        self.integrity = min(100, self.integrity + 10)
        self.trace = max(0, self.trace - 5)
        self.deck += self.hand + self.discard
        self.hand, self.discard = [], []
        random.shuffle(self.deck)
        self.shield = self.streak = 0
        self.state = "play"
        self.load_tier()
        self.begin_turn()

    def uninstall(self, name):
        if self.state == "play" and name in self.daemons:
            self.daemons.remove(name)
            if self.used > self.limit:
                self.daemons.append(name)
                self.say(f"Can't uninstall {name}: the rig would overflow.", "bad")
                return
            self.discard.append(name)
            self.settle()
            self.say(f"{name} uninstalled.")

    def lose(self, reason):
        self.state = "lost"
        self.reason = reason
        self.say(reason, "bad")