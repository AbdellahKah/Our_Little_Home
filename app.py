import streamlit as st
import pandas as pd
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="Our Forever Home", page_icon="🏡", layout="centered")
SECRET_PASSWORD = "1808"

# --- FANCY CSS (Hearts & Flowers + Mobile Fixes) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700&family=Pacifico&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Indie+Flower&display=swap');

    /* 1. MOBILE BASICS */
    * { -webkit-tap-highlight-color: transparent; }
    input, textarea, select { font-size: 16px !important; }

    /* 2. BACKGROUND: Hearts + Flowers + Gradient (RESTORED) */
    .stApp {
        background-image: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M30 53.65L25.65 49.65C10.25 35.45 0 26.05 0 14.55C0 5.15 7.35 -2.2 16.75 -2.2C22.05 -2.2 27.15 4.7 30 10.65C32.85 4.7 37.95 -2.2 43.25 -2.2C52.65 -2.2 60 5.15 60 14.55C60 26.05 49.75 35.45 34.35 49.65L30 53.65Z' fill='%23ffffff' fill-opacity='0.15'/%3E%3C/svg%3E"),
        url("data:image/svg+xml,%3Csvg width='50' height='50' viewBox='0 0 50 50' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M25 1C21.7 1 18.9 3.4 18.4 6.6C15.2 5.1 11.5 6.4 9.5 9.5C7.5 12.5 8 16.6 10.7 19.1C7.8 20.6 6.3 23.9 7.1 27.1C7.9 30.4 10.8 32.6 14.1 32.6C14.1 36.1 16.3 38.9 19.6 39.7C22.9 40.4 26.1 39 27.7 36.1C30.4 38.6 34.4 39.1 37.5 37.1C40.6 35.1 41.8 31.4 40.4 28.2C43.6 27.8 46 25 46 21.6C46 18.2 43.6 15.4 40.4 15C41.8 11.8 40.6 8.1 37.5 6.1C34.4 4.1 30.4 4.6 27.7 7.1C27.2 3.9 24.4 1 21.1 1L25 1Z' fill='%23ffffff' fill-opacity='0.1'/%3E%3C/svg%3E"),
        linear-gradient(-45deg, #ff9a9e, #fad0c4, #fad0c4, #fbc2eb);
        background-size: 100px 100px, 80px 80px, 400% 400%;
        background-position: 0 0, 40px 40px, 0% 50%;
        animation: gradient 15s ease infinite;
        font-family: 'Nunito', sans-serif;
    }
    @keyframes gradient {
        0% { background-position: 0 0, 40px 40px, 0% 50%; }
        50% { background-position: 0 0, 40px 40px, 100% 50%; }
        100% { background-position: 0 0, 40px 40px, 0% 50%; }
    }

    /* 3. TYPOGRAPHY */
    h1 { font-family: 'Pacifico', cursive; font-size: 2.2rem !important; color: #5A189A !important; text-align: center; text-shadow: 2px 2px 4px rgba(255,255,255,0.4); margin-top: -20px; }
    h3 { font-family: 'Nunito', sans-serif; color: #5A189A !important; font-weight: 700; font-size: 1.2rem; }

    /* 4. CARDS */
    .glass-card { 
        background: rgba(255, 255, 255, 0.7); 
        backdrop-filter: blur(12px); 
        border-radius: 20px; 
        border: 1px solid rgba(255, 255, 255, 0.5); 
        padding: 15px; 
        margin-bottom: 10px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); 
    }

    /* 5. BUTTONS */
    div.stButton > button { 
        background: linear-gradient(90deg, #FF69B4, #DA70D6) !important; 
        color: white !important; 
        border: none !important; 
        border-radius: 25px; 
        height: 50px; 
        font-size: 18px; 
        font-weight: bold; 
        width: 100%; 
    }
    
    /* 6. EDIT/DELETE BUTTONS (Fixed Placement) */
    div[data-testid="column"] button {
        background: rgba(255,255,255,0.6) !important;
        border: 1px solid rgba(255,255,255,0.8) !important;
        height: 40px;
        width: 100%; /* Fill column width */
        border-radius: 12px;
        font-size: 18px;
        padding: 0;
        margin-top: 15px; /* Pushes button down to align with text */
    }
    div[data-testid="column"] button:hover {
        background: white !important;
        border-color: #5A189A !important;
    }

    /* TABS */
    .stTabs [data-baseweb="tab-list"] { background-color: rgba(255,255,255,0.4); border-radius: 50px; padding: 5px; gap: 5px; }
    .stTabs [data-baseweb="tab"] { height: 45px; border-radius: 40px; background-color: transparent; color: #5A189A; font-weight: 700; border: none; flex-grow: 1; }
    .stTabs [aria-selected="true"] { background-color: #fff !important; color: #FF69B4 !important; }

    header, #MainMenu, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- GOOGLE SHEETS CONNECTION ---
def connect_to_gsheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            # 👇👇👇 YOUR SHEET ID 👇👇👇
            return gspread.authorize(creds).open_by_key("1y04dfrk53yPCm0MNU0OdiUMZlr41GhhxtXfgVDsBuoQ")
    except:
        pass
    try:
        if os.path.exists("service_account.json"):
            creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
            return gspread.authorize(creds).open_by_key("1y04dfrk53yPCm0MNU0OdiUMZlr41GhhxtXfgVDsBuoQ")
    except:
        return None
    return None

# --- FUNCTIONS ---
def get_data(worksheet_name):
    sheet = connect_to_gsheets()
    if not sheet: return pd.DataFrame()
    try:
        ws = sheet.worksheet(worksheet_name)
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        if not df.empty: df.columns = df.columns.str.strip()
        return df
    except: return pd.DataFrame() 

def add_row(worksheet_name, row_data):
    sheet = connect_to_gsheets()
    if not sheet: return False
    try:
        try: ws = sheet.worksheet(worksheet_name)
        except: 
            ws = sheet.add_worksheet(title=worksheet_name, rows=100, cols=10)
            if worksheet_name == "Schedule": ws.append_row(["Date", "Time", "Event", "Identity"])
            elif worksheet_name == "Tasks": ws.append_row(["Task", "Status", "Author", "Date"])
            elif worksheet_name == "Notes": ws.append_row(["Date", "Author", "Note"])
        ws.append_row(row_data)
        return True
    except: return False

def delete_specific_row(worksheet_name, row_number):
    sheet = connect_to_gsheets()
    if sheet:
        try: sheet.worksheet(worksheet_name).delete_rows(row_number); return True
        except: return False

def update_row(worksheet_name, row_number, new_data):
    sheet = connect_to_gsheets()
    if sheet:
        try: sheet.worksheet(worksheet_name).update(f"A{row_number}:D{row_number}", [new_data]); return True
        except: return False

# --- UI ---
def login_screen():
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>Knock Knock! 🚪</h1>", unsafe_allow_html=True)
    st.write("") 
    with st.form("login_form"):
        password = st.text_input("Enter the Secret Key:", type="password", placeholder="Shhh...")
        if st.form_submit_button("Open Door 🔑", use_container_width=True):
            if password == SECRET_PASSWORD:
                st.session_state.authenticated = True
                st.balloons()
                st.rerun()
            else:
                st.error("Wrong key!")

def main_app():
    st.markdown("<h1 style='text-align: center;'>Our Forever Home 🏡</h1>", unsafe_allow_html=True)
    user = st.radio("Who are you?", ["🤴 Aboudii", "👸 Saratii"], horizontal=True, label_visibility="collapsed")
    st.write("") 
    
    tab1, tab2, tab3 = st.tabs(["📅 Dates", "✅ Tasks", "💌 Notes"])

    # --- TAB 1: DATES ---
    with tab1:
        with st.expander("➕ Plan a New Date", expanded=False):
            with st.form("new_event"):
                c1, c2 = st.columns(2)
                with c1: event_date = st.date_input("When?")
                with c2: event_time = st.time_input("Time", value=None)
                event_name = st.text_input("What is the plan?")
                if st.form_submit_button("Save to Calendar"):
                    time_str = event_time.strftime("%H:%M") if event_time else "All Day"
                    add_row("Schedule", [str(event_date), time_str, event_name, user])
                    st.toast("Saved!", icon="🎉")
                    time.sleep(1)
                    st.rerun()
        
        df = get_data("Schedule")
        if not df.empty and "Date" in df.columns:
            df['sheet_row'] = df.index + 2
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values(by='Date')
            df['Month'] = df['Date'].dt.strftime('%B')
            
            for month, group in df.groupby('Month', sort=False):
                st.markdown(f"<h3 style='margin: 15px 0 5px 0; padding-left: 5px;'>{month}</h3>", unsafe_allow_html=True)
                for i, row in group.iterrows():
                    icon = '🤴' if 'Aboudii' in str(row.get('Identity', '')) else '👸'
                    row_num = row['sheet_row']

                    # --- ROW CONTAINER START ---
                    with st.container():
                        # RESTORED: 3-Column Layout (Text | Edit | Delete)
                        # Ratios: 5 (Text) : 0.8 (Edit) : 0.8 (Delete)
                        c_text, c_edit, c_del = st.columns([5, 0.8, 0.8])
                        
                        with c_text:
                            st.markdown(
                                f"""
                                <div class='glass-card' style='border-left: 6px solid #5A189A; padding: 12px; margin-bottom: 5px; height: 100%;'>
                                    <div style='display: flex; justify-content: space-between; align-items: flex-start;'>
                                        <div>
                                            <div style='font-size: 18px; font-weight: bold; color: #5A189A; line-height: 1.2;'>{row.get('Event', 'Date')}</div>
                                            <div style='font-size: 13px; color: #666; margin-top: 4px;'>
                                                📅 {row['Date'].strftime('%a %d')} &nbsp; ⏰ {row.get('Time', '')}
                                            </div>
                                        </div>
                                        <div style='font-size: 22px; padding-left: 10px;'>{icon}</div>
                                    </div>
                                </div>
                                """, 
                                unsafe_allow_html=True
                            )
                        
                        with c_edit:
                            if st.button("✏️", key=f"e_{row_num}"):
                                st.session_state[f"editing_{row_num}"] = not st.session_state.get(f"editing_{row_num}", False)

                        with c_del:
                            if st.button("❌", key=f"d_{row_num}"):
                                delete_specific_row("Schedule", row_num)
                                st.rerun()
                    # --- ROW CONTAINER END ---

                    # Edit Form
                    if st.session_state.get(f"editing_{row_num}"):
                        with st.form(key=f"edit_form_{row_num}"):
                            st.caption(f"Editing: {row['Event']}")
                            e_date = st.date_input("Date", value=row['Date'])
                            try: t_val = datetime.datetime.strptime(row['Time'], "%H:%M").time()
                            except: t_val = None
                            e_time = st.time_input("Time", value=t_val)
                            e_name = st.text_input("Event", value=row['Event'])
                            
                            if st.form_submit_button("Update"):
                                new_time_str = e_time.strftime("%H:%M") if e_time else "All Day"
                                update_row("Schedule", row_num, [str(e_date), new_time_str, e_name, row['Identity']])
                                st.session_state[f"editing_{row_num}"] = False
                                st.rerun()
        else:
             st.info("No dates yet! Add one above.")

    # --- TAB 2: TASKS ---
    with tab2:
        with st.form("task_form", clear_on_submit=True):
            c1, c2 = st.columns([3, 1])
            with c1: new_task = st.text_input("Task", placeholder="Buy milk...", label_visibility="collapsed")
            with c2: 
                if st.form_submit_button("Add") and new_task:
                    add_row("Tasks", [new_task, "Pending", user, datetime.datetime.now().strftime("%Y-%m-%d")])
                    st.rerun()
        
        df = get_data("Tasks")
        if not df.empty and "Task" in df.columns:
            for i, row in df.iterrows():
                is_done = row.get('Status', '') == "Done"
                bg_color = "rgba(255,255,255,0.4)" if is_done else "rgba(255,255,255,0.85)"
                txt_deco = "line-through" if is_done else "none"
                
                # Checkbox | Text Layout
                c_check, c_txt = st.columns([1, 5])
                with c_check:
                    btn_label = "✅" if is_done else "⬜"
                    if st.button(btn_label, key=f"tick_{i}"):
                        delete_specific_row("Tasks", i + 2)
                        if not is_done: add_row("Tasks", [row['Task'], "Done", row['Author'], row['Date']])
                        st.rerun()
                with c_txt:
                    st.markdown(f"<div style='background: {bg_color}; border-radius: 12px; padding: 12px; opacity: 1; min-height: 45px; display: flex; align-items: center;'><span style='font-size: 16px; color: #333; text-decoration: {txt_deco}; font-weight: 600;'>{row['Task']}</span></div>", unsafe_allow_html=True)
        else: st.info("No tasks! You are free! 🕊️")

    # --- TAB 3: NOTES ---
    with tab3:
        with st.form("love_note"):
            note = st.text_area("Note", placeholder="Write something sweet...", height=100, label_visibility="collapsed")
            if st.form_submit_button("Post Note ❤️"):
                add_row("Notes", [datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), user, note])
                st.rerun()
        
        df = get_data("Notes")
        if not df.empty and "Note" in df.columns:
            df = df.iloc[::-1]
            for i, row in df.iterrows():
                rotation = (i % 3) - 1.5
                st.markdown(f"<div class='glass-card' style='background: #fff9c4; transform: rotate({rotation}deg); border: none; margin-top: 10px;'><div style='font-size: 11px; color: #888; margin-bottom: 5px; display: flex; justify-content: space-between; border-bottom: 1px dashed #bbb; padding-bottom: 4px;'><span>{row.get('Date','')}</span><span style='color: #5A189A;'><b>{row.get('Author','')}</b></span></div><div style='font-family: \"Indie Flower\", cursive; font-size: 20px; color: #333; line-height: 1.3;'>{row['Note']}</div></div>", unsafe_allow_html=True)

if "authenticated" not in st.session_state: st.session_state.authenticated = False
if not st.session_state.authenticated: login_screen()
else: main_app()
