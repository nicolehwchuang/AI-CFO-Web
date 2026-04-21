import streamlit as st
import google.generativeai as genai
import pandas as pd
import yfinance as yf  # 新增：抓取即時股價的工具

# --- 1. 網頁配置 ---
st.set_page_config(page_title="你的專屬 AI 財務長", page_icon="📈", layout="wide")
st.title("📈 你的專屬 AI 財務長 (自動計算版)")

with st.sidebar:
    st.header("🔑 系統設定")
    api_key = st.text_input("輸入 Gemini API Key:", type="password")
    st.info("💡 提示：台股代號請加 .TW (如 0050.TW)，美股直接輸入代號 (如 TSLA)")

# --- 2. 使用者輸入區 ---
col_left, col_right = st.columns([1, 1.5], gap="large")

with col_left:
    st.subheader("🎯 設定理財目標")
    target_name = st.text_input("目標名稱", value="30歲買房頭期款")
    target_amount = st.number_input("目標金額 (台幣)", min_value=0, value=3000000)
    target_years = st.slider("預計達成時間 (年)", 1, 30, 12)

with col_right:
    st.subheader("📂 編輯持股清單")
    # 將「目前市值」欄位換成「持股數量」
    default_data = pd.DataFrame([
        {"資產名稱": "台股基金/個股", "標的代號": "006208.TW", "持股數量": 5000},
        {"資產名稱": "美股/全球 ETF", "標的代號": "VT", "持股數量": 100},
        {"資產名稱": "現金儲蓄", "標的代號": "TWD", "持股數量": 150000},
    ])
    
    edited_df = st.data_editor(default_data, num_rows="dynamic", use_container_width=True)

st.divider()

# --- 3. 核心邏輯：自動抓取股價並計算市值 ---
if st.button("🚀 啟動 AI 深度理財分析", use_container_width=True):
    if not api_key:
        st.error("請在左側輸入 API Key！")
    else:
        with st.spinner('正在連線全球股市並計算即時市值...'):
            try:
                # 建立一個清單來儲存計算結果
                final_assets = []
                total_market_value = 0
                
                for index, row in edited_df.iterrows():
                    symbol = row["標的代號"]
                    shares = row["持股數量"]
                    
                    # 如果是現金 (TWD)，市值就等於數量
                    if symbol.upper() == "TWD":
                        current_price = 1.0
                        market_value = shares
                    else:
                        # 使用 yfinance 抓取即時價格
                        stock = yf.Ticker(symbol)
                        current_price = stock.history(period="1d")["Close"].iloc[-1]
                        # 簡單處理匯率（假設美股匯率 32，未來可再優化）
                        if ".TW" not in symbol:
                            current_price *= 32
                        market_value = shares * current_price
                    
                    total_market_value += market_value
                    final_assets.append({
                        "標的": symbol,
                        "持股數": shares,
                        "目前單價(約台幣)": round(current_price, 2),
                        "總市值": round(market_value, 0)
                    })

                # 將計算結果轉成 DataFrame 給 AI 看
                final_df = pd.DataFrame(final_assets)
                
                # 4. 呼叫 AI
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-flash-latest')
                
                prompt = f"""
                你現在是專業財務顧問。
                【使用者資產細節】：
                {final_df.to_string(index=False)}
                總市值：{total_market_value} 元台幣。

                【目標】：在 {target_years} 年內達成「{target_name}」，金額 {target_amount} 元。
                
                請分析：
                1. 各資產佔總資產的比例（%）。
                2. 根據「持股數量」與「市值」，判斷目前分散程度是否足夠。
                3. 給出達成目標所需的預期回報率建議。
                """

                response = model.generate_content(prompt)
                st.success("✨ 報告生成完畢！")
                st.table(final_df) # 讓使用者先看一眼自動算出來的市值表
                st.markdown(response.text)

            except Exception as e:
                st.error(f"資料讀取失敗，請檢查代號是否正確：{e}")
