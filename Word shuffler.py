import streamlit as st
import random
import re
import json
import os
import time

# --- CẤU HÌNH HỆ THỐNG ---
DB_FILE = "game_state.json"
PASSWORD_TEACHER = "123456" # Bạn có thể đổi mật khẩu ở đây

def load_state():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: return json.load(f)
    return {"sentence": "", "status": "waiting", "results": []}

def save_state(state):
    with open(DB_FILE, "w") as f: json.dump(state, f)

# Khởi tạo session_state cá nhân
if 'user_role' not in st.session_state: st.session_state.user_role = None
if 'nickname' not in st.session_state: st.session_state.nickname = ""
if 'placed_words' not in st.session_state: st.session_state.placed_words = []
if 'available_words' not in st.session_state: st.session_state.available_words = []

# --- CSS: Giao diện Block ---
st.markdown("""
<style>
    .placeholder { border: 2px dashed #bbb; border-radius: 10px; padding: 15px; min-width: 80px; min-height: 40px; display: inline-block; margin: 5px; background: #f9f9f9; }
    .word-block { background: #FFEB3B; border: 2px solid #FBC02D; border-radius: 8px; padding: 10px 20px; font-weight: bold; cursor: pointer; display: inline-block; margin: 5px; }
    .stButton button { width: 100%; }
</style>
""", unsafe_allow_html=True)

# --- TRANG 1: CHỌN TƯ CÁCH ---
if st.session_state.user_role is None:
    st.title("Welcome to Word Shuffler")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Join as Student"):
            st.session_state.temp_role = "Student"
    with col2:
        if st.button("Join as Teacher"):
            st.session_state.temp_role = "Teacher"

    if 'temp_role' in st.session_state:
        if st.session_state.temp_role == "Student":
            nick = st.text_input("Please input nickname (English characters only):")
            if st.button("Confirm Student"):
                if re.match("^[a-zA-Z0-9 ]+$", nick):
                    st.session_state.nickname = nick
                    st.session_state.user_role = "Student"
                    st.rerun()
                else: st.error("Invalid nickname! Please use English characters only.")
        
        else:
            pwd = st.text_input("Please input password:", type="password")
            if st.button("Confirm Teacher") or (pwd and pwd == PASSWORD_TEACHER):
                if pwd == PASSWORD_TEACHER:
                    st.session_state.user_role = "Teacher"
                    st.rerun()
                else: st.error("Wrong password!")

# --- TRANG 2: MÀN HÌNH CHÍNH ---
else:
    state = load_state()

    # --- GIAO DIỆN HỌC SINH ---
    if st.session_state.user_role == "Student":
        if state["status"] == "waiting":
            st.header(f"Hello, {st.session_state.nickname}!")
            st.info("Please wait for the teacher to send a sentence...")
            time.sleep(2)
            st.rerun()
        
        elif state["status"] == "playing":
            # Nếu mới bắt đầu game, xáo trộn từ
            if not st.session_state.available_words and not st.session_state.placed_words:
                words = state["sentence"].split()
                random.shuffle(words)
                st.session_state.available_words = words

            st.write("### Reorder the sentence:")
            
            # Khu vực ô mờ (Placeholder)
            st.write("Your Answer:")
            cols_p = st.container()
            with cols_p:
                if not st.session_state.placed_words:
                    st.markdown('<div class="placeholder">...</div>', unsafe_allow_html=True)
                for i, w in enumerate(st.session_state.placed_words):
                    if st.button(w, key=f"placed_{i}"):
                        st.session_state.available_words.append(w)
                        st.session_state.placed_words.pop(i)
                        st.rerun()

            st.write("---")
            # Khu vực block từ để chọn
            st.write("Available Words:")
            for i, w in enumerate(st.session_state.available_words):
                if st.button(w, key=f"avail_{i}"):
                    st.session_state.placed_words.append(w)
                    st.session_state.available_words.pop(i)
                    st.rerun()

            if st.button("Confirm Submission", type="primary"):
                final_ans = " ".join(st.session_state.placed_words)
                state["results"].append({"name": st.session_state.nickname, "answer": final_ans, "time": time.time()})
                save_state(state)
                st.session_state.submitted = True
                st.success("Submitted! Please wait for others.")
                st.session_state.available_words = [] # Lock screen

        elif state["status"] == "ended":
            st.write("# Finished!")
            st.write("Please wait for teacher to restart.")
            time.sleep(3)
            st.rerun()

    # --- GIAO DIỆN GIÁO VIÊN ---
    elif st.session_state.user_role == "Teacher":
        st.header("Teacher Dashboard")
        
        if state["status"] == "waiting":
            input_sent = st.text_area("Input sentence for students:")
            if st.button("Send to Students") and input_sent:
                state["sentence"] = input_sent
                state["status"] = "playing"
                state["results"] = []
                save_state(state)
                st.rerun()
        
        elif state["status"] == "playing":
            st.subheader("Leaderboard (Submissions)")
            results = state["results"]
            for i, res in enumerate(results):
                st.write(f"{i+1}. {res['name']} - Submitted")
            
            if st.button("End Session & Collect Answers"):
                state["status"] = "ended"
                save_state(state)
                st.rerun()

        elif state["status"] == "ended":
            st.subheader("Final Results")
            # Sắp xếp theo thời gian nộp
            sorted_res = sorted(state["results"], key=lambda x: x['time'])
            for i, res in enumerate(sorted_res):
                st.write(f"**Rank {i+1}: {res['name']}**")
                st.code(res['answer'])
            
            if st.button("Reset Game (Back to Page 1)"):
                save_state({"sentence": "", "status": "waiting", "results": []})
                st.session_state.user_role = None
                st.rerun()