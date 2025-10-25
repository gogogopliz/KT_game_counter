# KT_game_counter
# Kill Team 2025 — Match Scorer (Streamlit Prototype)

Single-file Streamlit prototype to keep score during Kill Team 2025 matches. Includes:
- Turn control and initiative handling
- CP tracking (editable anytime)
- Crit Ops and Tac Ops counters with per-turn maximums
- Kill Ops calculator with editable table
- Initiative cards list (mark used)
- Secret Tac Op mission and Primary wager (revealed at end)
- Export / Import match JSON

## Files
- `app.py` — main Streamlit app
- `requirements.txt` — Python dependencies

## How to run locally
1. Install Python 3.10+ and create a virtualenv (recommended).
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run Streamlit:
   ```bash
   streamlit run app.py
   ```
4. Open the URL shown in the terminal on your mobile/tablet or desktop.

## How to publish on Streamlit Community Cloud (free)
1. Create a GitHub repository and push these files (`app.py`, `requirements.txt`, `README.md`).
2. Go to https://streamlit.io/cloud and sign in with GitHub.
3. Click "New app", choose your repo and branch, and deploy.
4. The app will be hosted and can be installed on mobile as a PWA (add to home screen).

## Notes on Kill Ops table
- This app includes an editable Kill Ops table. You should fill it with the official table values from Games Workshop (if you have them).

## License & IP
- This is a third-party fan tool. Avoid distributing copyrighted official PDFs without permission.
