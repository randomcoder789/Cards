PRIV = ["GUEST", "USER", "OPERATOR", "ROOT"]

CARDS = {
    "PING": {"kind": "EXEC", "ram": 1, "req": 0, "dmg": 5, "text": "Deal 5 damage. Quiet traffic, never flagged."},
    "SQL_INJECTION": {"kind": "EXEC", "ram": 2, "req": 0, "dmg": 12, "text": "Deal 12 damage."},
    "BRUTE_FORCE": {"kind": "EXEC", "ram": 3, "req": 1, "dmg": 18, "trace": 3, "text": "Deal 18 damage. Noisy: +3% trace."},
    "SPOOF_MAC.py": {"kind": "DAEMON", "ram": 2, "req": 0, "shield": 4, "text": "Daemon. +4 shield every turn."},
    "VP_VPN.py": {"kind": "DAEMON", "ram": 3, "req": 1, "vpn": 1, "text": "Daemon. -1% trace every turn."},
    "GARBAGE_COLLECTOR": {"kind": "OPT", "ram": 0, "req": 0, "free": 3, "draw": 1, "text": "Free 3 GB of RAM and draw 1 card."},
    "POLYMORPHIC_SHELL": {"kind": "OPT", "ram": 1, "req": 1, "reset": True, "text": "Reset the executable streak to zero."},
    "FIREWALL_PATCH": {"kind": "OPT", "ram": 1, "req": 0, "block": 6, "text": "Gain 6 shield this turn."},
    "PHISH_KIT": {"kind": "OPT", "ram": 1, "req": 0, "draw": 2, "trace": 2, "text": "Draw 2 cards. +2% trace."},
    "LOG_WIPER": {"kind": "OPT", "ram": 2, "req": 1, "wipe": 8, "text": "Remove 8% trace."},
    "PASS_THE_HASH": {"kind": "EXPLOIT", "ram": 2, "req": 0, "grant": 1, "draw": 2, "trace": 5, "text": "Clearance to USER. Draw 2. +5% trace."},
    "SUDO_EXPLOIT": {"kind": "EXPLOIT", "ram": 2, "req": 1, "grant": 2, "draw": 1, "trace": 4, "text": "Clearance to OPERATOR. Draw 1. +4% trace."},
    "ROOTKIT": {"kind": "EXPLOIT", "ram": 3, "req": 2, "grant": 3, "trace": 6, "text": "Clearance to ROOT. +6% trace."},
    "ZERO_DAY": {"kind": "EXPLOIT", "ram": 4, "req": 2, "dmg": 25, "trace": 6, "text": "Deal 25 damage. +6% trace."},
    "AIR_GAP_BRIDGE": {"kind": "EXPLOIT", "ram": 4, "req": 3, "dmg": 40, "lock": 4, "text": "Tier 3 only. Deal 40. RAM locked to 4 GB this layer."},
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
    "easy": {"ice": 70, "trace": 70, "ram": 8, "hand": 5, "timer": 30},
    "normal": {"ice": 100, "trace": 100, "ram": 8, "hand": 5, "timer": 20},
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
    "RAM         You spend RAM to play cards. Daemons stay installed and keep\n"
    "            eating RAM until you uninstall them (click the chip).\n"
    "PANIC       Go over your RAM and the rig crashes: -10 integrity, trace\n"
    "            spike, daemons wiped, turn over.\n"
    "TRACE       Climbs every turn. At 100% you are locked out for good.\n"
    "SIGNATURE   Three executables in a row and trace gain triples.\n"
    "            Daemons and optimizers reset it.\n"
    "CLEARANCE   guest > user > operator > root. Some cards and layers need more.\n"
    "EXTRACTION  After you break a layer, find the file that matches the target\n"
    "            exactly. A wrong click runs malware: damage, trace, and a\n"
    "            card in your deck gets corrupted. Run out of time and it hurts too.\n\n"
    "keys: 1-9 play a card or pick a file, space ends your turn",
]