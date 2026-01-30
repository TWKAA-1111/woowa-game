import streamlit as st
import random
import time
import os
import base64
import json
import datetime
import re
import pandas as pd
import streamlit.components.v1 as html
from barcode import Code128
from barcode.writer import ImageWriter
from io import BytesIO

# --- 1. 設定與參數 ---
GAME_DURATION = 20      # 遊戲時間 20 秒
GRID_SIZE = 9           # 3x3
MAX_DAILY_ATTEMPTS = 3  # 每日次數限制
VIP_EMAIL = "vip@woowa.com" # VIP 帳號

DATA_FILE = "user_data.json" 
LOG_FILE = "game_logs.csv"   
ADMIN_PASSWORD = "admin"     

# 圖片路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
path_win = os.path.join(current_dir, "win.png")
path_bg = os.path.join(current_dir, "bg.jpg")
path_cover = os.path.join(current_dir, "cover.png")
path_alert = os.path.join(current_dir, "alert.png")

# 雜魚圖路徑
path_lose1 = os.path.join(current_dir, "lose1.png")
path_lose2 = os.path.join(current_dir, "lose2.png")
path_lose3 = os.path.join(current_dir, "lose3.png")

st.set_page_config(page_title="黃金WooWa兄弟", page_icon="🏆", layout="wide")

# --- 2. 資料存取邏輯 (含自動修復功能) ---

def load_data():
    if not os.path.exists(DATA_FILE): return {}
    try:
        with open(DATA_FILE, "r") as f: return json.load(f)
    except: return {}

def save_data(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f)

def check_and_update_attempts(email):
    if email == VIP_EMAIL: return True, "VIP無限"
    data = load_data()
    today_str = str(datetime.date.today())
    if email not in data: data[email] = {}
    current_count = data[email].get(today_str, 0)
    if current_count >= MAX_DAILY_ATTEMPTS: return False, current_count
    data[email][today_str] = current_count + 1
    save_data(data)
    return True, current_count + 1

def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None

def log_game_result(email, result, prize_name="N/A", coupon_code="N/A"):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    new_data = pd.DataFrame([{
        "時間": now, 
        "Email": email, 
        "遊戲結果": result, 
        "獎項": prize_name,
        "優惠碼": coupon_code
    }])

    if not os.path.exists(LOG_FILE):
        new_data.to_csv(LOG_FILE, index=False, encoding='utf-8-sig')
    else:
        try:
            old_df = pd.read_csv(LOG_FILE)
            combined = pd.concat([old_df, new_data], ignore_index=True)
            combined.to_csv(LOG_FILE, index=False, encoding='utf-8-sig')
        except Exception as e:
            new_data.to_csv(LOG_FILE, mode='a', header=False, index=False, encoding='utf-8-sig')

# --- 3. 視覺與 CSS ---

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f: data = f.read()
    return base64.b64encode(data).decode()

def add_custom_css():
    bg_style = ""
    if os.path.exists(path_bg):
        bin_str = get_base64_of_bin_file(path_bg)
        bg_style = f"""
        .stApp {{
            background-image: url("data:image/jpg;base64,{bin_str}");
            background-size: cover;
            background-repeat: no-repeat;
            background-position: center;
        }}
        """

    card_back_style = ""
    card_text_color = "#333" 
    
    if os.path.exists(path_cover):
        cover_bin = get_base64_of_bin_file(path_cover)
        card_back_style = f"""
            background-image: url("data:image/png;base64,{cover_bin}") !important;
            background-size: 100% 100% !important; 
            background-position: center !important;
            background-repeat: no-repeat !important;
            background-origin: border-box !important;
        """
        card_text_color = "transparent" 

    st.markdown(f"""
    <style>
    {bg_style}
    
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    @keyframes shake {{
        0% {{ transform: translate(1px, 1px) rotate(0deg); }}
        10% {{ transform: translate(-1px, -2px) rotate(-1deg); }}
        20% {{ transform: translate(-3px, 0px) rotate(1deg); }}
        30% {{ transform: translate(3px, 2px) rotate(0deg); }}
        40% {{ transform: translate(1px, -1px) rotate(1deg); }}
        50% {{ transform: translate(-1px, 2px) rotate(-1deg); }}
        60% {{ transform: translate(-3px, 1px) rotate(0deg); }}
        70% {{ transform: translate(3px, 1px) rotate(-1deg); }}
        80% {{ transform: translate(-1px, -1px) rotate(1deg); }}
        90% {{ transform: translate(1px, 2px) rotate(0deg); }}
        100% {{ transform: translate(1px, -2px) rotate(-1deg); }}
    }}
    
    .shaking {{
        animation: shake 0.5s;
        animation-iteration-count: infinite;
    }}

    /* === 電腦版 === */
    @media (min-width: 601px) {{
        [data-testid="stHorizontalBlock"]:has(button) {{
            width: 600px !important;
            margin: 0 auto !important;
            gap: 20px !important;
        }}
        div.stButton > button, div[data-testid="stImage"] {{
            width: 180px !important; 
            height: 180px !important;
            margin-bottom: 20px !important;
            font-size: 50px !important;
            color: {card_text_color} !important;
            {card_back_style}
        }}
        div[data-testid="stImage"] > img {{
             width: 180px !important; height: 180px !important; object-fit: cover;
        }}
        [data-testid="stExpander"] {{ max-width: 300px !important; }}
    }}

    /* === 手機版專用 === */
    @media (max-width: 600px) {{
        .block-container {{
            padding-top: 2rem !important;
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }}
        [data-testid="stHorizontalBlock"]:has(button) {{
            display: grid !important;
            grid-template-columns: 1fr 1fr 1fr !important;
            gap: 8px !important; 
            width: 100% !important;
            margin: 0 auto !important;
        }}
        [data-testid="stHorizontalBlock"]:has(button) [data-testid="column"] {{
            width: 100% !important; min-width: 0 !important; flex: unset !important;
        }}
        div.stButton > button {{
            width: 100% !important; aspect-ratio: 1 / 1 !important;
            margin: 0 !important; padding: 0 !important; border: none !important;     
            border-radius: 8px !important; color: {card_text_color} !important;
            {card_back_style}
            min-height: 0 !important; box-shadow: none !important;
        }}
        div[data-testid="stImage"] {{
            width: 100% !important; aspect-ratio: 1 / 1 !important;
            margin: 0 !important; padding: 0 !important;
            display: flex !important; align-items: center !important; justify-content: center !important;
            min-height: 0 !important;
        }}
        div[data-testid="stImage"] > img {{
            width: 100% !important; height: 100% !important;
            object-fit: cover !important; border-radius: 8px !important; padding: 0 !important;
        }}
        [data-testid="stExpander"] {{
            width: 100% !important; min-width: 100% !important; margin-top: 20px !important;
        }}
        [data-testid="stExpander"] p {{ font-size: 16px !important; }}
        h1 {{ font-size: 1.5rem !important; margin-bottom: 10px !important; }}
        p {{ font-size: 0.9rem !important; }}
    }}
    
    .prize-title {{
        font-size: 24px; font-weight: bold; color: #d63031; text-align: center; margin-top: 20px;
    }}
    .prize-name {{
        font-size: 20px; font-weight: bold; color: #2d3436; text-align: center; margin-bottom: 10px;
        background: rgba(255,255,255,0.8); padding: 15px; border-radius: 10px;
    }}
    .prize-expiry {{
        font-size: 16px; color: #636e72; text-align: center; margin-bottom: 10px;
    }}
    .screenshot-alert {{
        background-color: #ff7675; color: white; padding: 10px; border-radius: 8px;
        text-align: center; font-weight: bold; font-size: 18px; margin: 15px 0;
        animation: pulse 2s infinite;
    }}
    @keyframes pulse {{
        0% {{ box-shadow: 0 0 0 0 rgba(255, 118, 117, 0.7); }}
        70% {{ box-shadow: 0 0 0 10px rgba(255, 118, 117, 0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(255, 118, 117, 0); }}
    }}
    .footer-note {{
        font-size: 12px; color: #636e72; margin-top: 30px; padding: 10px;
        background-color: rgba(240, 240, 240, 0.9); border-radius: 5px;
        line-height: 1.5;
    }}
    </style>
    """, unsafe_allow_html=True)

def show_dynamic_timer(seconds_left):
    if seconds_left < 0: seconds_left = 0
    
    alert_img_html = ""
    if os.path.exists(path_alert):
        alert_bin = get_base64_of_bin_file(path_alert)
        alert_img_html = f"""
            <img id="alert_icon" src="data:image/png;base64,{alert_bin}" 
            style="display:none; width:30px; vertical-align:middle; margin-right:10px;" />
        """
    
    init_val = int(seconds_left)
    
    timer_html = f"""
    <style>
        @keyframes shake {{
            0% {{ transform: translate(1px, 1px) rotate(0deg); }}
            10% {{ transform: translate(-1px, -2px) rotate(-1deg); }}
            20% {{ transform: translate(-3px, 0px) rotate(1deg); }}
            30% {{ transform: translate(3px, 2px) rotate(0deg); }}
            40% {{ transform: translate(1px, -1px) rotate(1deg); }}
            50% {{ transform: translate(-1px, 2px) rotate(-1deg); }}
            60% {{ transform: translate(-3px, 1px) rotate(0deg); }}
            70% {{ transform: translate(3px, 1px) rotate(-1deg); }}
            80% {{ transform: translate(-1px, -1px) rotate(1deg); }}
            90% {{ transform: translate(1px, 2px) rotate(0deg); }}
            100% {{ transform: translate(1px, -2px) rotate(-1deg); }}
        }}
        .shaking {{
            animation: shake 0.5s;
            animation-iteration-count: infinite;
        }}
    </style>
    <div style="font-family:'Arial';font-size:18px;font-weight:bold;color:white;background-color:#ff4b4b;padding:8px;border-radius:50px;text-align:center;width:80%;max-width:300px;margin:10px auto;box-shadow:1px 1px 3px rgba(0,0,0,0.3); display:flex; align-items:center; justify-content:center;">
        {alert_img_html}
        <span>⏱️ <span id="timer_val">{init_val}</span> 秒</span>
    </div>
    <script>
        (function() {{
            var timeleft = {init_val}; 
            var timerElement = document.getElementById("timer_val");
            var alertIcon = document.getElementById("alert_icon");
            
            if (window.gameTimer) clearInterval(window.gameTimer);
            
            if(timeleft <= 5 && alertIcon) {{
                alertIcon.style.display = "inline-block";
                alertIcon.classList.add("shaking");
            }}

            window.gameTimer = setInterval(function(){{
                timeleft -= 1;
                
                if(timeleft <= 0){{
                    clearInterval(window.gameTimer);
                    if(timerElement) timerElement.innerHTML = "0";
                }} else {{
                    if(timerElement) timerElement.innerHTML = Math.floor(timeleft);
                }}
                
                if(timeleft <= 5 && alertIcon) {{
                    alertIcon.style.display = "inline-block";
                    alertIcon.classList.add("shaking");
                }}
                
            }}, 1000);
        }})();
    </script>
    """
    html.html(timer_html, height=60)

def generate_barcode_image(code_text):
    rv = BytesIO()
    Code128(code_text, writer=ImageWriter()).write(rv)
    return rv

# --- 4. 遊戲邏輯 ---

def init_game():
    target_count = 3 
    distractor_count = GRID_SIZE - target_count
    
    win_content = path_win if os.path.exists(path_win) else "🌟"
    
    available_lose = []
    if os.path.exists(path_lose1): available_lose.append(path_lose1)
    if os.path.exists(path_lose2): available_lose.append(path_lose2)
    if os.path.exists(path_lose3): available_lose.append(path_lose3)
    
    if not available_lose:
        old_lose = os.path.join(current_dir, "lose.png")
        if os.path.exists(old_lose):
            available_lose.append(old_lose)
        else:
            available_lose.append("💨") 

    cards = [win_content] * target_count
    for _ in range(distractor_count):
        cards.append(random.choice(available_lose))
        
    random.shuffle(cards)
    
    st.session_state.board = cards
    st.session_state.solved = [False] * GRID_SIZE
    st.session_state.temp_flipped = [] 
    st.session_state.game_phase = "PLAYING"
    st.session_state.start_time = time.time()
    st.session_state.win_symbol = win_content
    st.session_state.logged = False 

# --- 5. 主程式 ---

add_custom_css()

if 'game_phase' not in st.session_state:
    st.session_state.game_phase = "LOGIN"

# ================= 階段 1: 登入 =================
if st.session_state.game_phase == "LOGIN":
    st.markdown("<h1 style='text-align: center;'>🏆 找出黃金WooWa三兄弟</h1>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown("<p style='text-align: center;'>規則：一次翻出「3張」WooWa三兄弟！</p>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            email_input = st.text_input("Email 信箱", placeholder="user@example.com")
            
            if st.button("🚀 開始挑戰", use_container_width=True):
                if not email_input:
                    st.warning("請輸入 Email")
                elif not is_valid_email(email_input):
                    st.error("Email 格式不正確")
                else:
                    can_play, current_count = check_and_update_attempts(email_input)
                    if can_play:
                        msg = f"登入成功！今日第 {current_count}/3 次" if current_count != "VIP無限" else "👑 VIP 測試帳號登入！"
                        st.success(msg)
                        st.session_state.current_user_email = email_input
                        time.sleep(1)
                        init_game()
                        st.rerun()
                    else:
                        st.error(f"抱歉，{email_input} 今日次數已用完")

# ================= 階段 2: 進行中 =================
elif st.session_state.game_phase == "PLAYING":
    
    st.markdown("<h1 style='text-align: center;'>🏆 找出黃金WooWa三兄弟</h1>", unsafe_allow_html=True)
    
    elapsed = time.time() - st.session_state.start_time
    left = GAME_DURATION - elapsed
    show_dynamic_timer(left)
    
    if left <= 0:
        st.session_state.game_phase = "LOSE"
        st.rerun()

    with st.container():
        cols = st.columns(3) 
        for i in range(GRID_SIZE):
            with cols[i % 3]:
                content = st.session_state.board[i]
                
                if st.session_state.solved[i] or i in st.session_state.temp_flipped:
                    if str(content).lower().endswith(('.png','.jpg','.jpeg')): 
                        st.image(content)
                    else: 
                        st.markdown(f"<div style='width:100%;aspect-ratio:1/1;background:white;display:flex;align-items:center;justify-content:center;font-size:30px;border-radius:8px;border:2px solid #333;'>{content}</div>", unsafe_allow_html=True)
                else:
                    disable = (len(st.session_state.temp_flipped) >= 3)
                    if st.button("❓", key=i, disabled=disable):
                        st.session_state.temp_flipped.append(i)
                        st.rerun()

    if len(st.session_state.temp_flipped) == 3:
        idx1, idx2, idx3 = st.session_state.temp_flipped
        c1 = st.session_state.board[idx1]
        c2 = st.session_state.board[idx2]
        c3 = st.session_state.board[idx3]
        
        if c1 == c2 == c3 == st.session_state.win_symbol:
            st.toast("🎉 成功！WooWa兄弟集合！", icon="✅")
            st.session_state.solved[idx1] = True
            st.session_state.solved[idx2] = True
            st.session_state.solved[idx3] = True
            st.session_state.temp_flipped = [] 
            st.session_state.game_phase = "WIN"
            st.rerun()
        else:
            st.toast("❌ 失敗！這不是三兄弟...", icon="⚠️")
            time.sleep(1.5) 
            st.session_state.temp_flipped = [] 
            st.rerun()

# ================= 階段 3: 結算 =================
elif st.session_state.game_phase == "WIN":
    if not st.session_state.logged:
        rewards = [
            ("A", "飲品折10元優惠"),
            ("B", "任一飲品+餐點折20元"),
            ("C", "WOOWA吊飾乙個(隨機)")
        ]
        probabilities = [0.497, 0.497, 0.006]
        
        selected = random.choices(rewards, weights=probabilities, k=1)[0]
        prize_type = selected[0] 
        prize_name = selected[1] 
        
        code = f"{prize_type}-{random.randint(10000,99999)}"
        
        # 期限 3 天
        expiry_date = datetime.date.today() + datetime.timedelta(days=3)
        expiry_str = expiry_date.strftime("%Y/%m/%d")
        
        st.session_state.prize_info = {
            "name": prize_name,
            "code": code,
            "expiry": expiry_str
        }
        
        log_game_result(st.session_state.current_user_email, "WIN", prize_name, code)
        st.session_state.logged = True

    st.balloons()
    
    prize = st.session_state.prize_info
    
    st.markdown("<h1 style='text-align: center;'>🎉 恭喜中獎！</h1>", unsafe_allow_html=True)
    st.markdown(f"<div class='prize-name'>獲得：{prize['name']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='prize-expiry'>📅 使用期限：{prize['expiry']} (含當日)</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='screenshot-alert'>📸 請務必截圖保存，憑此畫面兌換！</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        img = generate_barcode_image(prize['code'])
        st.image(img, caption=f"優惠碼: {prize['code']}")
        
        if st.button("再來一局", use_container_width=True):
            st.session_state.game_phase = "LOGIN"
            st.rerun()
            
    # ★ 注意事項 (第4點加粗體)
    st.markdown("""
    <div class='footer-note'>
        <b>注意事項：</b><br>
        1. 使用期限以得獎畫面顯示時間為主，到期恕無法兌換。<br>
        2. 獎品僅限於 M5 COFFEE 內用店，外帶店不參加活動。<br>
        3. 本活動最後最終決定權，取決於 M5 COFFEE 公告為主。<br>
        4. <b>每組兌換碼僅限兌換一次。</b>
    </div>
    """, unsafe_allow_html=True)

elif st.session_state.game_phase == "LOSE":
    if not st.session_state.logged:
        log_game_result(st.session_state.current_user_email, "LOSE", "N/A", "N/A")
        st.session_state.logged = True

    st.error("⏰ 時間到！挑戰失敗！")
    if st.button("再試一次"):
        st.session_state.game_phase = "LOGIN"
        st.rerun()

# ================= ★ 後台介面 ★ =================
st.divider()

with st.expander("⚙️ 管理員登入"):
    admin_pwd = st.text_input("密碼", type="password", key="admin_pwd")
    if admin_pwd == ADMIN_PASSWORD:
        st.success("已登入")
        if os.path.exists(LOG_FILE):
            try:
                df = pd.read_csv(LOG_FILE)
                st.dataframe(df, height=200) 
                csv = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("下載 CSV", csv, "game_data.csv", "text/csv")
            except Exception as e:
                st.error("⚠️ 偵測到數據格式版本衝突。")
                st.warning("請點擊下方按鈕重置數據庫以修復。")
                if st.button("🔴 重置數據庫"):
                    os.remove(LOG_FILE)
                    st.rerun()
        else:
            st.caption("尚無數據")