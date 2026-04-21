%%writefile app.py
import streamlit as st
import google.generativeai as genai
import pandas as pd

# --- 1. 網頁配置 ---
st.set_page_config(page_title="你的專屬 AI 財務長", page_icon="🏦", layout="wide")

st.markdown("<h1 style='text-align: center;'>🏦 你的專屬 AI 財務長</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>輸入你真實的資產組合與理財目標，由 AI 提供專業配置建議</p>", unsafe_allow_html=True)

# 側邊欄設定
with st.sidebar:
    st.header("🔐 系統設定")
    api_key = st.text_input("請輸入 Gemini API Key:", type="password")
    st.divider()
    st.info("💡 提示：輸入資產時，建議填寫代號（如 2330, QQQ）AI 的分析會更精準。")

# --- 2. 介面切換：左邊設目標，右邊填資產 ---
col_left, col_right = st.columns([1, 1.2], gap="large")

with col_left:
    st.subheader("🎯 設定理財目標")
    target_name = st.text_input("你的夢想目標是？", value="30歲買房頭期款")
    target_amount = st.number_input("目標金額 (台幣)", min_value=0, value=3000000, step=100000)
    target_years = st.slider("預計幾年後達成？", 1, 30, 12)

with col_right:
    st.subheader("💰 編輯你的資產清單")
    st.write("您可以直接點擊下方表格修改內容或新增行數：")
    
    # 預設資料 (以妳的配置作為範例，但使用者可以隨意改)
    default_data = pd.DataFrame([
        {"資產名稱": "台股基金/個股", "標的代號": "006208", "目前市值": 498875},
        {"資產名稱": "美股/全球 ETF", "標的代號": "VT", "目前市值": 709269},
        {"資產名稱": "現金儲蓄", "標的代號": "TWD", "目前市值": 150000},
    ])
    
    # 建立一個互動式表格，讓使用者可以自由編輯
    edited_df = st.data_editor(
        default_data, 
        num_rows="dynamic", # 允許使用者點擊「+」新增行
        use_container_width=True
    )

st.divider()

# --- 3. 執行分析 ---
if st.button("🚀 啟動 AI 深度理財分析", use_container_width=True):
    
    if not api_key:
        st.error("請在左側側邊欄輸入 API Key！")
    else:
        # 計算總額
        total_value = edited_df["目前市值"].sum()
        
        with st.spinner('AI 正在讀取全球市場數據並為您規劃中...'):
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-flash-latest')

                # 將編輯後的表格轉成文字傳給 AI
                assets_str = edited_df.to_string(index=False)

                prompt = f"""
                你現在是一位精通全球金融市場的專業理財顧問。
                
                【使用者目前資產清單】：
                {assets_str}
                總市值：約 {total_value} 元台幣。

                【使用者的理財目標】：
                1. 目標：{target_name}
                2. 目標金額：{target_amount} 元台幣。
                3. 預計達成時間：{target_years} 年。

                請幫我完成以下任務，並以繁體中文回覆：
                1. [配置診斷]：根據使用者提供的具體標的代號，分析其風險分散程度與年化報酬潛力。
                2. [缺口精算]：考慮 {target_years} 年的時間與目標金額，計算目前達成率，並評估是否需要增加每月的儲蓄金額。
                3. [具體建議]：針對這份特定的資產組合，給出下個月的調倉或投資建議。
                4. [警示提醒]：對於這個目標，未來幾年有什麼潛在的經濟風險（如匯率、通膨）需要注意？
                """

                response = model.generate_content(prompt)
                
                st.success(f"✨ 針對「{target_name}」的 AI 評估報告已完成！")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"分析失敗，這通常與 API Key 或資料格式有關：{e}")
