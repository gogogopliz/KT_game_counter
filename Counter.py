# Counter.py

import streamlit as st

st.set_page_config(page_title="Kill Team 2025 - Simple Counter", layout="wide")

if "turn" not in st.session_state:
    st.session_state.turn = 1
    st.session_state.cpA = 0
    st.session_state.cpB = 0
    st.session_state.critA = 0
    st.session_state.critB = 0
    st.session_state.tacA = 0
    st.session_state.tacB = 0

st.title("Kill Team 2025 - Simple Counter")

col1, col2 = st.columns(2)

with col1:
    st.header("Player A")
    st.session_state.cpA = st.number_input("CP", value=st.session_state.cpA, key="cpA_num")
    st.session_state.critA = st.number_input("Crit Ops", value=st.session_state.critA, key="critA_num")
    st.session_state.tacA = st.number_input("Tac Ops", value=st.session_state.tacA, key="tacA_num")

with col2:
    st.header("Player B")
    st.session_state.cpB = st.number_input("CP", value=st.session_state.cpB, key="cpB_num")
    st.session_state.critB = st.number_input("Crit Ops", value=st.session_state.critB, key="critB_num")
    st.session_state.tacB = st.number_input("Tac Ops", value=st.session_state.tacB, key="tacB_num")

if st.button("Next Turn"):
    st.session_state.turn += 1
    st.session_state.cpA += 1
    st.session_state.cpB += 1

st.markdown(f"### Turn: {st.session_state.turn}")
st.write(f"Player A total: {st.session_state.critA + st.session_state.tacA}")
st.write(f"Player B total: {st.session_state.critB + st.session_state.tacB}")
