# Counter.py
import streamlit as st
import math

st.set_page_config(page_title="KT 2025 - Simple Scorer", layout="wide")

# --- Init session state ---
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.turn = 1
    st.session_state.players = {
        "A": {
            "name": "Player A",
            "cp": 0,
            "crit": 0,
            "tac": 0,
            "kills": 0,
            "enemy_initial": 6,
            "kill_ops_points": 0,
            "initiative_cards": [],
            "final_bonus": 0
        },
        "B": {
            "name": "Player B",
            "cp": 0,
            "crit": 0,
            "tac": 0,
            "kills": 0,
            "enemy_initial": 6,
            "kill_ops_points": 0,
            "initiative_cards": [],
            "final_bonus": 0
        }
    }
    st.session_state.tac_op_choice = "(hidden)"
    st.session_state.primary_choice = "(hidden)"
    st.session_state.revealed = False

# --- Helpers ---
def max_ops_allowed(turn):
    # 0 on turn 1, +2 per subsequent turn, max 6
    return min(6, max(0, (turn - 1) * 2))

def apply_initiative(winner_key):
    loser_key = "B" if winner_key == "A" else "A"
    st.session_state.players[winner_key]["cp"] = st.session_state.players[winner_key].get("cp", 0) + 1
    st.session_state.players[loser_key]["cp"] = st.session_state.players[loser_key].get("cp", 0) + 2
    # loser gets an initiative card (simple default +1)
    st.session_state.players[loser_key]["initiative_cards"].append({"type": "+1", "used": False})

def finalize_match():
    # simple finalize: reveal secrets and lock nothing (user can still edit)
    st.session_state.revealed = True
    # final bonus for kill_ops: whoever has more kills gets +1 (simple approach until table added)
    a_k = st.session_state.players["A"].get("kills", 0)
    b_k = st.session_state.players["B"].get("kills", 0)
    if a_k > b_k:
        st.session_state.players["A"]["final_bonus"] = 1
        st.session_state.players["B"]["final_bonus"] = 0
    elif b_k > a_k:
        st.session_state.players["B"]["final_bonus"] = 1
        st.session_state.players["A"]["final_bonus"] = 0
    else:
        st.session_state.players["A"]["final_bonus"] = 0
        st.session_state.players["B"]["final_bonus"] = 0

# --- Layout ---
st.title("Kill Team 2025 — Simple Scorer")

# Top: Turn control
st.markdown(f"## Current Turn: {st.session_state.turn}")
col_t1, col_t2, col_t3 = st.columns([1,1,2])
with col_t1:
    if st.button("Previous turn") and st.session_state.turn > 1:
        st.session_state.turn -= 1
with col_t2:
    # We show a simple initiative chooser inline to avoid modals (mobile friendly)
    winner_choice = st.radio("Select who won initiative (then press Apply):",
                             options=[st.session_state.players["A"]["name"], st.session_state.players["B"]["name"]],
                             key=f"init_choice_{st.session_state.turn}")
    if st.button("Apply initiative result"):
        winner_key = "A" if winner_choice == st.session_state.players["A"]["name"] else "B"
        apply_initiative(winner_key)
        # advance turn after applying initiative (do not exceed 4 for game logic)
        if st.session_state.turn < 4:
            st.session_state.turn += 1
        else:
            # if it was turn 4 and we applied initiative, consider match ready to finalize
            st.info("Initiative applied on turn 4. You can finalize the match when ready.")
with col_t3:
    st.write("Tip: CP are editable anytime. Use Initiative chooser to apply +1/+2 automatically.")

st.markdown("---")

# Player columns
left, right = st.columns(2)

def player_panel(player_key, container):
    p = st.session_state.players[player_key]
    with container:
        st.subheader(p["name"])
        # Name edit
        new_name = st.text_input("Name", value=p["name"], key=f"name_{player_key}")
        p["name"] = new_name

        # CP controls
        c1, c2, c3 = st.columns([1,1,2])
        with c1:
            if st.button("+CP", key=f"plus_{player_key}"):
                p["cp"] += 1
            if st.button("-CP", key=f"minus_{player_key}"):
                p["cp"] = max(0, p["cp"] - 1)
        with c2:
            new_cp = st.number_input("CP", min_value=0, value=p.get("cp", 0), key=f"cp_input_{player_key}")
            p["cp"] = int(new_cp)
        with c3:
            st.write(f"Cards: {len(p.get('initiative_cards', []))} (tap to mark used below)")

        # Crit / Tac controls with limits
        allowed = max_ops_allowed(st.session_state.turn)
        st.write(f"Crit Ops (allowed ≤ {allowed})")
        new_crit = st.number_input("Crit Ops", min_value=0, max_value=6, value=p.get("crit", 0), key=f"crit_{player_key}")
        if new_crit > allowed:
            st.warning(f"Crit Ops cannot exceed {allowed} at this stage.")
            new_crit = allowed
        p["crit"] = int(new_crit)

        st.write(f"Tac Ops (allowed ≤ {allowed})")
        new_tac = st.number_input("Tac Ops", min_value=0, max_value=6, value=p.get("tac", 0), key=f"tac_{player_key}")
        if new_tac > allowed:
            st.warning(f"Tac Ops cannot exceed {allowed} at this stage.")
            new_tac = allowed
        p["tac"] = int(new_tac)

        # Kills simple input (we'll use this as temporary kill metric)
        p["enemy_initial"] = st.number_input("Enemy initial size", min_value=1, value=p.get("enemy_initial", 6), key=f"enemy_init_{player_key}")
        p["kills"] = st.number_input("Killed", min_value=0, value=p.get("kills", 0), key=f"killed_{player_key}")

        # Initiative cards listing and used toggle
        st.write("Initiative cards:")
        if not p["initiative_cards"]:
            st.write("— No cards — (cards are added when you lose initiative)")
        else:
            for idx, card in enumerate(p["initiative_cards"]):
                used = st.checkbox(f"Card {idx+1} ({card.get('type','?')}) used", value=card.get("used", False), key=f"card_{player_key}_{idx}")
                p["initiative_cards"][idx]["used"] = used

        # Display subtotal
        subtotal = p.get("crit",0) + p.get("tac",0) + p.get("kill_ops_points",0) + p.get("final_bonus",0)
        st.write(f"Subtotal (Crit + Tac + KillOps + final bonus): {subtotal}")
        st.write("---")

with left:
    player_panel("A", st.container())
with right:
    player_panel("B", st.container())

# Bottom controls: secret selection and finalize
st.markdown("## Pre-game secret selections")
if st.session_state.tac_op_choice == "(hidden)":
    # allow setting at start only
    tac = st.selectbox("Choose Tac Op mission (will remain hidden until reveal)", options=["(none)", "Hold Ground", "Secure Objective", "Sabotage"], index=0, key="tac_select")
    st.session_state.tac_op_choice = tac
else:
    if not st.session_state.revealed and st.session_state.turn <= 4:
        st.write("Tac Op mission is set (hidden until reveal).")
    else:
        st.write("Tac Op:", st.session_state.tac_op_choice)

if st.session_state.primary_choice == "(hidden)":
    primary = st.selectbox("Choose primary wager (hidden until reveal)", options=["(none)", "Crit Ops", "Tac Ops", "Kill Ops"], index=0, key="primary_select")
    st.session_state.primary_choice = primary
else:
    if not st.session_state.revealed and st.session_state.turn <= 4:
        st.write("Primary wager set (hidden until reveal).")
    else:
        st.write("Primary wager:", st.session_state.primary_choice)

st.markdown("---")

# Finalize match button
if st.button("Finalize match (reveal secrets & apply simple final bonus)"):
    finalize_match()
    st.success("Match finalized: secrets revealed and simple final bonus applied.")

# Reveal block when finalized or after turn 4
if st.session_state.revealed or st.session_state.turn > 4:
    st.markdown("### Revealed at end of match")
    st.write("Tac Op mission:", st.session_state.tac_op_choice)
    st.write("Primary wager:", st.session_state.primary_choice)
    # Apply primary bonus (half of chosen category rounded up)
    def primary_bonus(player, choice):
        if choice == "Crit Ops":
            return math.ceil(player.get("crit",0)/2)
        if choice == "Tac Ops":
            return math.ceil(player.get("tac",0)/2)
        if choice == "Kill Ops":
            return math.ceil(player.get("kills",0)/2)  # temporary: using kills until table added
        return 0

    a = st.session_state.players["A"]
    b = st.session_state.players["B"]
    a_primary = primary_bonus(a, st.session_state.primary_choice)
    b_primary = primary_bonus(b, st.session_state.primary_choice)
    st.write(f"{a['name']} primary bonus: {a_primary}  |  {b['name']} primary bonus: {b_primary}")

# Totals shown always (live)
def compute_total(p):
    primary = 0
    if st.session_state.revealed or st.session_state.turn > 4:
        # apply using simplified kill metric until full table added
        if st.session_state.primary_choice != "(none)":
            if st.session_state.primary_choice == "Crit Ops":
                primary = math.ceil(p.get("crit",0)/2)
            elif st.session_state.primary_choice == "Tac Ops":
                primary = math.ceil(p.get("tac",0)/2)
            elif st.session_state.primary_choice == "Kill Ops":
                primary = math.ceil(p.get("kills",0)/2)
    return p.get("crit",0) + p.get("tac",0) + p.get("kill_ops_points",0) + p.get("final_bonus",0) + primary

st.markdown("## Live totals")
a_total = compute_total(st.session_state.players["A"])
b_total = compute_total(st.session_state.players["B"])
st.write(f"**{st.session_state.players['A']['name']} total:** {a_total}   |   **{st.session_state.players['B']['name']} total:** {b_total}")

st.markdown("---")
st.write("This is a minimal working prototype. If this runs fine on Streamlit Cloud, we'll progressively re-add the Kill Ops table editor, export/import, and sharing features.")
