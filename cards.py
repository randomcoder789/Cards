PRIV = ["GUEST", "USER", "OPERATOR", "ROOT"]
KIND_ORDER = ["EXEC", "DAEMON", "OPT", "EXPLOIT"]
DECK_MIN, DECK_MAX = 10, 24

CARDS = {
    "PING": {"kind": "EXEC", "ram": 500, "req": 0, "dmg": 5, "quiet": True, "text": "Deal 5 damage. Quiet traffic, never flagged."},
    "NOP_SLED": {"kind": "EXEC", "ram": 250, "req": 0, "dmg": 2, "draw": 1, "quiet": True, "text": "Deal 2 damage. Draw 1 card. Never flagged."},
    "ARP_SPOOF": {"kind": "EXEC", "ram": 500, "req": 0, "dmg": 4, "quiet": True, "text": "Deal 4 damage. Never flagged."},
    "PORT_SCAN": {"kind": "EXEC", "ram": 500, "req": 0, "dmg": 4, "draw": 1, "text": "Deal 4 damage. Draw 1 card."},
    "XSS_PAYLOAD": {"kind": "EXEC", "ram": 750, "req": 0, "dmg": 7, "trace": 1, "text": "Deal 7 damage. +1% trace."},
    "SYN_FLOOD": {"kind": "EXEC", "ram": 750, "req": 0, "dmg": 3, "hits": 3, "trace": 1, "text": "Deal 3 damage three times. +1% trace."},
    "DDOS": {"kind": "EXEC", "ram": 1000, "req": 0, "stun": 1, "trace": 3, "text": "ICE skips its next strike. +3% trace."},
    "DICTIONARY_ATTACK": {"kind": "EXEC", "ram": 1000, "req": 0, "dmg": 5, "hits": 2, "trace": 1, "text": "Deal 5 damage twice. +1% trace."},
    "SQL_INJECTION": {"kind": "EXEC", "ram": 1500, "req": 0, "dmg": 12, "text": "Deal 12 damage."},
    "FORK_BOMB": {"kind": "EXEC", "ram": 1500, "req": 0, "dmg": 5, "hits": 3, "trace": 2, "text": "Deal 5 damage three times. +2% trace."},
    "RACE_CONDITION": {"kind": "EXEC", "ram": 1500, "req": 0, "dmg": 6, "per_daemon": 4, "text": "Deal 6 damage, +4 for each running daemon."},
    "MAN_IN_THE_MIDDLE": {"kind": "EXEC", "ram": 1500, "req": 1, "dmg": 8, "block": 5, "text": "Deal 8 damage. Gain 5 shield this turn."},
    "PAYLOAD_DROP": {"kind": "EXEC", "ram": 2000, "req": 1, "dmg": 14, "leech": 4, "text": "Deal 14 damage. Restore 4 integrity."},
    "BRUTE_FORCE": {"kind": "EXEC", "ram": 2500, "req": 1, "dmg": 18, "trace": 3, "text": "Deal 18 damage. Noisy: +3% trace."},
    "BUFFER_OVERFLOW": {"kind": "EXEC", "ram": 2500, "req": 1, "dmg": 16, "pierce": True, "text": "Deal 16 damage. Ignores the clearance penalty."},

    "SWAP_FILE.py": {"kind": "DAEMON", "ram": 750, "req": 0, "bonus_ram": 1000, "text": "Daemon. Raises your RAM limit by 1 GB."},
    "RELAY.py": {"kind": "DAEMON", "ram": 1000, "req": 0, "shield": 2, "text": "Daemon. +2 shield every turn."},
    "SPOOF_MAC.py": {"kind": "DAEMON", "ram": 1500, "req": 0, "shield": 4, "text": "Daemon. +4 shield every turn."},
    "KEYLOGGER.py": {"kind": "DAEMON", "ram": 1500, "req": 0, "burn": 4, "text": "Daemon. Deal 4 damage to ICE every turn."},
    "WATCHDOG.py": {"kind": "DAEMON", "ram": 1500, "req": 0, "regen": 3, "text": "Daemon. Restore 3 integrity every turn."},
    "CRYPTO_MINER.py": {"kind": "DAEMON", "ram": 1500, "req": 0, "extra_draw": 1, "text": "Daemon. Draw 1 extra card every turn."},
    "LEECH_WORM.py": {"kind": "DAEMON", "ram": 1500, "req": 0, "burn": 2, "regen": 2, "text": "Daemon. Deal 2 damage and restore 2 integrity every turn."},
    "VP_VPN.py": {"kind": "DAEMON", "ram": 2000, "req": 1, "vpn": 1, "text": "Daemon. -1% trace every turn."},
    "HONEYPOT.py": {"kind": "DAEMON", "ram": 2000, "req": 1, "dull": 3, "text": "Daemon. ICE strikes for 3 less."},
    "BOTNET.py": {"kind": "DAEMON", "ram": 2500, "req": 1, "burn": 7, "text": "Daemon. Deal 7 damage to ICE every turn."},
    "PROXY_CHAIN.py": {"kind": "DAEMON", "ram": 2500, "req": 1, "shield": 3, "vpn": 1, "text": "Daemon. +3 shield and -1% trace every turn."},
    "RAM_DISK.py": {"kind": "DAEMON", "ram": 1500, "req": 1, "bonus_ram": 2500, "text": "Daemon. Raises your RAM limit by 2.5 GB."},

    "GARBAGE_COLLECTOR": {"kind": "OPT", "ram": 0, "req": 0, "free": 3000, "draw": 1, "text": "Free up to 3 GB of RAM in use and draw 1 card."},
    "CACHE_DUMP": {"kind": "OPT", "ram": 0, "req": 0, "free": 1500, "text": "Free up to 1.5 GB of RAM in use."},
    "CHECKSUM_TOOL": {"kind": "OPT", "ram": 250, "req": 0, "scan": 2, "text": "Rule out 2 wrong files in the next extraction."},
    "TIME_DILATION": {"kind": "OPT", "ram": 250, "req": 0, "time": 6, "text": "Add 6 seconds to the next extraction timer."},
    "OVERCLOCK": {"kind": "OPT", "ram": 250, "req": 0, "surge": 2000, "trace": 3, "text": "RAM limit +2 GB this turn. +3% trace."},
    "POLYMORPHIC_SHELL": {"kind": "OPT", "ram": 500, "req": 1, "reset": True, "text": "Reset the executable streak to zero."},
    "FIREWALL_PATCH": {"kind": "OPT", "ram": 500, "req": 0, "block": 6, "text": "Gain 6 shield this turn."},
    "STATIC_NOISE": {"kind": "OPT", "ram": 500, "req": 0, "weaken": 2, "text": "ICE strikes for 2 less for the rest of this layer."},
    "HOT_SWAP": {"kind": "OPT", "ram": 500, "req": 0, "cycle": True, "text": "Discard your hand and draw the same number of new cards."},
    "DEEP_PACKET": {"kind": "OPT", "ram": 500, "req": 0, "draw": 1, "scan": 1, "text": "Draw 1 card. Rule out 1 wrong file next extraction."},
    "BURNER_ACCOUNT": {"kind": "OPT", "ram": 500, "req": 0, "wipe": 4, "text": "Remove 4% trace."},
    "PHISH_KIT": {"kind": "OPT", "ram": 750, "req": 0, "draw": 2, "trace": 2, "text": "Draw 2 cards. +2% trace."},
    "COOLANT": {"kind": "OPT", "ram": 750, "req": 0, "heal": 6, "block": 3, "text": "Restore 6 integrity. Gain 3 shield."},
    "SANDBOX_ESCAPE": {"kind": "OPT", "ram": 1000, "req": 0, "reset": True, "draw": 1, "text": "Reset the executable streak. Draw 1 card."},
    "ZERO_TRUST": {"kind": "OPT", "ram": 1500, "req": 0, "block": 12, "text": "Gain 12 shield this turn."},
    "LOG_WIPER": {"kind": "OPT", "ram": 1500, "req": 1, "wipe": 8, "text": "Remove 8% trace."},
    "SYSTEM_RESTORE": {"kind": "OPT", "ram": 1500, "req": 1, "heal": 12, "text": "Restore 12 integrity."},

    "TOKEN_THEFT": {"kind": "EXPLOIT", "ram": 1000, "req": 0, "grant": 1, "trace": 3, "text": "Clearance to USER. +3% trace."},
    "PASS_THE_HASH": {"kind": "EXPLOIT", "ram": 1500, "req": 0, "grant": 1, "draw": 2, "trace": 5, "text": "Clearance to USER. Draw 2. +5% trace."},
    "SUDO_EXPLOIT": {"kind": "EXPLOIT", "ram": 1500, "req": 1, "grant": 2, "draw": 1, "trace": 4, "text": "Clearance to OPERATOR. Draw 1. +4% trace."},
    "SUPPLY_CHAIN": {"kind": "EXPLOIT", "ram": 1500, "req": 1, "dmg": 10, "grant": 1, "text": "Deal 10 damage. Clearance to USER."},
    "DLL_HIJACK": {"kind": "EXPLOIT", "ram": 2000, "req": 1, "dmg": 12, "weaken": 2, "trace": 3, "text": "Deal 12 damage. ICE strikes for 2 less. +3% trace."},
    "ROOTKIT": {"kind": "EXPLOIT", "ram": 2500, "req": 2, "grant": 3, "trace": 6, "text": "Clearance to ROOT. +6% trace."},
    "BACKDOOR": {"kind": "EXPLOIT", "ram": 2500, "req": 1, "grant": 2, "block": 6, "trace": 3, "text": "Clearance to OPERATOR. Gain 6 shield. +3% trace."},
    "LOGIC_BOMB": {"kind": "EXPLOIT", "ram": 2500, "req": 1, "dmg": 22, "hp_cost": 5, "trace": 4, "text": "Deal 22 damage. Costs 5 integrity. +4% trace."},
    "KILL_SWITCH": {"kind": "EXPLOIT", "ram": 2500, "req": 2, "dmg": 10, "stun": 1, "trace": 3, "text": "Deal 10 damage. ICE skips its next strike. +3% trace."},
    "ZERO_CLICK": {"kind": "EXPLOIT", "ram": 3000, "req": 2, "dmg": 20, "draw": 1, "trace": 5, "text": "Deal 20 damage. Draw 1 card. +5% trace."},
    "SCORCHED_EARTH": {"kind": "EXPLOIT", "ram": 3000, "req": 2, "dmg": 28, "hp_cost": 8, "trace": 5, "text": "Deal 28 damage. Costs 8 integrity. +5% trace."},
    "ZERO_DAY": {"kind": "EXPLOIT", "ram": 3500, "req": 2, "dmg": 25, "trace": 6, "text": "Deal 25 damage. +6% trace."},
    "RANSOMWARE": {"kind": "EXPLOIT", "ram": 3500, "req": 2, "dmg": 30, "trace": 7, "text": "Deal 30 damage. +7% trace."},
    "SINGULARITY": {"kind": "EXPLOIT", "ram": 4000, "req": 3, "dmg": 18, "hits": 2, "trace": 8, "text": "Root only. Deal 18 damage twice. +8% trace."},
    "AIR_GAP_BRIDGE": {"kind": "EXPLOIT", "ram": 3500, "req": 3, "dmg": 40, "lock": 4000, "text": "Tier 3 only. Deal 40. RAM locked to 4 GB this layer."},
}

START = (["PING"] * 3 + ["SQL_INJECTION"] * 2 +
         ["SPOOF_MAC.py", "GARBAGE_COLLECTOR", "PASS_THE_HASH", "SUDO_EXPLOIT", "BRUTE_FORCE",
          "POLYMORPHIC_SHELL", "VP_VPN.py", "FIREWALL_PATCH"])

TIERS = [
    {"name": "TIER 0 // THE DMZ", "ice": "GUEST_PORTAL", "hp": 30, "atk": 4, "min": 0,
     "blurb": "Public portals and guest wifi. Soft target.", "goal": "take the network map",
     "story": "The DMZ is Palanterror's front porch. Break the portal, then copy the network map so you know where everything else is."},
    {"name": "TIER 1 // ACTIVE DIRECTORY", "ice": "DOMAIN_GATEKEEPER", "hp": 45, "atk": 6, "min": 1,
     "blurb": "Needs USER clearance or your damage is halved.", "goal": "take the staff directory",
     "story": "Every employee login lives here. Steal the staff directory to get the credentials you need to go deeper."},
    {"name": "TIER 2 // DATA PIPELINES", "ice": "ACTIVE_SNIFFER", "hp": 60, "atk": 8, "min": 0,
     "blurb": "Executables with no daemon running add +2% trace.", "goal": "take the feed keys",
     "story": "Live surveillance flows through these pipes. Take the feed keys, because the vault door will not open without them."},
    {"name": "TIER 3 // AIR-GAPPED VAULT", "ice": "POLICING_AI", "hp": 90, "atk": 10, "min": 2,
     "blurb": "Needs OPERATOR clearance or your damage is halved.", "goal": "take the EXODUS_PAYLOAD",
     "story": "The vault holds the EXODUS_PAYLOAD: proof of everyone Palanterror wrongly flagged. Copies are everywhere, and most are traps."},
    {"name": "TIER 4 // EXTRACTION TUNNEL", "ice": "BLACK_ICE_HUNTER", "hp": 110, "atk": 14, "min": 1,
     "blurb": "Black-ice hits hard. Needs USER clearance.", "goal": "reach the Lantern's dropbox",
     "story": "You have the payload. Fight through the tunnel and send it to the journalists' dropbox before the hunters catch you."},
]

TARGETS = [
    ("guest_wifi_map", "db", "dmz-edge", 40),
    ("staff_directory", "csv", "ad-root", 180),
    ("feed_keys", "pem", "pipe-gw", 6),
    ("EXODUS_PAYLOAD", "enc", "vault-core", 2400),
    ("secure_dropbox", "key", "lantern-drop", 3),
]

PRESETS = {
    "easy": {"ice": 70, "trace": 70, "ram": 12, "hand": 5, "timer": 30},
    "normal": {"ice": 100, "trace": 100, "ram": 10, "hand": 5, "timer": 20},
    "hard": {"ice": 110, "trace": 120, "ram": 8, "hand": 5, "timer": 12},
}

DEFAULTS = dict(PRESETS["normal"], preset="normal", extract=True, shake=True, typing="normal", story=True)

STORY = [
    "THE CITY, 2031\n\nPalanterror is the police AI that runs the city. It watches every phone,\n"
    "camera and bus pass, predicts who will commit a crime, and has them\narrested before they do anything.\n\n"
    "Most of them never would have.\n\nA group of journalists called the Lantern hired you to prove it.",

    "THE PLAN\n\nThe proof is a file called EXODUS_PAYLOAD, locked in Palanterror's vault.\n"
    "You have to cross five layers of its network, one at a time.\n\n"
    "1. Each layer is guarded by ICE. Destroy it with your cards.\n"
    "2. Then copy the layer's real file. It is hidden among decoys, and the\n"
    "   malware copies look almost identical. Check name, signer and size.\n"
    "3. Pick a new tool and go deeper.\n\nFinish all five layers and the Lantern gets their proof.",
]

RULES = [
    "HOW THE RIG WORKS\n\n"
    "RAM         Cards cost RAM, from 250 MB up to several GB. Daemons stay\n"
    "            installed and keep eating RAM until you uninstall them\n"
    "            (click the chip). Freeing RAM only works on RAM in use.\n"
    "PANIC       Go over your RAM limit and the rig crashes: -10 integrity,\n"
    "            trace spike, daemons wiped, turn over.\n"
    "TRACE       Climbs every turn. At 100% you are locked out for good.\n"
    "SIGNATURE   Three executables in a row and trace gain triples.\n"
    "            Daemons and optimizers reset it.\n"
    "CLEARANCE   guest > user > operator > root. Some cards and layers need more.\n"
    "EXTRACTION  After you break a layer, find the file that matches the target\n"
    "            exactly. A wrong click runs malware: damage, trace, and a\n"
    "            card in your deck gets corrupted. Run out of time and it hurts too.\n\n"
    "keys: 1-9 play a card or pick a file, space ends your turn",

    "BUILDING A DECK\n\n"
    "Open the deck builder from the main menu. You have three deck slots.\n"
    "The active slot is the one your next run starts with.\n\n"
    "Left click a card to add it, right click it to remove it.\n"
    "A deck needs 10 to 24 cards and at least 3 that work at guest clearance.\n"
    "Powerful cards have a lower copy limit. Cheap ones allow three.\n\n"
    "Cards you pick up during a run only last for that run.",
]


def fmt_ram(mb):
    if mb < 1000:
        return f"{mb} MB"
    return f"{mb / 1000:g} GB"


def copy_limit(name):
    ram = CARDS[name]["ram"]
    if ram >= 3500:
        return 1
    if ram >= 2500:
        return 2
    return 3


def deck_problem(deck):
    if len(deck) < DECK_MIN:
        return f"need at least {DECK_MIN} cards"
    if len(deck) > DECK_MAX:
        return f"no more than {DECK_MAX} cards"
    for name in set(deck):
        if deck.count(name) > copy_limit(name):
            return f"too many copies of {name}"
    if sum(1 for n in deck if CARDS[n]["req"] == 0) < 3:
        return "need 3 cards that work at guest clearance"
    return ""