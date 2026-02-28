import streamlit as st
import requests
from bs4 import BeautifulSoup
import random
import time
import json

# --- ページ設定 ---
st.set_page_config(page_title="ポケモン クイズマスター", layout="centered")

# --- カスタムCSS（iPad向け・小学生向け） ---
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        height: 70px;
        font-size: 22px !important;
        border-radius: 15px;
        margin-bottom: 10px;
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
            
            # タイプを取得（2つある場合も考慮して繋げる）
            type1 = pokemon_info.get('type_1', '')
            type2 = pokemon_info.get('type_2', '')
            types = type1
            if type2:
                types += f"、{type2}"
            if not types:
                types = "？？？"
                
            desc = pokemon_info.get('text_1', pokemon_info.get('text_2', "せつめいデータがありません。"))
            
            return {
                "name": pokemon_info.get('name', "不明なポケモン"),
                "category": pokemon_info.get('bunrui', "？？？ポケモン"),
                "height": f"{pokemon_info.get('takasa', 0)}m",
                "description": desc,
                "types": types,
                # 画像は安定して取得できるPokeAPIの公式アートワークを使用
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
    
    if col1.button("5問"):
        st.session_state.target_numbers = random.sample(range(1, 1025), 5)
        st.session_state.stage = 'playing'
        st.rerun()
        
    if col2.button("10問"):
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
        if st.button("トップに戻ってやり直す"):
            st.session_state.stage = 'start'
            st.rerun()
        st.stop()

    st.write(f"### 第 {idx + 1} 問 / 全 {total} 問")
    
    # 🌟 説明文の中にある「ポケモンの名前」を「〇〇〇」に変換する処理
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
    
    # 1段階目のヒント（タイプ）
    if st.session_state.hints_shown == 0:
        if st.button("💡 1つめのヒントをみる（タイプ）"):
            st.session_state.hints_shown = 1
            st.rerun()
            
    if st.session_state.hints_shown >= 1:
        st.markdown(f'<div class="hint-box">【タイプ】: {pokemon["types"]}</div>', unsafe_allow_html=True)
        
        # 2段階目のヒント（名前の最初）
        if st.session_state.hints_shown == 1:
            if st.button("💡 2つめのヒントをみる（なまえの最初）"):
                st.session_state.hints_shown = 2
                st.rerun()
                
    if st.session_state.hints_shown >= 2:
        # 最初の1文字 + 残りの文字数分の〇を作成
        name_len = len(pokemon['name'])
        hint2_text = pokemon['name'][0] + "〇" * (name_len - 1)
        st.markdown(f'<div class="hint-box">【なまえ】: {hint2_text}</div>', unsafe_allow_html=True)
        
        # 3段階目のヒント（シルエット）
        if st.session_state.hints_shown == 2:
            if st.button("💡 3つめのヒントをみる（シルエット）"):
                st.session_state.hints_shown = 3
                st.rerun()

    if st.session_state.hints_shown >= 3:
        st.write("【シルエット】")
        # filter: brightness(0%); で画像を真っ黒にしています
        st.markdown(f"""
            <div style="text-align: center; background-color: white; border-radius: 15px; padding: 10px;">
                <img src="{pokemon['image_url']}" style="width: 250px; filter: brightness(0%);">
            </div>
        """, unsafe_allow_html=True)
        
    st.write("---")
    
    # 解答入力
    user_answer = st.text_input("ポケモンの 名前を いれてね！", key=f"ans_{idx}").strip()
    
    if st.button("これだ！ (判定)"):
        if user_answer == pokemon['name']:
            st.balloons()
            st.success("せいかい！ すごいぞ！")
            # 正解したら色付きの画像を表示
            st.image(pokemon['image_url'], width=200)
            st.session_state.score += 1
        else:
            st.error(f"ざんねん！ こたえは 「{pokemon['name']}」 だよ。")
            # 不正解でも色付きの画像を表示
            st.image(pokemon['image_url'], width=200)
            
        time.sleep(3) # 画像と答えを確認する時間を少し長めに
        
        # 次の問題へ進む準備
        if idx + 1 < total:
            st.session_state.current_idx += 1
            st.session_state.hints_shown = 0 # ヒント状態をリセット
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
        st.session_state.hints_shown = 0 # ヒント状態をリセット
        st.rerun()