# Counter.py

import streamlit as st
import math

# --- Page config & styles ---
st.set_page_config(page_title="Kill Team 2025 Scoring App", layout="wide")

PRIMARY_ORANGE = "#f25c05"
BG_DARK = "#0f0f0f"
CARD_BG = "#1b1b1b"
TEXT_LIGHT = "#eaeaea"

st.markdown(f"""
<style>
body {{ background-color: {BG_DARK}; color: {TEXT_LIGHT}; }}
div.block-container {{ padding-top: 1rem; }}
.stButton>button {{ background-color: {PRIMARY_ORANGE}; color: white; border-radius:8px; }}
.st-bc {{ background-color: {CARD_BG}; padding: 12px; border-radius: 10px; margin-bottom:8px; }}
.card-title {{ font-weight:700; color: {PRIMARY_ORANGE}; }}
.small-muted {{ color: #bdbdbd; font-size:12px; }}
.card-grid {{ display: flex; gap: 8px; flex-wrap: wrap; }}
.card-item {{ background: #262626; padding: 8px 10px; border-radius: 8px; color: {TEXT_LIGHT}; }}
.badge {{ background: {PRIMARY_ORANGE}; color: #fff; padding: 3px 8px; border-radius: 6px; font-weight:700; }}
.inactive {{ opacity: 0.45; text-decoration: line-through; }}
input, textarea {{ background: #111; color: {TEXT_LIGHT}; }}
</style>
""", unsafe_allow_html=True)

# --- Initialization ---
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.turn = 0  # 0 = pre-game initiative resolution; 1..4 game turns
    # Players default
    st.session_state.players = {
        "A": {"name": "Player A", "cp": 3, "crit": 0, "tac": 0, "kills": 0, "enemy_initial": 6, "kill_ops_points": 0, "initiative_cards": [], "final_bonus": 0},
        "B": {"name": "Player B", "cp": 3, "crit": 0, "tac": 0, "kills": 0, "enemy_initial": 6, "kill_ops_points": 0, "initiative_cards": [], "final_bonus": 0}
    }
    st.session_state.show_initiative_prompt = True
    st.session_state.advance_after_apply = False
    st.session_state.revealed = False
    st.session_state.tac_op_choice = "(hidden)"
    st.session_state.primary_choice = "(hidden)"
    # default kill ops table: for enemy sizes 4..12, assign points for killed 0..size proportionally as default
    st.session_state.kill_ops_table = {}
    for size in range(4,13):
        row = {}
        for k in range(0, size+1):
            # default mapping proportional to 0..4 points
            row[k] = int(round((k/ max(1,size)) * 4))
        st.session_state.kill_ops_table[size] = row

# --- Helpers ---
def card_for_loss(turn_number):
    if turn_number == 0:
        return {"type": "Repetition", "used": False}
    elif turn_number == 1:
        return {"type": "+1", "used": False}
    elif turn_number == 2:
        return {"type": "+2", "used": False}
    elif turn_number == 3:
        return {"type": "+3", "used": False}
    else:
        return {"type": "Repetition", "used": False}

def apply_initiative(winner_key):
    loser_key = "B" if winner_key == "A" else "A"
    st.session_state.players[winner_key]["cp"] = st.session_state.players[winner_key].get("cp",0) + 1
    st.session_state.players[loser_key]["cp"] = st.session_state.players[loser_key].get("cp",0) + 2
    card = card_for_loss(st.session_state.turn)
    st.session_state.players[loser_key]["initiative_cards"].append(card)

def calc_kill_ops_from_table(enemy_initial, killed):
    try:
        enemy_initial = int(enemy_initial)
        killed = int(killed)
    except:
        return 0
    table = st.session_state.kill_ops_table
    if enemy_initial in table:
        row = table[enemy_initial]
        k = max(0, min(killed, max(row.keys())))
        return int(row.get(k,0))
    # fallback proportional
    try:
        return int(round((killed / max(1, enemy_initial)) * 4))
    except:
        return 0

def max_ops_allowed(turn):
    # Crit/Tac: 0 on turn 1, +2 per subsequent turn, up to 6
    # Note: user wanted 0 in first turn (turn 1), but our turns start at 0 pre-game, so formula:
    # if turn <=1 -> 0 ; else -> min(6, (turn-1)*2)
    if turn <= 1:
        return 0
    return min(6, (turn-1)*2)

# --- Header ---
st.markdown(f"<div class='st-bc'><div style='display:flex;justify-content:space-between;align-items:center'>"
            f"<div><h2 class='card-title'>Kill Team 2025 Scoring App</h2><div class='small-muted'>Dark theme · initiative & CP manager</div></div>"
            f"<div style='text-align:right'><span class='badge'>Turn {st.session_state.turn}</span></div></div></div>", unsafe_allow_html=True)

# --- Initiative prompt section ---
if st.session_state.show_initiative_prompt:
    st.markdown("<div class='st-bc'><strong>Resolve Initiative (current resolution)</strong></div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1,2])
    with c1:
        winner_choice = st.radio("Who won initiative?", options=[st.session_state.players["A"]["name"], st.session_state.players["B"]["name"]], key=f"init_choice_{st.session_state.turn}")
    with c2:
        st.write("When applied: winner +1 CP, loser +2 CP. Loser receives initiative card mapped to the turn of the loss: turn 0→Repetition, turn1→+1, turn2→+2, turn3→+3.")
        if st.button("Apply initiative result"):
            winner_key = "A" if winner_choice == st.session_state.players["A"]["name"] else "B"
            apply_initiative(winner_key)
            st.session_state.show_initiative_prompt = False
            if st.session_state.advance_after_apply:
                if st.session_state.turn < 4:
                    st.session_state.turn += 1
                st.session_state.advance_after_apply = False
            st.rerun()

# --- Main UI layout ---
left, right = st.columns([1,1])

with left:
    st.markdown("<div class='st-bc'><strong>Player A</strong></div>", unsafe_allow_html=True)
    pA = st.session_state.players["A"]
    pA["name"] = st.text_input("Name A", value=pA["name"], key="nameA")
    pA["cp"] = st.number_input("CP A", value=pA.get("cp",3), min_value=0, key="cpA_num")
    allowed = max_ops_allowed(st.session_state.turn)
    st.write(f"Crit Ops (allowed ≤ {allowed})")
    pA["crit"] = st.number_input("Crit A", value=pA.get("crit",0), min_value=0, max_value=6, key="critA_num")
    if pA["crit"] > allowed:
        st.warning(f"Crit Ops cannot exceed {allowed} at this point.")
        pA["crit"] = allowed
    st.write(f"Tac Ops (allowed ≤ {allowed})")
    pA["tac"] = st.number_input("Tac A", value=pA.get("tac",0), min_value=0, max_value=6, key="tacA_num")
    if pA["tac"] > allowed:
        st.warning(f"Tac Ops cannot exceed {allowed} at this point.")
        pA["tac"] = allowed
    pA["enemy_initial"] = st.number_input("Enemy initial size A", value=pA.get("enemy_initial",6), min_value=1, key="einitA")
    pA["kills"] = st.number_input("Kills A", value=pA.get("kills",0), min_value=0, key="killsA")

    st.markdown("**Initiative cards A**")
    if not pA["initiative_cards"]:
        st.write("— None —")
    else:
        for i, c in enumerate(pA["initiative_cards"]):
            used = st.checkbox(f"A card {i+1} ({c['type']}) used", value=c.get("used",False), key=f"cardA_{i}")
            pA["initiative_cards"][i]["used"] = used

with right:
    st.markdown("<div class='st-bc'><strong>Player B</strong></div>", unsafe_allow_html=True)
    pB = st.session_state.players["B"]
    pB["name"] = st.text_input("Name B", value=pB["name"], key="nameB")
    pB["cp"] = st.number_input("CP B", value=pB.get("cp",3), min_value=0, key="cpB_num")
    st.write(f"Crit Ops (allowed ≤ {allowed})")
    pB["crit"] = st.number_input("Crit B", value=pB.get("crit",0), min_value=0, max_value=6, key="critB_num")
    if pB["crit"] > allowed:
        st.warning(f"Crit Ops cannot exceed {allowed} at this point.")
        pB["crit"] = allowed
    st.write(f"Tac Ops (allowed ≤ {allowed})")
    pB["tac"] = st.number_input("Tac B", value=pB.get("tac",0), min_value=0, max_value=6, key="tacB_num")
    if pB["tac"] > allowed:
        st.warning(f"Tac Ops cannot exceed {allowed} at this point.")
        pB["tac"] = allowed
    pB["enemy_initial"] = st.number_input("Enemy initial size B", value=pB.get("enemy_initial",6), min_value=1, key="einitB")
    pB["kills"] = st.number_input("Kills B", value=pB.get("kills",0), min_value=0, key="killsB")

    st.markdown("**Initiative cards B**")
    if not pB["initiative_cards"]:
        st.write("— None —")
    else:
        for i, c in enumerate(pB["initiative_cards"]):
            used = st.checkbox(f"B card {i+1} ({c['type']}) used", value=c.get("used",False), key=f"cardB_{i}")
            pB["initiative_cards"][i]["used"] = used

st.markdown("---")

# Controls row
c1, c2, c3 = st.columns([1,1,2])
with c1:
    if st.button("Advance turn (prompts initiative then advances)"):
        st.session_state.advance_after_apply = True
        st.session_state.show_initiative_prompt = True
        st.experimental_rerun()
with c2:
    if st.button("Resolve initiative now (no advance)"):
        st.session_state.show_initiative_prompt = True
        st.experimental_rerun()
with c3:
    if st.button("Reset match"):
        st.session_state.clear()
        st.experimental_rerun()

st.markdown("---")

# Kill Ops calculation from table
pA["kill_ops_points"] = calc_kill_ops_from_table(pA["enemy_initial"], pA["kills"])
pB["kill_ops_points"] = calc_kill_ops_from_table(pB["enemy_initial"], pB["kills"])

st.markdown("<div class='st-bc'><strong>Match summary</strong></div>", unsafe_allow_html=True)
st.write(f"{pA['name']} — CP: {pA['cp']} | Crit: {pA['crit']} | Tac: {pA['tac']} | KillOps: {pA['kill_ops_points']}")
st.write(f"{pB['name']} — CP: {pB['cp']} | Crit: {pB['crit']} | Tac: {pB['tac']} | KillOps: {pB['kill_ops_points']}")

# Pre-game secret selection
st.markdown("### Pre-game secret selections")
if st.session_state.tac_op_choice == "(hidden)":
    tac_options = ["(none)", "Hold Ground", "Secure Objective", "Sabotage", "Assassinate"]
    st.session_state.tac_op_choice = st.selectbox("Choose Tac Op mission (hidden until reveal)", options=tac_options, index=0, key="tac_select")
else:
    if not st.session_state.revealed and st.session_state.turn <= 4:
        st.write("Tac Op mission is set (hidden until reveal).")
    else:
        st.write("Tac Op mission:", st.session_state.tac_op_choice)

if st.session_state.primary_choice == "(hidden)":
    st.session_state.primary_choice = st.selectbox("Choose primary wager (hidden until reveal)", options=["(none)","Crit Ops","Tac Ops","Kill Ops"], index=0, key="primary_select")
else:
    if not st.session_state.revealed and st.session_state.turn <= 4:
        st.write("Primary wager is set (hidden until reveal).")
    else:
        st.write("Primary wager:", st.session_state.primary_choice)

# Kill Ops table editor in sidebar (simple inputs)
with st.sidebar.expander("Edit Kill Ops table (default proportional values)"):
    st.markdown("Choose enemy initial size to edit then set points for each 'killed' value.")
    sizes = sorted(list(st.session_state.kill_ops_table.keys()))
    chosen = st.selectbox("Enemy initial size", options=sizes, index= sizes.index(6) if 6 in sizes else 0)
    row = st.session_state.kill_ops_table[chosen]
    st.markdown(f"Editing table for enemy initial size = {chosen}. Set points for killed = 0..{chosen}.")
    new_row = {}
    cols = st.columns(3)
    for k in range(0, chosen+1):
        col = cols[k % 3]
        val = col.number_input(f"killed={k}", value=row.get(k,0), min_value=0, max_value=20, key=f"tbl_{chosen}_{k}")
        new_row[k] = int(val)
    st.session_state.kill_ops_table[chosen] = new_row
    if st.button("Save table row", key="save_tbl"):
        st.success(f"Saved row for size {chosen}.")

# Finalize match
if st.button("Finalize match (reveal & apply final bonuses)"):
    st.session_state.revealed = True
    # assign final bonus +1 to higher kill_ops (tie -> none)
    if pA["kill_ops_points"] > pB["kill_ops_points"]:
        st.session_state.players["A"]["final_bonus"] = 1
        st.session_state.players["B"]["final_bonus"] = 0
    elif pB["kill_ops_points"] > pA["kill_ops_points"]:
        st.session_state.players["B"]["final_bonus"] = 1
        st.session_state.players["A"]["final_bonus"] = 0
    else:
        st.session_state.players["A"]["final_bonus"] = 0
        st.session_state.players["B"]["final_bonus"] = 0
    st.experimental_rerun()

# Reveal block and primary bonuses
if st.session_state.revealed or st.session_state.turn > 4:
    st.markdown("### Revealed at end of match")
    st.write("Tac Op mission:", st.session_state.tac_op_choice)
    st.write("Primary wager:", st.session_state.primary_choice)
    def primary_bonus(player, choice):
        if choice == "Crit Ops":
            return math.ceil(player.get("crit",0)/2)
        if choice == "Tac Ops":
            return math.ceil(player.get("tac",0)/2)
        if choice == "Kill Ops":
            return math.ceil(player.get("kill_ops_points",0)/2)
        return 0
    a_primary = primary_bonus(pA, st.session_state.primary_choice)
    b_primary = primary_bonus(pB, st.session_state.primary_choice)
    st.write(f"{pA['name']} primary bonus: {a_primary} | {pB['name']} primary bonus: {b_primary}")

# Totals
def total(player):
    prim = 0
    if st.session_state.revealed or st.session_state.turn > 4:
        if st.session_state.primary_choice != "(none)":
            if st.session_state.primary_choice == "Crit Ops":
                prim = math.ceil(player.get("crit",0)/2)
            elif st.session_state.primary_choice == "Tac Ops":
                prim = math.ceil(player.get("tac",0)/2)
            elif st.session_state.primary_choice == "Kill Ops":
                prim = math.ceil(player.get("kill_ops_points",0)/2)
    return player.get("crit",0) + player.get("tac",0) + player.get("kill_ops_points",0) + player.get("final_bonus",0) + prim

st.markdown("---")
st.write(f"**Totals:** {pA['name']}: {total(pA)}  |  {pB['name']}: {total(pB)}")
st.markdown("---")
st.markdown("<div class='small-muted'>Phase-2 Pro: initiative rules (turn 0), CP auto on initiative, initiative cards per-turn, kill ops table editor in sidebar. State persists in session. Next: export/import & cloud save.</div>", unsafe_allow_html=True)
