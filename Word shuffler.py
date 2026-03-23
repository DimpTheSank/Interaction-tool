import streamlit as st
import random
import re
import json
import os
import time

# --- CẤU HÌNH HỆ THỐNG ---
DB_FILE = "game_state.json"
PASSWORD_TEACHER = "123456"

def load_state():
    # Cấu trúc mặc định đầy đủ các phím
    default_state = {"sentence": "", "status": "waiting", "results": [], "question_id": 0}
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: 
                data = json.load(f)
                # Kiểm tra và bổ sung các key thiếu từ file cũ
                for key, value in default_state.items():
                    if key not in data:
                        data[key] = value
                return data
        except:
            pass
    return default_state

def save_state(state):
    with open(DB_FILE, "w") as f: 
        json.dump(state, f)

# Khởi tạo session_state cá nhân
if 'user_role' not in st.session_state: st.session_state.user_role = None
if 'nickname' not in st.session_state: st.session_state.nickname = ""
if 'placed_words' not in st.session_state: st.session_state.placed_words = []
if 'available_words' not in st.session_state: st.session_state.available_words = []
if 'last_question_id' not in st.session_state: st.session_state.last_question_id = -1
if 'submitted' not in st.session_state: st.session_state.submitted = False

# --- CSS: Giao diện Block ---
st.markdown("""
<style>
    .placeholder-container { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; margin-bottom: 30px; min-height: 80px; padding: 20px; border: 3px dashed #bbb; border-radius: 15px; background: #fdfdfd; }
    .word-block { background: #FFEB3B; border: 3px solid #FBC02D; border-radius: 12px; padding: 15px 25px; font-weight: bold; font-size: 24px; cursor: pointer; box-shadow: 4px 4px 0px #ddd; display: inline-block; }
    .rank-card { padding: 12px; border-radius: 12px; background: #e3f2fd; margin-bottom: 8px; border-left: 6px solid #1976d2; font-size: 18px; }
</style>
""", unsafe_allow_html=True)

# --- TRANG 1: CHỌN TƯ CÁCH ---
if st.session_state.user_role is None:
    st.title("🏆 English Class Word Game")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Join as Student", use_container_width=True):
            st.session_state.temp_role = "Student"
    with col2:
        if st.button("Join as Teacher", use_container_width=True):
            st.session_state.temp_role = "Teacher"

    if 'temp_role' in st.session_state:
        if st.session_state.temp_role == "Student":
            nick = st.text_input("Please input nickname (English only):").strip()
            # Xử lý nhấn Enter hoặc nút Confirm
            if st.button("Confirm Name") or (nick and st.session_state.get('last_input') != nick):
                if re.match("^[a-zA-Z0-9 ]+$", nick):
                    st.session_state.nickname = nick
                    st.session_state.user_role = "Student"
                    st.rerun()
                elif nick: 
                    st.error("Only English letters and numbers allowed!")
        
        else:
            pwd = st.text_input("Please input teacher password:", type="password")
            if st.button("Access Panel") or (pwd == PASSWORD_TEACHER):
                if pwd == PASSWORD_TEACHER:
                    st.session_state.user_role = "Teacher"
                    st.rerun()
                elif pwd: 
                    st.error("Incorrect password!")

# --- TRANG CHÍNH ---
else:
    state = load_state()

    # --- GIAO DIỆN HỌC SINH ---
    if st.session_state.user_role == "Student":
        # Tự động Reset khi giáo viên đổi câu mới (Dựa trên question_id)
        if state["question_id"] != st.session_state.last_question_id:
            st.session_state.placed_words = []
            st.session_state.submitted = False
            st.session_state.last_question_id = state["question_id"]
            if state["status"] == "playing":
                words = state["sentence"].split()
                random.shuffle(words)
                st.session_state.available_words = words
            st.rerun()

        if state["status"] == "waiting":
            st.header(f"Hello, {st.session_state.nickname}!")
            st.subheader("⏳ Please wait for the teacher to start...")
            time.sleep(2)
            st.rerun()
        
        elif state["status"] == "playing":
            if st.session_state.submitted:
                st.success("✅ Submitted! Waiting for results...")
                time.sleep(3)
                st.rerun()
            else:
                st.write("### Arrange the sentence:")
                # Vùng hiển thị câu đang xếp
                st.markdown('<div class="placeholder-container">', unsafe_allow_html=True)
                for i, w in enumerate(st.session_state.placed_words):
                    if st.button(w, key=f"p_{i}"):
                        st.session_state.available_words.append(w)
                        st.session_state.placed_words.pop(i)
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

                # Vùng các block từ để chọn
                st.write("Available words:")
                for i, w in enumerate(st.session_state.available_words):
                    if st.button(w, key=f"a_{i}"):
                        st.session_state.placed_words.append(w)
                        st.session_state.available_words.pop(i)
                        st.rerun()

                if st.button("CONFIRM ANSWER", type="primary", use_container_width=True):
                    final = " ".join(st.session_state.placed_words)
                    state["results"].append({"name": st.session_state.nickname, "answer": final, "time": time.time()})
                    save_state(state)
                    st.session_state.submitted = True
                    st.rerun()

        elif state["status"] == "ended":
            st.info("⌛ Session ended. The teacher is reviewing.")
            time.sleep(3)
            st.rerun()

    # --- GIAO DIỆN GIÁO VIÊN ---
    elif st.session_state.user_role == "Teacher":
        st.header("👨‍🏫 Teacher Control Panel")
        
        if state["status"] == "waiting":
            sentence = st.text_area("Input English sentence:", placeholder="e.g., I love learning English")
            if (st.button("SEND TO CLASS") or (sentence and sentence.endswith('\n'))) and sentence:
                state["sentence"] = sentence.strip()
                state["status"] = "playing"
                state["results"] = []
                state["question_id"] += 1 # Kích hoạt reset cho học sinh
                save_state(state)
                st.rerun()
        
        elif state["status"] == "playing":
            st.subheader("⚡ Live Ranking (Submission Order)")
            # Sắp xếp học sinh theo thời gian nộp nhanh nhất
            ranked = sorted(state["results"], key=lambda x: x['time'])
            
            if not ranked:
                st.write("Waiting for students...")
            else:
                for i, res in enumerate(ranked):
                    st.markdown(f'<div class="rank-card"><b>Rank {i+1}:</b> {res["name"]} - <i>Submitted</i></div>', unsafe_allow_html=True)
            
            if st.button("END & SHOW RESULTS", type="primary"):
                state["status"] = "ended"
                save_state(state)
                st.rerun()
            time.sleep(2)
            st.rerun()

        elif state["status"] == "ended":
            st.subheader("Final Class Results")
            ranked = sorted(state["results"], key=lambda x: x['time'])
            for i, res in enumerate(ranked):
                st.write(f"**Rank {i+1}: {res['name']}**")
                st.code(res['answer'])
            
            if st.button("NEXT QUESTION (Restart Flow)"):
                state["status"] = "waiting"
                state["results"] = []
                # Giữ nguyên question_id cho đến khi có câu hỏi thực sự mới
                save_state(state)
                st.rerun()
