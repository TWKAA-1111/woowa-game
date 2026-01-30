這是一個關於 CSS 樣式衝突的經典問題。

**問題解析：**

1. **卡背圖太小**：這是因為按鈕預設有「內距 (Padding)」，導致背景圖被往內擠。我們需要用 CSS 強制把內距歸零，並設定背景圖「完全拉伸 (100% 100%)」。
2. **管理員登入太擠**：這是因為我上一版為了強制九宮格，寫了一條「所有欄位寬度強制 32%」的 CSS 規則。這條規則「誤傷」了管理員登入區塊，導致原本只有兩欄的它也被壓縮成 32%。**解決方法是：管理員區塊不要用欄位 (Columns)，改用 CSS 控制寬度。**
3. **倒數計時不動**：可能是 JavaScript 載入時機的問題，我優化了計時器的代碼，並確保它在手機上也能順暢執行。

---

### 🚀 最終修正版 `game.py` (全能修復版)

請**全選複製**並覆蓋原本的檔案。這版程式碼解決了上述三個問題。

```python
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

# 圖片路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
path_win = os.path.join(current_dir, "win.png")
path_lose = os.path.join(current_dir, "lose.png")
path_bg = os.path.join(current_dir, "bg.jpg")
path_cover = os.path.join(current_dir, "cover.png")

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

# --- 3. 視覺與 CSS (修正卡背大小 + 管理員排版) ---

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
        # ★ 關鍵修正 1: 強制背景圖滿版，不留空隙 (100% 100%)
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
        
        /* 管理員登入框在電腦版限制寬度 */
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
        
        /* 1. 只針對遊戲區的 Grid 做強制排版 (避免誤傷管理員區塊) */
        /* 透過檢查是否包含 button 來判斷這是不是遊戲盤面 */
        [data-testid="stHorizontalBlock"]:has(button) {{
            display: grid !important;
            grid-template-columns: 1fr 1fr 1fr !important;
            gap: 8px !important; 
            width: 100% !important;
            margin: 0 auto !important;
        }}
        
        /* 針對遊戲區的 column 強制設定 */
        [data-testid="stHorizontalBlock"]:has(button) [data-testid="column"] {{
            width: 100% !important;
            min-width: 0 !important;
            flex: unset !important;
        }}

        /* 2. 按鈕 (牌背) 修正：移除 padding 與 border，讓圖片滿版 */
        div.stButton > button {{
            width: 100% !important;
            aspect-ratio: 1 / 1 !important;
            margin: 0 !important;
            padding: 0 !important;       /* ★ 移除內距 */
            border: none !important;     /* ★ 移除邊框 */
            border-radius: 8px !important;
            color: {card_text_color} !important;
            {card_back_style}
            min-height: 0 !important;
            box-shadow: none !important;
        }}

        /* 3. 圖片 (牌面) 修正 */
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
            object-fit: cover !important; /* ★ 滿版 */
            border-radius: 8px !important;
            padding: 0 !important;
        }}

        /* 4. ★ 關鍵修正：管理員登入區塊 ★ */
        /* 讓 Expander 在手機版恢復 100% 寬度，不再被壓縮 */
        [data-testid="stExpander"] {{
            width: 100% !important;
            min-width: 100% !important;
            margin-top: 20px !important;
        }}
        
        [data-testid="stExpander"] p {{
            font-size: 16px !important; /* 放大文字讓它可閱讀 */
        }}

        h1 {{ font-size: 1.5rem !important; margin-bottom: 10px !important; }}
        p {{ font-size: 0.9rem !important; }}
    }}
    </style>
    """, unsafe_allow_html=True)

def show_dynamic_timer(seconds_left):
    if seconds_left < 0: seconds_left = 0
    # ★ 修正計時器 JS，確保變數正確傳遞並強制執行
    timer_html = f"""
    <div style="font-family:'Arial';font-size:18px;font-weight:bold;color:white;background-color:#ff4b4b;padding:8px;border-radius:50px;text-align:center;width:70%;max-width:300px;margin:10px auto;box-shadow:1px 1px 3px rgba(0,0,0,0.3);">
        ⏱️ <span id="timer_val">{int(seconds_left)}</span> 秒
    </div>
    <script>
        (function() {{
            var timeleft = {seconds_left};
            var timerElement = document.getElementById("timer_val");
            
            // 清除可能存在的舊計時器
            if (window.gameTimer) clearInterval(window.gameTimer);
            
            window.gameTimer = setInterval(function(){{
                timeleft -= 1;
                if(timeleft <= 0){{
                    clearInterval(window.gameTimer);
                    if(timerElement) timerElement.innerHTML = "0";
                }} else {{
                    if(timerElement) timerElement.innerHTML = timeleft;
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
    lose_content = path_lose if os.path.exists(path_lose) else "💨"
    
    cards = [win_content] * target_count + [lose_content] * distractor_count
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

# ================= ★ 後台介面 (移除 column 限制，使用直接 Expander) ★ =================
st.divider()

# 不使用 st.columns，直接放 expander，並透過 CSS 控制寬度
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

```