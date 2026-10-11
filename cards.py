PRIV = ["GUEST", "USER", "OPERATOR", "ROOT"]

CARDS = {
    "PING": {"kind": "EXEC", "ram": 1, "req": 0, "dmg": 5,
                 "text": "Deal 5 damage. Quiet traffic."},
    "SQL_INJECTION": {"kind": "EXEC", "ram": 2, "req": 0, "dmg": 12,
                          "text": "Deal 12 damage."},
    "BRUTE_FORCE": {"kind": "EXEC", "ram": 3, "req": 1, "dmg": 18, "trace": 3,
                        "text": "Deal 18 damage. Noisy: +3% trace."},
    "SPOOF_MAC.py": {"kind": "DAEMON", "ram": 2, "req": 0, "shield": 4,
                         "text": "Daemon. +4 shield every turn. Holds 2 GB."},
    "VP_VPN.py": {"kind": "DAEMON", "ram": 3, "req": 1, "vpn": 1,
                      "text": "Daemon. -1% trace every turn. Holds 3 GB."},
    "GARBAGE_COLLECTOR": {"kind": "OPT", "ram": 0, "req": 0, "free": 3, "draw": 1,
                              "text": "Free 3 GB of RAM and draw 1 card."},
    "POLYMORPHIC_SHELL": {"kind": "OPT", "ram": 1, "req": 1, "reset": True,
                              "text": "Reset the executable streak to zero."},
    "PASS_THE_HASH": {"kind": "EXPLOIT", "ram": 2, "req": 0, "grant": 1, "draw": 2, "trace": 5,
                          "text": "Clearance to USER. Draw 2. +5% trace."},
    "SUDO_EXPLOIT": {"kind": "EXPLOIT", "ram": 2, "req": 1, "grant": 2, "draw": 1, "trace": 4,
                         "text": "Clearance to OPERATOR. Draw 1. +4% trace."},
    "ROOTKIT": {"kind": "EXPLOIT", "ram": 3, "req": 2, "grant": 3, "trace": 6,
                    "text": "Clearance to ROOT. +6% trace."},
    "AIR_GAP_BRIDGE": {"kind": "EXPLOIT", "ram": 4, "req": 3, "dmg": 40, "lock": 4,
                           "text": "Tier 3 only. Deal 40. RAM locked to 4 GB this phase."},
}

START = (["PING"] * 3 + ["SQL_INJECTION"] * 2 +
         ["SPOOF_MAC.py", "GARBAGE_COLLECTOR", "PASS_THE_HASH", "SUDO_EXPLOIT",
          "BRUTE_FORCE", "POLYMORPHIC_SHELL", "VP_VPN.py"])

TIERS = [
    {"name": "TIER 0 // THE DMZ", "ice": "GUEST_PORTAL_DAEMON", "hp": 30, "atk": 4, "min": 0,
         "blurb": "Public portals and guest wifi. Soft target."},
    {"name": "TIER 1 // ACTIVE DIRECTORY", "ice": "DOMAIN_GATEKEEPER", "hp": 45, "atk": 6, "min": 1,
     "blurb": "Needs USER clearance or your damage is halved."},
     {"name": "TIER 2 // DATA PIPELINES", "ice": "ACTIVE_SNIFFER", "hp": 60, "atk": 8, "min": 1,
      "blurb": "Needs USER clearance or your damage is halved."},
    {"name": "TIER 3 // AIR-GAPPED VAULT", "ice": "PREDICTIVE_POLICING_AI", "hp": 90, "atk": 10, "min": 2,
     "blurb": "Needs OPERATOR clearance. Holds the EXODUS_PAYLOAD."},
     {"name": "TIER 4 // EXTRACTION TUNNEL", "ice": "BLACK_ICE_HUNTER", "hp": 110, "atk": 14, "min": 3,
      "blurb": "Needs ROOT clearance. Haul the payload out. Black-ice hits hard."},
]
