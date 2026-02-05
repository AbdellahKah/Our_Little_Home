import streamlit as st
import pandas as pd
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Our Forever Home", page_icon="🏡", layout="centered")
SECRET_PASSWORD = "1808"

# --- FANCY CSS (Hearts & Flowers + TARGETED BUTTON FIX) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700&family=Pacifico&display=swap');

    /* BACKGROUND */
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

    h1 { font-family: 'Pacifico', cursive; font-size: 3rem !important; color: #5A189A !important; text-shadow: 2px 2px 4px rgba(255,255,255,0.4); margin-bottom: 0px; }
    h3 { font-family: 'Nunito', sans-serif; color: #5A189A !important; font-weight: 700; }
    
    /* CARD STYLING */
    .glass-card { background: rgba(255, 255, 255, 0.6); backdrop-filter: blur(12px); border-radius: 25px; border: 1px solid rgba(255, 255, 255, 0.5); padding: 15px 25px; margin-bottom: 10px; box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.05); }
    
    /* INPUT FIXES */
    div[data-baseweb="base-input"], input.st-be, input.st-bf, input.st-bg { background-color: white !important; border: 2px solid rgba(255,255,255,0.8) !important; border-radius: 12px !important; color: #5A189A !important; }
    div[data-baseweb="input"] { background-color: white !important; border-radius: 12px !important; }
    div[data-baseweb="select"] > div { background-color: white !important; color: #5A189A !important; border-radius: 12px !important; }
    div[data-baseweb="select"] span { color: #5A189A !important; }
    .streamlit-expanderHeader { background-color: rgba(255,255,255,0.6) !important; color: #5A189A !important; border-radius: 12px !important; }
    div.stButton > button { background: linear-gradient(90deg, #FF69B4, #DA70D6) !important; color: white !important; border: none !important; border-radius: 25px; height: 50px; font-size: 18px; font-weight: bold; width: 100%; }
    
    /* --- MAGIC BUTTONS (Targeted Lift) --- */
    /* Target the Edit button specifically using title attribute */
    button[title="Edit"] {
        background: rgba(255, 255, 255, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.8) !important;
        border-radius: 50% !important;
        width: 40px !important;
        height: 40px !important;
        font-size: 16px !important;
        padding: 0 !important;
        line-height: 40px !important;
        color: #5A189A !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        
        /* MOVE IT UP INTO THE CARD */
        position: relative !important;
        top: -105px !important;  /* Physical lift */
        left: -10px !important;
        z-index: 100 !important;
        margin-bottom: -100px !important; /* Remove empty space */
    }

    /* Target the Delete button specifically */
    button[title="Delete"] {
        background: rgba(255, 255, 255, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.8) !important;
        border-radius: 50% !important;
        width: 40px !important;
        height: 40px !important;
        font-size: 16px !important;
        padding: 0 !important;
        line-height: 40px !important;
        color: #D00000 !important; /* Red color for delete */
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        
        /* MOVE IT UP INTO THE CARD */
        position: relative !important;
        top: -105px !important; 
        left: -10px !important;
        z-index: 100 !important;
        margin-bottom: -100px !important; /* Remove empty space */
    }

    button[title="Edit"]:hover, button[title="Delete"]:hover {
        transform: scale(1.1);
        background: #fff !important;
        border-color: #FF69B4 !important;
    }

    .stTabs [data-baseweb="tab-list"] { background-color: rgba(255,255,255,0.4); border-radius: 50px; padding: 8px; gap: 10px; margin-bottom: 20px; }
    .stTabs [data-baseweb="tab"] { height: 40px; border-radius: 40px; background-color: transparent; color: #5A189A; font-weight: 700; border: none; flex-grow: 1; }
    .stTabs [aria-selected="true"] { background-color: #fff !important; color: #FF69B4 !important; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    header, #MainMenu, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- GOOGLE SHEETS CONNECTION ---
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
    SHEET_ID = "1y04dfrk53yPCm0MNU0OdiUMZlr41GhhxtXfgVDsBuoQ"
    try:
        sheet = client.open_by_key(SHEET_ID)
        return sheet
    except Exception as e:
        return None

# --- ROBUST DATA FUNCTIONS ---
def get_data(worksheet_name):
    sheet = connect_to_gsheets()
    if not sheet: return pd.DataFrame()
    try:
        ws = sheet.worksheet(worksheet_name)
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        if not df.empty:
            df.columns = df.columns.str.strip()
        return df
    except:
        return pd.DataFrame() 

def add_row(worksheet_name, row_data):
    sheet = connect_to_gsheets()
    if not sheet:
        st.error("❌ Disconnected. Check Sheet ID.")
        return False
    try:
        ws = sheet.worksheet(worksheet_name)
    except:
        try:
            ws = sheet.add_worksheet(title=worksheet_name, rows=100, cols=10)
            if worksheet_name == "Schedule":
                ws.append_row(["Date", "Time", "Event", "Identity"])
            elif worksheet_name == "Tasks":
                ws.append_row(["Task", "Status", "Author", "Date"])
            elif worksheet_name == "Notes":
                ws.append_row(["Date", "Author", "Note"])
        except Exception as e:
            st.error(f"Error creating sheet: {e}")
            return False

    try:
        ws.append_row(row_data)
        return True
    except Exception as e:
        st.error(f"❌ Error appending data: {e}")
        return False

def delete_specific_row(worksheet_name, row_number):
    sheet = connect_to_gsheets()
    if sheet:
        try:
            ws = sheet.worksheet(worksheet_name)
            ws.delete_rows(row_number)
            return True
        except Exception as e:
            st.error(f"Error deleting: {e}")
            return False

def update_row(worksheet_name, row_number, new_data):
    sheet = connect_to_gsheets()
    if sheet:
        try:
            ws = sheet.worksheet(worksheet_name)
            cell_range = f"A{row_number}:D{row_number}"
            ws.update(cell_range, [new_data]) 
            return True
        except Exception as e:
            st.error(f"Error updating: {e}")
            return False

# --- SCREENS ---
def login_screen():
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>Knock Knock! 🚪</h1>", unsafe_allow_html=True)
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
    # --- CONNECTION CHECK ---
    sheet = connect_to_gsheets()
    if not sheet:
        st.error("⚠️ App cannot connect to Google Sheets.")
        st.warning("Did you replace 'PASTE_YOUR_REAL_ID_HERE' with your actual Sheet ID in the code?")
        return

    st.markdown("<h1 style='text-align: center;'>Our Forever Home 🏡</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 4, 1])
    with c2:
        user = st.radio("Who are you?", ["🤴 Aboudii", "👸 Saratii"], horizontal=True, label_visibility="collapsed")
    st.write("") 
    
    tab1, tab2, tab3 = st.tabs(["📅 Dates", "✅ Tasks", "💌 Notes"])

    # --- TAB 1: DATES ---
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
                        st.toast("Saved!", icon="🎉")
                        time.sleep(1)
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        df = get_data("Schedule")
        if not df.empty and "Date" in df.columns:
            df['sheet_row'] = df.index + 2
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values(by='Date')
            df['Month'] = df['Date'].dt.strftime('%B')
            
            for month, group in df.groupby('Month', sort=False):
                st.markdown(f"<h3 style='margin: 20px 0 10px 0;'>{month}</h3>", unsafe_allow_html=True)
                for i, row in group.iterrows():
                    icon = '🤴' if 'Aboudii' in str(row.get('Identity', '')) else '👸'
                    row_num = row['sheet_row']

                    # 1. RENDER HTML CARD (With Gap for Buttons)
                    # min-width: 110px reserves space for the buttons to land in
                    st.markdown(
                        f"""
                        <div class='glass-card' style='border-left: 8px solid #5A189A; display: flex; align-items: center; justify-content: space-between; height: 90px; padding-right: 10px;'>
                            <div style='flex-grow: 1;'>
                                <div style='font-size: 20px; font-weight: bold; color: #5A189A; line-height: 1.2;'>{row.get('Event', 'Date')}</div>
                                <div style='font-size: 14px; color: #666; margin-top: 4px;'>⏰ {row.get('Time', '')} • {row['Date'].strftime('%a %d')}</div>
                            </div>
                            <div style='min-width: 110px;'></div> <div style='font-size: 28px;'>{icon}</div>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )

                    # 2. RENDER BUTTONS (Targeted via 'help' attribute)
                    # The CSS catches 'button[title="Edit"]' and pulls it up -105px
                    c_spacer, c_edit, c_del, c_emoji_spacer = st.columns([5.5, 0.6, 0.6, 0.8])
                    
                    with c_edit:
                        # IMPORTANT: help="Edit" allows CSS to find this specific button
                        if st.button("✏️", key=f"edit_{row_num}", help="Edit"):
                            st.session_state[f"editing_{row_num}"] = not st.session_state.get(f"editing_{row_num}", False)

                    with c_del:
                        # IMPORTANT: help="Delete" allows CSS to find this specific button
                        if st.button("❌", key=f"del_{row_num}", help="Delete"):
                            delete_specific_row("Schedule", row_num)
                            st.rerun()

                    # 3. EDIT FORM
                    if st.session_state.get(f"editing_{row_num}"):
                        with st.form(key=f"edit_form_{row_num}"):
                            st.caption(f"Editing: {row['Event']}")
                            e_date = st.date_input("New Date", value=row['Date'])
                            try:
                                t_val = datetime.datetime.strptime(row['Time'], "%H:%M").time()
                            except:
                                t_val = None
                            e_time = st.time_input("New Time", value=t_val)
                            e_name = st.text_input("Event Name", value=row['Event'])
                            
                            if st.form_submit_button("Update Event"):
                                new_time_str = e_time.strftime("%H:%M") if e_time else "All Day"
                                update_row("Schedule", row_num, [str(e_date), new_time_str, e_name, row['Identity']])
                                st.session_state[f"editing_{row_num}"] = False
                                st.rerun()

        else:
            st.markdown("<div style='text-align: center; padding: 40px; opacity: 0.7;'><div style='font-size: 60px;'>✈️</div><h3>Nothing planned yet!</h3></div>", unsafe_allow_html=True)

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
        
        df = get_data("Tasks")
        if not df.empty and "Task" in df.columns:
            for i, row in df.iterrows():
                is_done = row.get('Status', '') == "Done"
                opacity, icon = ("0.6", "✅") if is_done else ("1.0", "⬜")
                decoration = "line-through" if is_done else "none"
                col_btn, col_txt = st.columns([1, 5])
                with col_btn:
                    if st.button(icon, key=f"t_{i}"):
                        delete_specific_row("Tasks", i + 2)
                        if not is_done: add_row("Tasks", [row['Task'], "Done", row['Author'], row['Date']])
                        st.rerun()
                with col_txt:
                    st.markdown(f"<div style='background: rgba(255,255,255,0.7); border-radius: 15px; padding: 12px; margin-bottom: 5px; opacity: {opacity}; text-decoration: {decoration};'><span style='font-size: 16px; color: #333; font-weight: 600;'>{row['Task']}</span></div>", unsafe_allow_html=True)
        else:
             st.markdown("<div style='text-align: center; padding: 40px; opacity: 0.7;'><div style='font-size: 60px;'>☕</div><h3>All caught up!</h3></div>", unsafe_allow_html=True)

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
        
        df = get_data("Notes")
        if not df.empty and "Note" in df.columns:
            df = df.iloc[::-1]
            for i, row in df.iterrows():
                rotation = (i % 5) - 2 
                st.markdown(f"<div class='glass-card' style='background: #fff9c4; transform: rotate({rotation}deg); border: none; margin-bottom: 25px;'><div style='font-size: 12px; color: #888; margin-bottom: 8px; display: flex; justify-content: space-between; border-bottom: 1px dashed #ccc; padding-bottom: 5px;'><span>{row.get('Date','')}</span><span><b>{row.get('Author','')}</b></span></div><div style='font-family: \"Indie Flower\", cursive; font-size: 18px; color: #333; line-height: 1.4;'>{row['Note']}</div></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='text-align: center; padding: 40px; opacity: 0.7;'><div style='font-size: 60px;'>💌</div><h3>No notes yet.</h3></div>", unsafe_allow_html=True)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    login_screen()
else:
    main_app()
