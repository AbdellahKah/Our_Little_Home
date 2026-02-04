import streamlit as st
import pandas as pd
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# --- CONFIGURATION ---
st.set_page_config(page_title="Our Forever Home", page_icon="🏡", layout="centered")

# --- FANCY CSS OVERHAUL ---
st.markdown("""
    <style>
    /* 1. IMPORT FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700&family=Pacifico&display=swap');

    /* 2. ANIMATED BACKGROUND */
    .stApp {
        background: linear-gradient(-45deg, #ff9a9e, #fad0c4, #fad0c4, #fbc2eb);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
        font-family: 'Nunito', sans-serif;
    }
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* 3. HEADERS & TEXT */
    h1, h2, h3 {
        font-family: 'Pacifico', cursive;
        color: #5A189A !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        font-weight: normal;
    }
    p, label, span, div {
        color: #4a4a4a;
    }

    /* 4. GLASSMORPHISM CARDS */
    .glass-card {
        background: rgba(255, 255, 255, 0.65);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1);
        transition: transform 0.2s;
    }
    .glass-card:hover {
        transform: translateY(-2px);
    }

    /* 5. CUSTOM TABS */
    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(255,255,255,0.5);
        border-radius: 30px;
        padding: 5px;
        gap: 5px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        border-radius: 25px;
        background-color: transparent;
        color: #5A189A;
        font-weight: 700;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #fff !important;
        color: #FF69B4 !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    /* 6. BUTTONS & INPUTS */
    div.stButton > button {
        background: linear-gradient(90deg, #FF69B4, #DA70D6);
        color: white;
        border: none;
        border-radius: 25px;
        height: 50px;
        font-size: 18px;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(255, 105, 180, 0.3);
        width: 100%;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(255, 105, 180, 0.4);
    }
    
    /* Remove default Streamlit header stuff */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    </style>
""", unsafe_allow_html=True)

# --- GOOGLE SHEETS CONNECTION ---
@st.cache_resource
def connect_to_gsheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        # Load from Secrets (Clean Logic)
        creds_dict = dict(st.secrets["gcp_service_account"])
        # Fix formatting issues automatically
        if "private_key" in creds_dict:
            key = creds_dict["private_key"]
            key = key.replace("\\n", "\n").replace('"', '')
            if "-----BEGIN PRIVATE KEY-----" not in key:
                 import re
                 clean_key = re.sub(r'[\s\n\r]', '', key)
                 key = f"-----BEGIN PRIVATE KEY-----\n{clean_key}\n-----END PRIVATE KEY-----\n"
            creds_dict["private_key"] = key
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    except:
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
        except:
            return None 

    client = gspread.authorize(creds)
    
    # --- ⚠️ PASTE YOUR SHEET ID HERE ⚠️ ---
    SHEET_ID = "1y04dfrk53yPCm0MNU0OdiUMZlr41GhhxtXfgVDsBuoQ" 
    
    try:
        sheet = client.open_by_key(SHEET_ID)
        return sheet
    except Exception as e:
        return f"Error: {e}"

# --- HELPER FUNCTIONS ---
def get_data(worksheet_name):
    sheet = connect_to_gsheets()
    if not sheet or isinstance(sheet, str): return pd.DataFrame()
    try:
        ws = sheet.worksheet(worksheet_name)
        data = ws.get_all_records()
        return pd.DataFrame(data)
    except:
        return pd.DataFrame() 

def add_row(worksheet_name, row_data):
    sheet = connect_to_gsheets()
    if sheet and not isinstance(sheet, str):
        ws = sheet.worksheet(worksheet_name)
        ws.append_row(row_data)

def delete_row_by_index(worksheet_name, index):
    sheet = connect_to_gsheets()
    if sheet and not isinstance(sheet, str):
        ws = sheet.worksheet(worksheet_name)
        all_rows = ws.get_all_values()
        if index + 1 < len(all_rows):
            del all_rows[index + 1]
            ws.clear()
            ws.update(all_rows)

# --- MAIN APP LOGIC ---
def main():
    # Header Section
    st.markdown("<h1 style='text-align: center; margin-bottom: 5px;'>Our Forever Home 🏡</h1>", unsafe_allow_html=True)
    
    # User Toggle (Styled with columns for centering)
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        user = st.radio("Identity", ["🤴 Husband", "👸 Wife"], horizontal=True, label_visibility="collapsed")
    
    st.write("") # Spacer

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📅 Dates", "✅ Tasks", "💌 Notes"])

    # --- TAB 1: SCHEDULE ---
    with tab1:
        # Input Form inside a Glass Card
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        with st.expander("➕ Plan a Date", expanded=False):
            with st.form("new_event"):
                c1, c2 = st.columns(2)
                with c1: event_date = st.date_input("When?")
                with c2: event_time = st.time_input("Time", value=None)
                event_name = st.text_input("What are we doing?")
                if st.form_submit_button("Save to Calendar"):
                    time_str = event_time.strftime("%H:%M") if event_time else "All Day"
                    add_row("Schedule", [str(event_date), time_str, event_name, user])
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # Display Events
        df_sched = get_data("Schedule")
        if not df_sched.empty:
            df_sched['Date'] = pd.to_datetime(df_sched['Date'])
            df_sched = df_sched.sort_values(by='Date')
            df_sched['Month'] = df_sched['Date'].dt.strftime('%B')
            
            for month, group in df_sched.groupby('Month', sort=False):
                st.markdown(f"<h3 style='margin-top:20px;'>{month}</h3>", unsafe_allow_html=True)
                for i, row in group.iterrows():
                    date_pretty = row['Date'].strftime("%a %d")
                    # Fancy Event Card
                    st.markdown(f"""
                    <div class="glass-card" style="border-left: 8px solid #5A189A; padding: 15px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 24px; font-weight: bold; color: #5A189A;">{date_pretty}</div>
                            <div style="font-size: 14px; color: #888;">⏰ {row['Time']}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 18px; font-weight: 600;">{row['Event']}</div>
                            <div style="font-size: 12px; color: #aaa;">Added by {row['Identity']}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Calendar is empty! Let's plan something. ✈️")

    # --- TAB 2: TASKS ---
    with tab2:
        # Input
        st.markdown('<div class="glass-card" style="padding: 10px;">', unsafe_allow_html=True)
        c1, c2 = st.columns([3, 1])
        with c1: new_task = st.text_input("Task", placeholder="Add a new task...", label_visibility="collapsed")
        with c2: 
            if st.button("Add"):
                if new_task:
                    add_row("Tasks", [new_task, "Pending", user, datetime.datetime.now().strftime("%Y-%m-%d")])
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Display Tasks
        df_tasks = get_data("Tasks")
        if not df_tasks.empty:
            for i, row in df_tasks.iterrows():
                is_done = row['Status'] == "Done"
                opacity = "0.5" if is_done else "1.0"
                decoration = "line-through" if is_done else "none"
                icon = "✅" if is_done else "⬜"
                
                # Custom HTML Task Row
                col_btn, col_txt = st.columns([1, 5])
                with col_btn:
                    if st.button(icon, key=f"t_{i}"):
                        delete_row_by_index("Tasks", i)
                        if not is_done:
                            add_row("Tasks", [row['Task'], "Done", row['Author'], row['Date']])
                        st.rerun()
                
                with col_txt:
                    st.markdown(f"""
                    <div class="glass-card" style="margin-bottom: 0px; padding: 12px; opacity: {opacity}; text-decoration: {decoration};">
                        <b>{row['Task']}</b>
                    </div>
                    """, unsafe_allow_html=True)
        else:
             st.info("Nothing to do! Relax time. ☕")

    # --- TAB 3: NOTES ---
    with tab3:
        # Note Input
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        with st.form("love_note"):
            note = st.text_area("Write a note...", placeholder="I love you because...", height=100)
            if st.form_submit_button("Post Note ❤️"):
                add_row("Notes", [datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), user, note])
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Display Notes
        df_notes = get_data("Notes")
        if not df_notes.empty:
            df_notes = df_notes.iloc[::-1] # Newest first
            for i, row in df_notes.iterrows():
                # Sticky Note Style
                st.markdown(f"""
                <div class="glass-card" style="background: #fff9c4; transform: rotate({(i%3)-1}deg);">
                    <div style="font-size: 12px; color: #888; margin-bottom: 5px; display: flex; justify-content: space-between;">
                        <span>{row['Date']}</span>
                        <span><b>{row['Author']}</b></span>
                    </div>
                    <div style="font-family: 'Indie Flower', cursive; font-size: 18px; color: #333;">
                        {row['Note']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No notes yet. Be the first!")

if __name__ == "__main__":
    main()
