import streamlit as st
import pandas as pd
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Our Forever Home", page_icon="🏡", layout="centered")

# --- PASSWORD ---
SECRET_PASSWORD = "1808"

# --- FANCY CSS (Nuclear Fix) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700&family=Pacifico&display=swap');
    .stApp { background: linear-gradient(-45deg, #ff9a9e, #fad0c4, #fad0c4, #fbc2eb); background-size: 400% 400%; animation: gradient 15s ease infinite; font-family: 'Nunito', sans-serif; }
    h1 { font-family: 'Pacifico', cursive; font-size: 3rem !important; color: #5A189A !important; text-shadow: 2px 2px 4px rgba(255,255,255,0.4); margin-bottom: 0px; }
    h3 { font-family: 'Nunito', sans-serif; color: #5A189A !important; font-weight: 700; }
    .glass-card { background: rgba(255, 255, 255, 0.5); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border-radius: 25px; border: 1px solid rgba(255, 255, 255, 0.5); padding: 25px; margin-bottom: 20px; box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.05); }
    div[data-baseweb="base-input"], input.st-be, input.st-bf, input.st-bg { background-color: white !important; border: 2px solid rgba(255,255,255,0.8) !important; border-radius: 12px !important; color: #5A189A !important; }
    div[data-baseweb="input"] { background-color: white !important; border-radius: 12px !important; }
    div[data-baseweb="select"] > div { background-color: white !important; color: #5A189A !important; border-radius: 12px !important; }
    div[data-baseweb="select"] span { color: #5A189A !important; }
    .streamlit-expanderHeader { background-color: rgba(255,255,255,0.6) !important; color: #5A189A !important; border-radius: 12px !important; }
    div.stButton > button { background: linear-gradient(90deg, #FF69B4, #DA70D6) !important; color: white !important; border: none !important; border-radius: 25px; height: 50px; font-size: 18px; font-weight: bold; width: 100%; }
    .stTabs [data-baseweb="tab-list"] { background-color: rgba(255,255,255,0.4); border-radius: 50px; padding: 8px; gap: 10px; margin-bottom: 20px; }
    .stTabs [data-baseweb="tab"] { height: 40px; border-radius: 40px; background-color: transparent; color: #5A189A; font-weight: 700; border: none; flex-grow: 1; }
    .stTabs [aria-selected="true"] { background-color: #fff !important; color: #FF69B4 !important; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    header, #MainMenu, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- GOOGLE SHEETS CONNECTION (With Auto-Refresh) ---
# ttl=60 means "refresh the connection every 60 seconds" to find new tabs
@st.cache_resource(ttl=60)
def connect_to_gsheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
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
    # THIS ID MUST MATCH YOUR BROWSER URL
    SHEET_ID = "1y04dfrk53yPCm0MNU0OdiUMZlr41GhhxtXfgVDsBuoQ"
    
    try:
        sheet = client.open_by_key(SHEET_ID)
        return sheet
    except Exception as e:
        return str(e)

# --- DATA FUNCTIONS ---
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
    
    if not sheet:
        st.error("❌ Disconnected. Check Secrets.")
        return False
    if isinstance(sheet, str):
        st.error(f"❌ Connection Error: {sheet}")
        return False

    try:
        ws = sheet.worksheet(worksheet_name)
        ws.append_row(row_data)
        return True
    except gspread.WorksheetNotFound:
        # --- DEBUG MODE ---
        # This will tell you EXACTLY what tabs the app sees
        try:
            existing_tabs = [ws.title for ws in sheet.worksheets()]
            st.error(f"❌ Error: Tab '{worksheet_name}' missing. I found these instead: {existing_tabs}")
            st.info(f"💡 Tip: Do you see a space in the name? Like '{worksheet_name} '?")
        except:
             st.error(f"❌ Error: Tab '{worksheet_name}' not found.")
        return False
    except Exception as e:
        st.error(f"❌ Save Error: {e}")
        return False

def delete_row_by_index(worksheet_name, index):
    sheet = connect_to_gsheets()
    if sheet and not isinstance(sheet, str):
        try:
            ws = sheet.worksheet(worksheet_name)
            all_rows = ws.get_all_values()
            if index + 1 < len(all_rows):
                del all_rows[index + 1]
                ws.clear()
                ws.update(all_rows)
        except:
            pass

# --- SCREENS ---
def login_screen():
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>Knock Knock! 🚪</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>This is our private little space.</p>", unsafe_allow_html=True)
    st.write("") 
    c1, c2, c3 = st.columns([1, 2, 1]) 
    with c2:
        password = st.text_input("Enter the Secret Key:", type="password", placeholder="Shhh...")
        st.write("") 
        if st.button("Open Door 🔑", use_container_width=True):
            if password == SECRET_PASSWORD:
                st.session_state.authenticated = True
                st.balloons()
                st.rerun()
            else:
                st.error("Wrong key! Are you a stranger? 😜")

def main_app():
    st.markdown("<h1 style='text-align: center;'>Our Forever Home 🏡</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 4, 1])
    with c2:
        user = st.radio("Who are you?", ["🤴 Husband", "👸 Wife"], horizontal=True, label_visibility="collapsed")
    st.write("") 
    
    tab1, tab2, tab3 = st.tabs(["📅 Dates", "✅ Tasks", "💌 Notes"])

    # --- TAB 1: SCHEDULE ---
    with tab1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        with st.expander("➕ Plan a New Date", expanded=False):
            with st.form("new_event"):
                c1, c2 = st.columns(2)
                with c1: event_date = st.date_input("When?")
                with c2: event_time = st.time_input("Time", value=None)
                event_name = st.text_input("What is the plan?")
                st.write("") 
                
                if st.form_submit_button("Save to Calendar"):
                    time_str = event_time.strftime("%H:%M") if event_time else "All Day"
                    success = add_row("Schedule", [str(event_date), time_str, event_name, user])
                    if success:
                        st.toast("Saved! Refreshing...", icon="🎉")
                        time.sleep(1)
                        st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        df_sched = get_data("Schedule")
        if not df_sched.empty:
            df_sched['Date'] = pd.to_datetime(df_sched['Date'])
            df_sched = df_sched.sort_values(by='Date')
            df_sched['Month'] = df_sched['Date'].dt.strftime('%B')
            for month, group in df_sched.groupby('Month', sort=False):
                st.markdown(f"<h3 style='margin: 20px 0 10px 0;'>{month}</h3>", unsafe_allow_html=True)
                for i, row in group.iterrows():
                    date_pretty = row['Date'].strftime("%a %d")
                    st.markdown(f"""
                    <div class="glass-card" style="border-left: 8px solid #5A189A; padding: 15px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <div style="flex-grow: 1;">
                            <div style="font-size: 20px; font-weight: bold; color: #5A189A;">{row['Event']}</div>
                            <div style="font-size: 14px; color: #666;">⏰ {row['Time']} • {date_pretty}</div>
                        </div>
                        <div style="text-align: right; min-width: 60px;">
                             <div style="font-size: 24px;">{ '🤴' if 'Husband' in row['Identity'] else '👸' }</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("<div style='text-align: center; padding: 40px; opacity: 0.7;'><div style='font-size: 60px;'>✈️</div><h3>Nothing planned yet!</h3><p>Click the <b>+</b> above to add a date.</p></div>", unsafe_allow_html=True)

    # --- TAB 2: TASKS ---
    with tab2:
        st.markdown('<div class="glass-card" style="padding: 15px;">', unsafe_allow_html=True)
        c1, c2 = st.columns([4, 1])
        with c1: new_task = st.text_input("Task", placeholder="Add a new task...", label_visibility="collapsed")
        with c2: 
            if st.button("Add"):
                if new_task:
                    success = add_row("Tasks", [new_task, "Pending", user, datetime.datetime.now().strftime("%Y-%m-%d")])
                    if success: st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        df_tasks = get_data("Tasks")
        if not df_tasks.empty:
            for i, row in df_tasks.iterrows():
                is_done = row['Status'] == "Done"
                opacity, icon = ("0.6", "✅") if is_done else ("1.0", "⬜")
                decoration = "line-through" if is_done else "none"
                col_btn, col_txt = st.columns([1, 5])
                with col_btn:
                    if st.button(icon, key=f"t_{i}"):
                        delete_row_by_index("Tasks", i)
                        if not is_done: add_row("Tasks", [row['Task'], "Done", row['Author'], row['Date']])
                        st.rerun()
                with col_txt:
                    st.markdown(f"<div style='background: rgba(255,255,255,0.7); border-radius: 15px; padding: 12px; margin-bottom: 5px; opacity: {opacity}; text-decoration: {decoration}; box-shadow: 0 2px 5px rgba(0,0,0,0.05);'><span style='font-size: 16px; color: #333; font-weight: 600;'>{row['Task']}</span></div>", unsafe_allow_html=True)
        else:
             st.markdown("<div style='text-align: center; padding: 40px; opacity: 0.7;'><div style='font-size: 60px;'>☕</div><h3>All caught up!</h3><p>Relax time.</p></div>", unsafe_allow_html=True)

    # --- TAB 3: NOTES ---
    with tab3:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        with st.form("love_note"):
            note = st.text_area("Write a note...", placeholder="I love you because...", height=100)
            if st.form_submit_button("Post Note ❤️"):
                success = add_row("Notes", [datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), user, note])
                if success:
                    st.toast("Posted!", icon="💌")
                    time.sleep(1)
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        df_notes = get_data("Notes")
        if not df_notes.empty:
            df_notes = df_notes.iloc[::-1]
            for i, row in df_notes.iterrows():
                rotation = (i % 5) - 2 
                st.markdown(f"<div class='glass-card' style='background: #fff9c4; transform: rotate({rotation}deg); border: none; margin-bottom: 25px;'><div style='font-size: 12px; color: #888; margin-bottom: 8px; display: flex; justify-content: space-between; border-bottom: 1px dashed #ccc; padding-bottom: 5px;'><span>{row['Date']}</span><span><b>{row['Author']}</b></span></div><div style='font-family: \"Indie Flower\", cursive; font-size: 18px; color: #333; line-height: 1.4;'>{row['Note']}</div></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='text-align: center; padding: 40px; opacity: 0.7;'><div style='font-size: 60px;'>💌</div><h3>No notes yet.</h3><p>Be the first to write something sweet!</p></div>", unsafe_allow_html=True)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    login_screen()
else:
    main_app()

