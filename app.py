import streamlit as st
import requests
from bs4 import BeautifulSoup
import random
import time

# --- ページ設定 ---
st.set_page_config(page_title="ポケモン クイズマスター", layout="centered")

# --- カスタムCSS（iPad向け・小学生向けにボタンを大きく） ---
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        height: 80px;
        font-size: 24px !important;
        border-radius: 20px;
    }
    .question-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 15px;
        border-left: 10px solid #ff4b4b;
        margin-bottom: 20px;
    }
    .pokemon-info {
        font-size: 20px;
        line-height: 1.6;
    }
    </style>
    """, unsafe_allow_html=True)

# --- データ取得関数 ---
def get_pokemon_data(zukan_number):
    """
    指定された図鑑番号のポケモン情報を公式サイトから取得
    """
    # 4桁の文字列に変換（例: 1 -> 0001）
    formatted_number = str(zukan_number).zfill(4)
    url = f"https://zukan.pokemon.co.jp/detail/{formatted_number}"
    
    try:
        response = requests.get(url)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # サイトの構造に合わせて抽出（※サイト仕様変更により調整が必要な場合があります）
        # JSONデータが埋め込まれていることが多いため、簡易的なパース例
        name = soup.find('p', class_='pokemon-slider__name')
        # 実際には公式サイトはJavaScriptで動的に描写されるため、
        # ここでは開発用として「取得失敗時のダミー」も考慮したロジックにしています
        
        # 注意: 公式サイトは動的コンテンツのため、BeautifulSoupのみでは取得が難しい場合があります。
        # 本来はAPIエンドポイントを叩くか、Selenium/Playwrightを検討しますが、
        # ここではプロトタイプとして「名前・分類・説明」の構造を定義します。
        
        return {
            "name": name.text.strip() if name else "フシギダネ", # 仮の取得例
            "category": "たねポケモン",
            "height": "0.7m",
            "description": "生まれたときから 背中に 植物の タネが あって 少しずつ 大きく 育つ。"
        }
    except Exception as e:
        return None

# --- セッション状態の初期化 ---
if 'stage' not in st.session_state:
    st.session_state.stage = 'start' # start, playing, finished
    st.session_state.questions = []
    st.session_state.current_idx = 0
    st.session_state.score = 0
    st.session_state.answer_feedback = ""

# --- メインロジック ---
st.title("🔴 ポケモン クイズマスター ⚪")

# 1. スタート画面
if st.session_state.stage == 'start':
    st.write("### 何問 挑戦（ちょうせん）する？")
    col1, col2 = st.columns(2)
    
    if col1.button("5問"):
        q_count = 5
        st.session_state.target_numbers = random.sample(range(1, 1025), q_count)
        st.session_state.stage = 'playing'
        st.rerun()
        
    if col2.button("10問"):
        q_count = 10
        st.session_state.target_numbers = random.sample(range(1, 1025), q_count)
        st.session_state.stage = 'playing'
        st.rerun()

# 2. クイズ画面
elif st.session_state.stage == 'playing':
    idx = st.session_state.current_idx
    total = len(st.session_state.target_numbers)
    
    # 現在のポケモンのデータを取得（キャッシュなしで毎回取得する簡易版）
    zukan_num = st.session_state.target_numbers[idx]
    pokemon = get_pokemon_data(zukan_num)
    
    st.write(f"### 第 {idx + 1} 問 / 全 {total} 問")
    
    # ヒントの表示
    st.markdown(f"""
    <div class="question-box">
        <p class="pokemon-info"><strong>【ぶんるい】</strong>: {pokemon['category']}</p>
        <p class="pokemon-info"><strong>【たかさ】</strong>: {pokemon['height']}</p>
        <p class="pokemon-info"><strong>【せつめい】</strong>:<br>{pokemon['description']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 解答入力
    user_answer = st.text_input("ポケモンの 名前を いれてね！", key=f"ans_{idx}").strip()
    
    if st.button("これだ！ (判定)"):
        if user_answer == pokemon['name']:
            st.balloons()
            st.success("せいかい！ すごいぞ！")
            st.session_state.score += 1
        else:
            st.error(f"ざんねん！ こたえは 「{pokemon['name']}」 だよ。")
        
        time.sleep(2) # 答えを確認する時間
        
        # 次の問題へ
        if idx + 1 < total:
            st.session_state.current_idx += 1
            st.rerun()
        else:
            st.session_state.stage = 'finished'
            st.rerun()

# 3. 終了画面
elif st.session_state.stage == 'finished':
    st.write("## 終了（しゅうりょう）！")
    st.write(f"### きみの スコアは {st.session_state.score} / {len(st.session_state.target_numbers)} 点だったよ！")
    
    if st.button("もういちど あそぶ"):
        st.session_state.stage = 'start'
        st.session_state.current_idx = 0
        st.session_state.score = 0
        st.rerun()
        