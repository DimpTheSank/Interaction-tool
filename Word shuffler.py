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
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: pass
    return {"sentence": "", "status": "waiting", "results": [], "question_id": 0}

def save_state(state):
    with open(DB_FILE, "w") as f: json.dump(state, f)

# Khởi tạo session_state cá nhân cho từng trình duyệt
if 'user_role' not in st.session_state: st.session_state.user_role = None
if 'nickname' not in st.session_state: st.session_state.nickname = ""
if 'placed_words' not in st.session_state: st.session_state.placed_words = []
if 'available_words' not in st.session_state: st.session_state.available_words = []
if 'last_question_id' not in st.session_state: st.session_state.last_question_id = -1
if 'submitted' not in st.session_state: st.session_state.submitted = False

# --- CSS: Giao diện Block chuyên nghiệp ---
st.markdown("""
<style>
    .placeholder-container { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; margin-bottom: 30px; min-height: 80px; padding: 15px; border: 3px dashed #ccc; border-radius: 15px; background: #fafafa; }
    .word-block { background: #FFEB3B; border: 3px solid #FBC02D; border-radius: 10px; padding: 12px 24px; font-weight: bold; font-size: 20px; cursor: pointer; box-shadow: 3px 3px 0px #ccc; }
    .word-block:hover { background: #FFF176; transform: translateY(-2px); }
    .rank-card { padding: 10px; border-radius: 10px; background: #e3f2fd; margin-bottom: 5px; border-left: 5px solid #2196f3; }
</style>
""", unsafe_allow_html=True)

# --- TRANG 1: CHỌN TƯ CÁCH THAM GIA ---
if st.session_state.user_role is None:
    st.title("🧩 English Word Game")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Student", use_container_width=True):
            st.session_state.temp_role = "Student"
    with col2:
        if st.button("Teacher", use_container_width=True):
            st.session_state.temp_role = "Teacher"

    if 'temp_role' in st.session_state:
        if st.session_state.temp_role == "Student":
            nick = st.text_input("Please input nickname (English characters only):").strip()
            # Xử lý khi nhấn Enter hoặc nhấn nút Confirm
            if (st.button("Confirm") or (nick and nick != st.session_state.nickname)) and nick:
                if re.match("^[a-zA-Z0-9 ]+$", nick):
                    st.session_state.nickname = nick
                    st.session_state.user_role = "Student"
                    st.rerun()
                else: st.error("Invalid nickname! No special characters or Vietnamese allowed.")
        
        else:
            pwd = st.text_input("Please input password:", type="password")
            if st.button("Confirm Password") or (pwd == PASSWORD_TEACHER):
                if pwd == PASSWORD_TEACHER:
                    st.session_state.user_role = "Teacher"
                    st.rerun()
                else: st.error("Wrong password!")

# --- TRANG CHÍNH ---
else:
    state = load_state()

    # --- GIAO DIỆN HỌC SINH ---
    if st.session_state.user_role == "Student":
        # 1. Kiểm tra nếu có câu hỏi mới từ giáo viên thì Reset dữ liệu cũ
        if state["question_id"] != st.session_state.last_question_id:
            st.session_state.placed_words = []
            st.session_state.available_words = []
            st.session_state.submitted = False
            st.session_state.last_question_id = state["question_id"]
            if state["status"] == "playing":
                words = state["sentence"].split()
                random.shuffle(words)
                st.session_state.available_words = words
            st.rerun()

        if state["status"] == "waiting":
            st.header(f"Hi {st.session_state.nickname}!")
            st.subheader("📢 Please wait for teacher...")
            time.sleep(2)
            st.rerun()
        
        elif state["status"] == "playing":
            if st.session_state.submitted:
                st.info("✅ Submitted! Please wait for others.")
                time.sleep(3)
                st.rerun()
            else:
                st.write("### Tap words to arrange:")
                
                # Khu vực các ô đợi (Placeholders)
                st.markdown('<div class="placeholder-container">', unsafe_allow_html=True)
                cols_p = st.columns(len(state["sentence"].split()) if state["sentence"] else 1)
                for i, w in enumerate(st.session_state.placed_words):
                    if st.button(w, key=f"placed_{i}", use_container_width=True):
                        st.session_state.available_words.append(w)
                        st.session_state.placed_words.pop(i)
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

                st.write("---")
                # Khu vực các block từ đang xáo trộn
                for i, w in enumerate(st.session_state.available_words):
                    if st.button(w, key=f"avail_{i}"):
                        st.session_state.placed_words.append(w)
                        st.session_state.available_words.pop(i)
                        st.rerun()

                if st.button("CONFIRM SUBMIT", type="primary", use_container_width=True):
                    final_ans = " ".join(st.session_state.placed_words)
                    state["results"].append({"name": st.session_state.nickname, "answer": final_ans, "time": time.time()})
                    save_state(state)
                    st.session_state.submitted = True
                    st.rerun()

        elif state["status"] == "ended":
            st.warning("⌛ Time's up! Waiting for the next round.")
            time.sleep(3)
            st.rerun()

    # --- GIAO DIỆN GIÁO VIÊN ---
    elif st.session_state.user_role == "Teacher":
        st.header("Teacher Control Panel")
        
        if state["status"] == "waiting":
            input_sent = st.text_area("Input a new sentence:", placeholder="Type here...")
            if st.button("SEND TO STUDENTS") and input_sent:
                state["sentence"] = input_sent
                state["status"] = "playing"
                state["results"] = []
                state["question_id"] += 1 # Tăng ID để máy học sinh tự Reset
                save_state(state)
                st.rerun()
        
        elif state["status"] == "playing":
            st.subheader("实时 Leaderboard (Submitting...)")
            # Sắp xếp theo thời gian nộp ngay lập tức
            sorted_subs = sorted(state["results"], key=lambda x: x['time'])
            
            if not sorted_subs:
                st.write("No one has submitted yet...")
            else:
                for i, res in enumerate(sorted_subs):
                    st.markdown(f'<div class="rank-card">Rank {i+1}: <b>{res["name"]}</b> (Submitted)</div>', unsafe_allow_html=True)
            
            if st.button("END & SHOW ALL ANSWERS", type="primary"):
                state["status"] = "ended"
                save_state(state)
                st.rerun()
            
            time.sleep(2) # Tự động cập nhật Leaderboard
            st.rerun()

        elif state["status"] == "ended":
            st.subheader("Final Results Summary")
            sorted_res = sorted(state["results"], key=lambda x: x['time'])
            
            for i, res in enumerate(sorted_res):
                col_a, col_b = st.columns([1, 4])
                col_a.write(f"**Rank {i+1}: {res['name']}**")
                col_b.code(res['answer'], language="text")
            
            if st.button("NEXT QUESTION (Reset All)"):
                state["status"] = "waiting"
                state["sentence"] = ""
                state["results"] = []
                # Không reset question_id ở đây để học sinh vẫn ở trạng thái chờ câu mới
                save_state(state)
                st.rerun()
