import random
from cards import CARDS, TIERS, START


class Game:
    def __init__(self):
        self.integrity = 100
        self.base_ram = 8
        self.ram_cap = 8
        self.trace = 0
        self.priv = 0
        self.tier = 0
        self.turn = 1
        self.deck = list(START)
        random.shuffle(self.deck)
        self.hand = []
        self.discard = []
        self.daemons = []
        self.spent = 0
        self.freed = 0
        self.shield = 0
        self.streak = 0
        self.log = []
        self.log_total = 0
        self.events = []
        self.state = "play"
        self.reason = ""
        self.rewards = []
        self.say("Rig online. Palanterror is watching.", "sys")
        self.load_tier()
        self.begin_turn()

    def say(self, msg, tag="sys"):
        self.log.append((msg, tag))
        self.log_total += 1
        self.log = self.log[-60:]

    @property
    def daemon_ram(self):
        return sum(CARDS[d]["ram"] for d in self.daemons)

    @property
    def used(self):
        return max(0, self.daemon_ram + self.spent - self.freed)

    @property
    def flagged(self):
        return self.streak >= 3

    def load_tier(self):
        t = TIERS[self.tier]
        self.ice_hp = self.ice_max = t["hp"]
        self.ice_atk = t["atk"]
        self.ram_cap = self.base_ram
        self.say("Entering " + t["name"], "sys")
        self.say(t["blurb"], "sys")

    def draw(self, n):
        for _ in range(n):
            if not self.deck:
                self.deck, self.discard = self.discard, []
                random.shuffle(self.deck)
            if not self.deck:
                return
            self.hand.append(self.deck.pop())

    def begin_turn(self):
        self.spent = 0
        self.freed = 0
        gain = sum(CARDS[d].get("shield", 0) for d in self.daemons)
        if gain:
            self.shield += gain
            self.say(f"Daemons generate {gain} shield.", "ok")
        self.draw(5 - len(self.hand))

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
        kind = c["kind"]
        if kind == "DAEMON":
            self.daemons.append(name)
            self.streak = 0
        else:
            self.spent += c["ram"]
            self.discard.append(name)
        if kind == "OPT":
            self.streak = 0
        self.say(f"> {name}", "cmd")
        if kind == "EXEC":
            self.streak += 1
            if self.streak == 3:
                self.say("Heuristics flagged your signature. Trace x3 until you mask traffic.", "bad")
        if "dmg" in c:
            self.hit(c["dmg"])
        if "trace" in c:
            self.add_trace(c["trace"])
        if "free" in c:
            self.freed += c["free"]
            self.say(f"Freed {c['free']} GB.", "ok")
        if "draw" in c:
            self.draw(c["draw"])
        if c.get("reset"):
            self.streak = 0
            self.say("Signature scrambled.", "ok")
        if "grant" in c and self.priv < c["grant"]:
            self.priv = c["grant"]
            self.say("Clearance escalated.", "ok")
        if "lock" in c:
            self.ram_cap = min(self.ram_cap, c["lock"])
            self.say(f"Hardware strain: RAM locked to {c['lock']} GB this layer.", "bad")
        if self.state != "play":
            return
        if self.used > self.ram_cap:
            self.panic()
        if self.state == "play":
            self.check_clear()

    def hit(self, dmg):
        if self.priv < TIERS[self.tier]["min"]:
            dmg //= 2
            self.say("Clearance too low. Damage halved.", "bad")
        self.ice_hp = max(0, self.ice_hp - dmg)
        self.say(f"ICE takes {dmg} damage.", "ok")
        self.events.append(("ice_hit", dmg))

    def add_trace(self, n):
        if self.flagged:
            n *= 3
        self.trace = min(100, self.trace + n)
        if self.trace >= 100 and self.state in ("play", "reward"):
            self.lose("TRACE 100%. Global subnet blackout.")
        return n

    def panic(self):
        self.say("KERNEL PANIC. Daemons wiped, -10 integrity, trace spike.", "bad")
        self.integrity -= 10
        self.events.append(("panic",))
        self.events.append(("hurt", 10))
        self.daemons = []
        self.add_trace(8)
        if self.integrity <= 0:
            self.lose("Integrity 0%. Your rig is fried.")
        if self.state == "play":
            self.end_turn()

    def end_turn(self):
        if self.state != "play":
            return
        self.discard += self.hand
        self.hand = []
        atk = self.ice_atk + random.randint(-1, 2)
        dmg = max(0, atk - self.shield)
        if dmg:
            self.integrity -= dmg
            self.events.append(("hurt", dmg))
        self.say(f"ICE strikes for {atk}. {self.shield} blocked, {dmg} through.", "bad" if dmg else "ok")
        self.shield = 0
        gain = max(1, 2 + self.tier - sum(CARDS[d].get("vpn", 0) for d in self.daemons))
        gain = self.add_trace(gain)
        self.say(f"Security sweep. +{gain}% trace.", "bad")
        if self.state != "play":
            return
        if self.integrity <= 0:
            self.lose("Integrity 0%. Your rig is fried.")
            return
        self.turn += 1
        self.begin_turn()

    def check_clear(self):
        if self.ice_hp > 0:
            return
        self.events.append(("breach",))
        if self.tier == 4:
            self.state = "won"
            self.say("EXODUS_PAYLOAD secured. You are out.", "ok")
            return
        self.state = "reward"
        self.rewards = random.sample(list(CARDS), 3)
        next_clearance = TIERS[self.tier + 1]["min"]
        if self.priv < next_clearance:
            upgrades = [name for name, card in CARDS.items()
                        if card.get("grant", 0) >= next_clearance and card["req"] <= self.priv]
            if upgrades:
                upgrade = random.choice(upgrades)
                if upgrade not in self.rewards:
                    self.rewards[-1] = upgrade
        self.say("Layer breached. Pick a tool to take with you.", "ok")

    def pick_reward(self, name):
        if self.state != "reward" or name not in self.rewards:
            return
        self.discard.append(name)
        self.tier += 1
        self.integrity = min(100, self.integrity + 10)
        self.trace = max(0, self.trace - 5)
        self.deck += self.hand + self.discard
        self.hand = []
        self.discard = []
        random.shuffle(self.deck)
        self.shield = 0
        self.streak = 0
        self.state = "play"
        self.load_tier()
        self.begin_turn()

    def uninstall(self, name):
        if self.state == "play" and name in self.daemons:
            self.daemons.remove(name)
            self.discard.append(name)
            self.say(f"{name} uninstalled.", "sys")

    def lose(self, reason):
        self.state = "lost"
        self.reason = reason
        self.say(reason, "bad")