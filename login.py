import streamlit as st
st.set_page_config(page_title="TGSRTC AI DASHBOARD", layout="wide")

import json
import pandas as pd
import base64
import time
from datetime import datetime

from auth import (
    authenticate_user,
    create_user,
    ensure_admin_exists,
    get_role_by_userid,
    get_depot_by_userid,
    fetch_depot_names,
    is_authenticated,
    logout,
    now_ist
)

# Import your modules
from Input_Data_DM import user_sheet

# ORM imports
from db_config import get_session
from models import TSAdmin, User

# ------------------- LOAD CONFIG -------------------
with open("config.json") as f:
    config = json.load(f)
logo_path = config["logo_path"]

# ------------------- ENSURE ADMIN -------------------
ensure_admin_exists()

# ------------------- SESSION INIT -------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.userid = ""
    st.session_state.user_role = None
    st.session_state.user_depot = None
    st.session_state.user_region = None

# ------------------- SESSION FEEDBACK -------------------
if st.session_state.get("session_expired"):
    st.warning("⚠️ Your session has expired. Please log in again.")
    time.sleep(1.5)
    st.session_state["session_expired"] = False
    st.rerun()
elif st.session_state.get("manual_logout"):
    st.info("✅ You have been logged out safely.")
    time.sleep(1.5)
    st.session_state["manual_logout"] = False
    st.rerun()

# ------------------- LOGIN SCREEN -------------------
if not st.session_state.logged_in or not is_authenticated():
    with open(logo_path, "rb") as img_file:
        b64_img = base64.b64encode(img_file.read()).decode()

    st.markdown(f"""
        <div style="text-align: center; background-color: #19bc9c; border-radius: 100px 20px;">
            <br>
            <img src="data:image/png;base64,{b64_img}" width="150" height="150">
            <h1 style="color: white;">Telangana State Road Transport Corporation</h1>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
        .stTextInput>div>div>input { background-color: #e4e4e4; color: black; }
        .login-btn button {
            background-color: #F63366 !important;
            color: white !important;
            font-weight: bold;
        }
    </style>
    """, unsafe_allow_html=True)

    # Login Form
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            userid = st.text_input("User ID", max_chars=30)
            user_depot_display = get_depot_by_userid(userid) if userid else None
            role = get_role_by_userid(userid) if userid else None
            password = st.text_input("Password", type="password", max_chars=30)

            st.text_input("Role", value=role or "(Role will appear here)", disabled=True)
            st.text_input("Depot/Region", value=user_depot_display or "(Depot/Region will appear here)", disabled=True)

    # Login Button
    login_col = st.columns([1, 2, 1])[1]
    with login_col:
        if st.button("🔐 Login", key="login_button"):
            success, depot, lock_until = authenticate_user(userid, password)
            if success:
                st.session_state.logged_in = True
                st.session_state.userid = userid
                role_from_db = get_role_by_userid(userid)
                st.session_state.user_role = role_from_db

                if role_from_db == "Depot Manager(DMs)":
                    st.session_state.user_depot = depot
                elif role_from_db == "Regional Manager(RMs)":
                    st.session_state.user_region = depot
                else:
                    st.session_state.user_depot = None
                    st.session_state.user_region = None

                st.rerun()
            else:
                if lock_until:
                    remaining = (lock_until - now_ist()).total_seconds() / 60
                    mins_left = max(1, int(remaining))
                    unlock_time = lock_until.strftime("%I:%M %p")
                    st.warning(
                        f"🔒 **Account locked** — Try again in {mins_left} minute(s) "
                        f"(unlocks at **{unlock_time} IST**)."
                    )
                else:
                    st.error("❌ Invalid User ID or Password.")
                time.sleep(1.5)

# ------------------- MAIN APP AFTER LOGIN -------------------
else:
    st.markdown(f"""
    <style>
    @keyframes fadeout {{
        0%   {{ opacity: 1; }}
        80%  {{ opacity: 1; }}
        100% {{ opacity: 0; display: none; }}
    }}
    #welcome {{
        padding: 1rem;
        background-color: #2ecc71;
        color: white;
        text-align: center;
        border-radius: 8px;
        font-size: 18px;
        font-weight: bold;
        animation: fadeout 2s forwards;
    }}
    </style>
    <div id="welcome">👋 Welcome, {st.session_state.userid}</div>
    """, unsafe_allow_html=True)

    # Sidebar logout
    with st.sidebar:
        if st.button("🚪 Logout"):
            logout(manual=True)
            st.session_state.logged_in = False
            st.rerun()

    # ------------------- ROLES -------------------
    else:
        role = st.session_state.user_role
        if role == "Depot Manager(DMs)":
            menu = [
                "Daily Depot Input Sheet",
              
            ]
            selection = st.sidebar.selectbox("Select Screen", menu)
            if selection == "Daily Depot Input Sheet":
                user_sheet(st.session_state.user_depot, role)
           
