import streamlit as st
import requests
from bs4 import BeautifulSoup
import random
import time
import json

# --- タイプ変換用の辞書 ---
TYPE_MAP = {
    "1": "ノーマル", "2": "ほのお", "3": "みず", "4": "くさ", "5": "でんき",
    "6": "こおり", "7": "かくとう", "8": "どく", "9": "じめん", "10": "ひこう",
    "11": "エスパー", "12": "むし", "13": "いわ", "14": "ゴースト", "15": "ドラゴン",
    "16": "あく", "17": "はがね", "18": "フェアリー"
}

# --- ページ設定 ---
st.set_page_config(page_title="ポケモン クイズマスター", layout="centered")

# --- カスタムCSS（基本サイズとレイアウト調整） ---
st.markdown("""
    <style>
    .stButton>button {
        height: 80px;
        font-size: 24px !important;
        border-radius: 15px;
        margin-bottom: 10px;
        font-weight: bold;
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
    .hint-box {
        background-color: #e6f3ff;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
        font-size: 20px;
        font-weight: bold;
    }
    /* 結果発表画面の画像用 */
    .result-image-container {
        text-align: center;
        margin: 20px 0;
        animation: fadeIn 0.5s;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: scale(0.9); }
        to { opacity: 1; transform: scale(1); }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 🌟 データ取得関数（キャッシュ化して爆速にする） ---
@st.cache_data(show_spinner=False)
def get_pokemon_data(zukan_number):
    formatted_number = str(zukan_number).zfill(4)
    url = f"https://zukan.pokemon.co.jp/detail/{formatted_number}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', id='json-data')
        
        if script_tag:
            data = json.loads(script_tag.string)
            pokemon_info = data.get('pokemon', {})
            
            type1_id = str(pokemon_info.get('type_1', ''))
            type2_id = str(pokemon_info.get('type_2', ''))
            
            type1_name = TYPE_MAP.get(type1_id, "")
            type2_name = TYPE_MAP.get(type2_id, "")
            
            types = type1_name
            if type2_name:
                types += f"、{type2_name}"
            if not types:
                types = "？？？"
                
            desc = pokemon_info.get('text_1', pokemon_info.get('text_2', "せつめいデータがありません。"))
            
            return {
                "name": pokemon_info.get('name', "不明なポケモン"),
                "category": pokemon_info.get('bunrui', "？？？ポケモン"),
                "height": f"{pokemon_info.get('takasa', 0)}m",
                "description": desc,
                "types": types,
                "image_url": f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{int(zukan_number)}.png"
            }
        else:
            return None
    except Exception as e:
        return None

# --- セッション状態の初期化 ---
if 'stage' not in st.session_state:
    st.session_state.stage = 'start' # start, playing, result, finished に状態を分けます
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = 0
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'hints_shown' not in st.session_state:
    st.session_state.hints_shown = 0
# 新しく追加する状態
if 'is_correct' not in st.session_state:
    st.session_state.is_correct = False
if 'earned_points' not in st.session_state:
    st.session_state.earned_points = 0

# --- メインロジック ---
st.title("🔴 ポケモン クイズマスター ⚪")

# 1. スタート画面
if st.session_state.stage == 'start':
    st.write("### 何問 挑戦（ちょうせん）する？")
    col1, col2 = st.columns(2)
    
    # type="primary" で赤色などの目立つ色にする
    if col1.button("5問", use_container_width=True, type="primary"):
        st.session_state.target_numbers = random.sample(range(1, 1025), 5)
        st.session_state.stage = 'playing'
        st.rerun()
        
    if col2.button("10問", use_container_width=True):
        st.session_state.target_numbers = random.sample(range(1, 1025), 10)
        st.session_state.stage = 'playing'
        st.rerun()

# 2. クイズ画面（問題出題中）
elif st.session_state.stage == 'playing':
    idx = st.session_state.current_idx
    total = len(st.session_state.target_numbers)
    
    zukan_num = st.session_state.target_numbers[idx]
    pokemon = get_pokemon_data(zukan_num) # キャッシュが効くので一瞬で取得！
    
    if pokemon is None:
        st.error("ごめんね、このポケモンのデータをうまく取れなかったみたい。")
        if st.button("次の問題へスキップ", use_container_width=True):
            st.session_state.current_idx += 1
            st.rerun()
        st.stop()

    # 右上に現在のスコアを表示
    st.write(f"### 第 {idx + 1} 問 / 全 {total} 問  (現在のスコア: {st.session_state.score}点)")
    
    masked_desc = pokemon['description'].replace(pokemon['name'], "〇〇〇")
    
    st.markdown(f"""
    <div class="question-box">
        <p class="pokemon-info"><strong>【ぶんるい】</strong>: {pokemon['category']}</p>
        <p class="pokemon-info"><strong>【たかさ】</strong>: {pokemon['height']}</p>
        <p class="pokemon-info"><strong>【せつめい】</strong>:<br>{masked_desc}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("---")
    
    # ヒント機能
    if st.session_state.hints_shown == 0:
        if st.button("💡 1つめのヒント（タイプ）を見る", use_container_width=True):
            st.session_state.hints_shown = 1
            st.rerun()
            
    if st.session_state.hints_shown >= 1:
        st.markdown(f'<div class="hint-box">【タイプ】: {pokemon["types"]}</div>', unsafe_allow_html=True)
        if st.session_state.hints_shown == 1:
            if st.button("💡 2つめのヒント（なまえの最初）を見る", use_container_width=True):
                st.session_state.hints_shown = 2
                st.rerun()
                
    if st.session_state.hints_shown >= 2:
        name_len = len(pokemon['name'])
        hint2_text = pokemon['name'][0] + "〇" * (name_len - 1)
        st.markdown(f'<div class="hint-box">【なまえ】: {hint2_text}</div>', unsafe_allow_html=True)
        if st.session_state.hints_shown == 2:
            if st.button("💡 3つめのヒント（シルエット）を見る", use_container_width=True):
                st.session_state.hints_shown = 3
                st.rerun()

    if st.session_state.hints_shown >= 3:
        st.write("【シルエット】")
        st.markdown(f"""
            <div style="text-align: center; background-color: white; border-radius: 15px; padding: 10px;">
                <img src="{pokemon['image_url']}" style="width: 250px; filter: brightness(0%);">
            </div>
        """, unsafe_allow_html=True)
        
    st.write("---")
    
    # 解答入力
    user_answer = st.text_input("ポケモンの 名前を いれてね！", key=f"ans_{idx}").strip()
    
    if st.button("これだ！ (判定)", use_container_width=True, type="primary"):
        if user_answer == pokemon['name']:
            st.session_state.is_correct = True
            # 🌟 ヒントの数に応じてポイント計算（4 - ヒント数）
            st.session_state.earned_points = 4 - st.session_state.hints_shown
            st.session_state.score += st.session_state.earned_points
        else:
            st.session_state.is_correct = False
            st.session_state.earned_points = 0
            
        # 結果発表画面へ移動
        st.session_state.stage = 'result'
        st.rerun()

# 3. 🌟 新設：結果発表ポップアップ画面
elif st.session_state.stage == 'result':
    idx = st.session_state.current_idx
    zukan_num = st.session_state.target_numbers[idx]
    pokemon = get_pokemon_data(zukan_num)
    
    if st.session_state.is_correct:
        st.balloons()
        st.success(f"大せいかい！！ ✨ {st.session_state.earned_points} 点 ゲットだぜ！")
    else:
        st.error(f"ざんねん！ こたえは 「{pokemon['name']}」 だよ。")

    # 画像を画面の中央に大きく表示
    st.markdown(f"""
        <div class="result-image-container">
            <img src="{pokemon['image_url']}" style="width: 350px; max-width: 100%;">
            <h2 style="color: #333;">{pokemon['name']}</h2>
        </div>
    """, unsafe_allow_html=True)
    
    # お子様が画像を見るための待機時間（3秒）
    time.sleep(3)
    
    # 次の問題、または終了画面へ自動移行
    if idx + 1 < len(st.session_state.target_numbers):
        st.session_state.current_idx += 1
        st.session_state.hints_shown = 0
        st.session_state.stage = 'playing'
        st.rerun()
    else:
        st.session_state.stage = 'finished'
        st.rerun()

# 4. 終了画面
elif st.session_state.stage == 'finished':
    max_score = len(st.session_state.target_numbers) * 4
    
    st.write("## 終了（しゅうりょう）！")
    st.info(f"### きみの さいしゅうスコアは...  {st.session_state.score} / {max_score} 点！！")
    
    if st.button("もういちど あそぶ", use_container_width=True, type="primary"):
        st.session_state.stage = 'start'
        st.session_state.current_idx = 0
        st.session_state.score = 0
        st.session_state.hints_shown = 0
        st.rerun()