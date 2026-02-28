import streamlit as st
import requests
from bs4 import BeautifulSoup
import random
import time
import json

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
    公式サイトのHTML内に埋め込まれたJSONデータから情報を取得する
    """
    formatted_number = str(zukan_number).zfill(4)
    url = f"https://zukan.pokemon.co.jp/detail/{formatted_number}"
    
    # 公式サイトのアクセス拒否を防ぐため、ブラウザからのアクセスを装う
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # id="json-data" の中にポケモン情報が隠れているので探す
        script_tag = soup.find('script', id='json-data')
        
        if script_tag:
            # 文字列を辞書型（JSON）に変換
            data = json.loads(script_tag.string)
            pokemon_info = data.get('pokemon', {})
            
            # 必要な情報（分類、高さ、説明文）を取り出す
            return {
                "name": pokemon_info.get('name', "不明なポケモン"),
                "category": pokemon_info.get('bunrui', "？？？ポケモン"),  # 公式サイトのキー名(bunrui)に合わせる
                "height": f"{pokemon_info.get('takasa', 0)}m",         # 公式サイトのキー名(takasa)に合わせる
                # 説明文は text_1 か text_2 に入っていることが多い
                "description": pokemon_info.get('text_1', pokemon_info.get('text_2', "説明データがありません。"))
            }
        else:
            return None
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
    
    if pokemon is None:
        st.error("ごめんね、このポケモンのデータをうまく取れなかったみたい。")
        if st.button("トップに戻ってやり直す"):
            st.session_state.stage = 'start'
            st.rerun()
        st.stop() # ここでいったん処理を止める
    
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
        