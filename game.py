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
GAME_DURATION = 30      # 遊戲時間
GRID_SIZE = 9           # 3x3
MAX_DAILY_ATTEMPTS = 3  # 每日次數限制
VIP_EMAIL = "vip@woowa.com" # VIP 帳號

DATA_FILE = "user_data.json" 
LOG_FILE = "game_logs.csv"   
ADMIN_PASSWORD = "admin"     

# 圖片路徑 (定義多個 lose 圖片)
current_dir = os.path.dirname(os.path.abspath(__file__))
path_win = os.path.join(current_dir, "win.png")
path_bg = os.path.join(current_dir, "bg.jpg")
path_cover = os.path.join(current_dir, "cover.png")
path_alert = os.path.join(current_dir, "alert.png")

# ★ 設定 3 種雜魚圖的路徑
path_lose1 = os.path.join(current_dir, "lose1.png")
path_lose2 = os.path.join(current_dir, "lose2.png")
path_lose3 = os.path.join(current_dir, "lose3.png")

st.set_page_config(page_title="黃金WooWa兄弟", page_icon="🏆", layout="wide")

# --- 2. 資料存取邏輯 ---

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

def log_game_result(email, result, coupon_code="N/A"):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_data = {"時間": [now], "Email": [email], "遊戲結果": [result], "優惠碼": [coupon_code]}
    new_df = pd.DataFrame(new_data)
    if os.path.exists(LOG_FILE):
        new_df.to_csv(LOG_FILE, mode='a', header=False, index=False, encoding='utf-8-sig')
    else:
        new_df.to_csv(LOG_FILE, index=False, encoding='utf-8-sig')

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
        """
        card_text_color = "transparent" 

    st.markdown(f"""
    <style>
    {bg_style}
    
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    /* === 電腦版 (螢幕 > 600px) === */
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
        
        [data-testid="stExpander"] {{
            max-width: 300px !important;
        }}
    }}

    /* === 手機版專用 (螢幕 <= 600px) === */
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
            width: 100% !important;
            min-width: 0 !important;
            flex: unset !important;
        }}

        div.stButton > button {{
            width: 100% !important;
            aspect-ratio: 1 / 1 !important;
            margin: 0 !important;
            padding: 0 !important;       
            border: none !important;     
            border-radius: 8px !important;
            color: {card_text_color} !important;
            {card_back_style}
            min-height: 0 !important;
            box-shadow: none !important;
        }}

        div[data-testid="stImage"] {{
            width: 100% !important;
            aspect-ratio: 1 / 1 !important;
            margin: 0 !important;
            padding: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            min-height: 0 !important;
        }}
        
        div[data-testid="stImage"] > img {{
            width: 100% !important;
            height: 100% !important;
            object-fit: cover !important; 
            border-radius: 8px !important;
            padding: 0 !important;
        }}

        [data-testid="stExpander"] {{
            width: 100% !important;
            min-width: 100% !important;
            margin-top: 20px !important;
        }}
        
        [data-testid="stExpander"] p {{
            font-size: 16px !important; 
        }}

        h1 {{ font-size: 1.5rem !important; margin-bottom: 10px !important; }}
        p {{ font-size: 0.9rem !important; }}
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
    
    # ★ 關鍵修正：將 CSS 放在 iframe 內部，確保動畫生效
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
            
            // 立即檢查
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
    
    # ★ 關鍵修正：隨機選取多種雜魚圖
    available_lose = []
    if os.path.exists(path_lose1): available_lose.append(path_lose1)
    if os.path.exists(path_lose2): available_lose.append(path_lose2)
    if os.path.exists(path_lose3): available_lose.append(path_lose3)
    
    # 如果沒找到 1,2,3，試試看有沒有舊的 lose.png，再沒有就用 Emoji
    if not available_lose:
        old_lose = os.path.join(current_dir, "lose.png")
        if os.path.exists(old_lose):
            available_lose.append(old_lose)
        else:
            available_lose.append("💨") # Emoji 備案

    # 產生牌組：3張贏 + 6張隨機的輸
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

    # ★ 繪製九宮格
    with st.container():
        cols = st.columns(3) 
        for i in range(GRID_SIZE):
            with cols[i % 3]:
                content = st.session_state.board[i]
                
                # 顯示牌面
                if st.session_state.solved[i] or i in st.session_state.temp_flipped:
                    if str(content).lower().endswith(('.png','.jpg','.jpeg')): 
                        st.image(content)
                    else: 
                        st.markdown(f"<div style='width:100%;aspect-ratio:1/1;background:white;display:flex;align-items:center;justify-content:center;font-size:30px;border-radius:8px;border:2px solid #333;'>{content}</div>", unsafe_allow_html=True)
                else:
                    # 顯示牌背
                    disable = (len(st.session_state.temp_flipped) >= 3)
                    if st.button("❓", key=i, disabled=disable):
                        st.session_state.temp_flipped.append(i)
                        st.rerun()

    # 比對邏輯
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
        code = f"VIP-{random.randint(10000,99999)}"
        st.session_state.coupon_code = code
        log_game_result(st.session_state.current_user_email, "WIN", code)
        st.session_state.logged = True

    st.balloons()
    st.markdown("<h1 style='text-align: center;'>🎉 恭喜通關！</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>▼ 請截圖保存您的優惠碼 ▼</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        img = generate_barcode_image(st.session_state.coupon_code)
        st.image(img, caption=f"優惠碼: {st.session_state.coupon_code}")
        
        if st.button("再來一局", use_container_width=True):
            st.session_state.game_phase = "LOGIN"
            st.rerun()

elif st.session_state.game_phase == "LOSE":
    if not st.session_state.logged:
        log_game_result(st.session_state.current_user_email, "LOSE", "N/A")
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
            df = pd.read_csv(LOG_FILE)
            st.dataframe(df, height=200) 
            csv = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button("下載 CSV", csv, "game_data.csv", "text/csv")
        else:
            st.caption("尚無數據")