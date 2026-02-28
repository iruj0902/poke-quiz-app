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

# --- カスタムCSS（iPad向け・小学生向けにボタンを大きくカラフルに） ---
st.markdown("""
    <style>
    /* スタート画面のボタンの色を分ける */
    div[data-testid="column"]:nth-of-type(1) button {
        background-color: #ff4b4b !important; /* 赤色 */
        color: white !important;
        border: none;
    }
    div[data-testid="column"]:nth-of-type(2) button {
        background-color: #1f77b4 !important; /* 青色 */
        color: white !important;
        border: none;
    }
    /* すべてのボタンの基本サイズ調整 */
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
    </style>
    """, unsafe_allow_html=True)

# --- データ取得関数 ---
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
            
            # 🌟 番号を日本語のタイプ名に変換する処理
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
    st.session_state.stage = 'start'
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = 0
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'hints_shown' not in st.session_state:
    st.session_state.hints_shown = 0

# --- メインロジック ---
st.title("🔴 ポケモン クイズマスター ⚪")

# 1. スタート画面
if st.session_state.stage == 'start':
    st.write("### 何問 挑戦（ちょうせん）する？")
    col1, col2 = st.columns(2)
    
    # 🌟 use_container_width=True でボタンを横幅いっぱいにする
    if col1.button("5問", use_container_width=True):
        st.session_state.target_numbers = random.sample(range(1, 1025), 5)
        st.session_state.stage = 'playing'
        st.rerun()
        
    if col2.button("10問", use_container_width=True):
        st.session_state.target_numbers = random.sample(range(1, 1025), 10)
        st.session_state.stage = 'playing'
        st.rerun()

# 2. クイズ画面
elif st.session_state.stage == 'playing':
    idx = st.session_state.current_idx
    total = len(st.session_state.target_numbers)
    
    zukan_num = st.session_state.target_numbers[idx]
    pokemon = get_pokemon_data(zukan_num)
    
    if pokemon is None:
        st.error("ごめんね、このポケモンのデータをうまく取れなかったみたい。")
        if st.button("トップに戻ってやり直す", use_container_width=True):
            st.session_state.stage = 'start'
            st.rerun()
        st.stop()

    st.write(f"### 第 {idx + 1} 問 / 全 {total} 問")
    
    # 説明文のマスキング
    masked_desc = pokemon['description'].replace(pokemon['name'], "〇〇〇")
    
    # 基本情報の表示
    st.markdown(f"""
    <div class="question-box">
        <p class="pokemon-info"><strong>【ぶんるい】</strong>: {pokemon['category']}</p>
        <p class="pokemon-info"><strong>【たかさ】</strong>: {pokemon['height']}</p>
        <p class="pokemon-info"><strong>【せつめい】</strong>:<br>{masked_desc}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # --- ヒント機能 ---
    st.write("---")
    
    if st.session_state.hints_shown == 0:
        if st.button("💡 1つめのヒントをみる（タイプ）", use_container_width=True):
            st.session_state.hints_shown = 1
            st.rerun()
            
    if st.session_state.hints_shown >= 1:
        st.markdown(f'<div class="hint-box">【タイプ】: {pokemon["types"]}</div>', unsafe_allow_html=True)
        
        if st.session_state.hints_shown == 1:
            if st.button("💡 2つめのヒントをみる（なまえの最初）", use_container_width=True):
                st.session_state.hints_shown = 2
                st.rerun()
                
    if st.session_state.hints_shown >= 2:
        name_len = len(pokemon['name'])
        hint2_text = pokemon['name'][0] + "〇" * (name_len - 1)
        st.markdown(f'<div class="hint-box">【なまえ】: {hint2_text}</div>', unsafe_allow_html=True)
        
        if st.session_state.hints_shown == 2:
            if st.button("💡 3つめのヒントをみる（シルエット）", use_container_width=True):
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
    
    if st.button("これだ！ (判定)", use_container_width=True):
        if user_answer == pokemon['name']:
            st.balloons()
            st.success("せいかい！ すごいぞ！")
            st.image(pokemon['image_url'], width=200)
            st.session_state.score += 1
        else:
            st.error(f"ざんねん！ こたえは 「{pokemon['name']}」 だよ。")
            st.image(pokemon['image_url'], width=200)
            
        time.sleep(3)
        
        if idx + 1 < total:
            st.session_state.current_idx += 1
            st.session_state.hints_shown = 0
            st.rerun()
        else:
            st.session_state.stage = 'finished'
            st.rerun()

# 3. 終了画面
elif st.session_state.stage == 'finished':
    st.write("## 終了（しゅうりょう）！")
    st.write(f"### きみの スコアは {st.session_state.score} / {len(st.session_state.target_numbers)} 点だったよ！")
    
    if st.button("もういちど あそぶ", use_container_width=True):
        st.session_state.stage = 'start'
        st.session_state.current_idx = 0
        st.session_state.score = 0
        st.session_state.hints_shown = 0
        st.rerun()