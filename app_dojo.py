# app_dojo.py
import streamlit as st
import json
import gspread
from datetime import datetime
import pandas as pd
from google.oauth2.service_account import Credentials
from data_dojo import KIDS, BEHAVIORS, MILESTONES

# ---- CONFIGURATION ----
st.set_page_config(
    page_title="Family Dojo Points Tracker",
    page_icon="🎯",
    layout="centered"
)

# Custom Styling
st.markdown("""
    <style>
        div.stButton > button:first-child {
            background-color: #6366f1 !important;
            color: white !important;
            border-radius: 8px !important;
            border: none !important;
            font-weight: bold !important;
            height: 45px !important;
        }
        .kid-card {
            background-color: #f8fafc;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            margin-bottom: 15px;
            text-align: center;
        }
        .thermometer-container {
            background-color: #e2e8f0;
            border-radius: 20px;
            position: relative;
            height: 30px;
            width: 100%;
            margin-top: 10px;
            overflow: hidden;
            border: 1px solid #cbd5e1;
        }
        .thermometer-fill {
            background: linear-gradient(90deg, #ff4b4b 0%, #6366f1 100%);
            height: 100%;
            border-radius: 20px;
            transition: width 0.5s ease-in-out;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🎯 Family Dojo Points Tracker")
st.write("Encouraging habits and tracking goals together!")
st.divider()

# ---- GOOGLE SHEETS CORE ----
# 🚨 PASTE YOUR GOOGLE SHEET URL HERE 🚨
SHEET_URL = "https://docs.google.com/spreadsheets/d/1VVVJt5ze_tnqk7jGL0-JVQLNL2HVi0FX0h5Lqspo5WA/edit?gid=0#gid=0"
EMOJI_MAPPING = {"Ari": "👧 Ari", "AJ": "👦 AJ"}

# Connect to Google securely via Streamlit Secrets
creds_dict = json.loads(st.secrets["google_credentials"])
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
gc = gspread.authorize(creds)

@st.cache_data(ttl=5)  # Caches data for 5 seconds so we don't overwhelm Google's servers
def load_data():
    sheet = gc.open_by_url(SHEET_URL).sheet1
    records = sheet.get_all_records()
    df = pd.DataFrame(records)
    
    history = []
    totals = {"Ari": 0, "AJ": 0}
    
    if not df.empty:
        for index, row in df.iterrows():
            raw_kid = str(row.get('Kid', ''))
            clean_kid = "Ari" if "Ari" in raw_kid else "AJ" if "AJ" in raw_kid else raw_kid.strip()
            try:
                pts = int(row.get('Points', 0))
            except (ValueError, TypeError):
                pts = 0
                
            if clean_kid in totals:
                totals[clean_kid] += pts
                
            history.append(row.to_dict())
            
    return history, totals

history_log, totals = load_data()

# ---- NAVIGATION TABS ----
tab_dash, tab_add, tab_rewards, tab_history = st.tabs([
    "📊 Leaderboard & Thermometers", "⚡ Log Points", "🎁 Reward Milestones", "📜 History Log"
])

# ---- TAB 1: LEADERBOARD & THERMOMETERS ----
with tab_dash:
    st.header("Point Thermometers")
    st.write("Tracking progress toward the major 100-point milestone goal!")
    
    col1, col2 = st.columns(2)
    THERMOMETER_GOAL = 100  
    
    with col1:
        st.markdown('<div class="kid-card">', unsafe_allow_html=True)
        st.subheader(EMOJI_MAPPING["Ari"])
        st.metric(label="Total Balance", value=f"{totals['Ari']} pts")
        
        ari_pct = min(max(float(totals['Ari']) / THERMOMETER_GOAL, 0.0), 1.0) * 100
        st.markdown(f"**Goal Progress: {int(ari_pct)}%**")
        st.markdown(f"""
            <div class="thermometer-container">
                <div class="thermometer-fill" style="width: {ari_pct}%;"></div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="kid-card">', unsafe_allow_html=True)
        st.subheader(EMOJI_MAPPING["AJ"])
        st.metric(label="Total Balance", value=f"{totals['AJ']} pts")
        
        aj_pct = min(max(float(totals['AJ']) / THERMOMETER_GOAL, 0.0), 1.0) * 100
        st.markdown(f"**Goal Progress: {int(aj_pct)}%**")
        st.markdown(f"""
            <div class="thermometer-container">
                <div class="thermometer-fill" style="width: {aj_pct}%;"></div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ---- TAB 2: LOG POINTS (ADD / DEDUCT) ----
with tab_add:
    st.header("Adjust Dojo Points Balance")
    
    if "success_msg" in st.session_state:
        st.success(st.session_state["success_msg"])
        del st.session_state["success_msg"]
    
    kid_display = st.radio("Select Child:", [EMOJI_MAPPING["Ari"], EMOJI_MAPPING["AJ"]], horizontal=True)
    action_type = st.radio("Action Type:", ["Award / Add Points 🟢", "Deduct / Remove Points 🔴"], horizontal=True)
    behavior_key = st.selectbox("Select Associated Behavior", list(BEHAVIORS.keys()))
    raw_points = st.number_input("Point Count", min_value=1, max_value=20, value=1, step=1)
    optional_notes = st.text_input("Notes / Context")
    
    submit_points = st.button("Submit Points Adjustment", type="primary", use_container_width=True)
    
    if submit_points:
        selected_kid = "Ari" if "Ari" in kid_display else "AJ"
        is_deduction = "Deduct" in action_type
        
        try:
            final_points = -abs(int(raw_points)) if is_deduction else abs(int(raw_points))
        except Exception:
            final_points = 1
            
        action_label = "Deduction" if is_deduction else "Award"
        behavior_desc = BEHAVIORS.get(behavior_key, f"Custom: {behavior_key}")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        safe_notes = str(optional_notes)
        safe_category = str(behavior_desc)
        
        # Write directly to Google Sheets
        sheet = gc.open_by_url(SHEET_URL).sheet1
        sheet.append_row([timestamp, selected_kid, action_label, safe_category, final_points, safe_notes])
            
        st.session_state["success_msg"] = f"Successfully logged {abs(final_points)} points for {selected_kid}!"
        st.cache_data.clear()  # Wipes the local cache so the app instantly fetches the new row!
        st.rerun()

# ---- TAB 3: REWARD MILESTONES ----
with tab_rewards:
    st.header("🎁 Prize Milestones")
    st.write("Track how close Ari and AJ are to unlocking their next reward targets!")
    
    selected_view_display = st.selectbox("Check milestone progress for:", [EMOJI_MAPPING["Ari"], EMOJI_MAPPING["AJ"]])
    selected_view = "Ari" if "Ari" in selected_view_display else "AJ"
    
    current_points = totals.get(selected_view, 0)
    
    st.write(f"**{selected_view_display} has: {current_points} points**")
    
    for mile in MILESTONES:
        target = mile.get("points", 100)
        reward_text = mile.get("reward", "Reward")
        
        progress_pct = min(max(float(current_points) / float(target), 0.0), 1.0)
        status_emoji = "✅ UNLOCKED!" if current_points >= target else f"⏳ {target - current_points} pts away"
        
        with st.expander(f"🏅 {target} Points Target — {status_emoji}"):
            st.progress(progress_pct)
            st.write(f"**Prize Item:** {reward_text}")

# ---- TAB 4: HISTORY LOG ----
with tab_history:
    st.header("Activity History")
    if history_log:
        display_list = []
        for row in history_log:
            display_list.append({
                "Timestamp": row.get("Timestamp", ""),
                "Kid": EMOJI_MAPPING.get(row.get("Kid", "Ari"), row.get("Kid", "Ari")),
                "Action": row.get("Action", ""),
                "Category": row.get("Category", ""),
                "Points": row.get("Points", 0),
                "Notes": row.get("Notes", "")
            })
        display_df = pd.DataFrame(display_list)
        st.dataframe(display_df.iloc[::-1], use_container_width=True)
    else:
        st.info("No activity logged yet.")
