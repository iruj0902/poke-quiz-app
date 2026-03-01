import streamlit as st
import requests
from bs4 import BeautifulSoup
import random
import json
import pandas as pd
import streamlit.components.v1 as components

# --- タイプ変換用の辞書 ---
TYPE_MAP = {
    "1": "ノーマル", "2": "ほのお", "3": "みず", "4": "くさ", "5": "でんき",
    "6": "こおり", "7": "かくとう", "8": "どく", "9": "じめん", "10": "ひこう",
    "11": "エスパー", "12": "むし", "13": "いわ", "14": "ゴースト", "15": "ドラゴン",
    "16": "あく", "17": "はがね", "18": "フェアリー"
}

# --- 画面の一番上へスクロールさせる関数 ---
def scroll_to_top():
    js = '''
    <script>
        const elements = window.parent.document.querySelectorAll('.main, [data-testid="stAppViewContainer"], .stApp');
        elements.forEach(e => e.scrollTo({top: 0}));
    </script>
    '''
    components.html(js, height=0, width=0)

# --- 進化の段階を判定する関数 ---
def get_evolution_stage(zukan_number):
    try:
        species_url = f"https://pokeapi.co/api/v2/pokemon-species/{int(zukan_number)}/"
        res_species = requests.get(species_url).json()
        chain_url = res_species['evolution_chain']['url']
        
        res_chain = requests.get(chain_url).json()
        chain = res_chain['chain']
        
        def get_id(species_dict):
            return int(species_dict['url'].rstrip('/').split('/')[-1])
            
        base_id = get_id(chain['species'])
        stage1_nodes = chain['evolves_to']
        
        stage2_nodes = []
        for node in stage1_nodes:
            stage2_nodes.extend(node['evolves_to'])
            
        if len(stage1_nodes) == 0:
            return "進化なし"
        elif len(stage2_nodes) == 0:
            line_type = "1進化"
        else:
            line_type = "2進化"
            
        target_id = int(zukan_number)
        
        if target_id == base_id:
            return f"{line_type}のタネポケモン"
            
        for node in stage1_nodes:
            if get_id(node['species']) == target_id:
                if line_type == "1進化":
                    return "1進化の進化後"
                else:
                    return "2進化の1進化ポケモン"
                    
        for node in stage2_nodes:
            if get_id(node['species']) == target_id:
                return "2進化の2進化ポケモン"
                
        return "進化じょうほう ふめい"
    except Exception:
        return "進化じょうほう ふめい"

# --- データ取得関数 ---
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
        
        evo_stage = get_evolution_stage(zukan_number)
        
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
                "evolution_stage": evo_stage,
                "image_url": f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{int(zukan_number)}.png"
            }
        else:
            return None
    except Exception as e:
        return None

# --- ページ設定 ---
st.set_page_config(page_title="ポケモン クイズマスター", layout="centered")

# --- カスタムCSS ---
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
    .result-image-container {
        text-align: center;
        margin: 5px 0; 
        animation: fadeIn 0.5s;
    }
    .result-image-container h2 {
        margin-top: 5px;
        margin-bottom: 10px;
        color: #333;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: scale(0.9); }
        to { opacity: 1; transform: scale(1); }
    }
    </style>
    """, unsafe_allow_html=True)

# --- セッション状態の初期化 ---
if 'stage' not in st.session_state:
    st.session_state.stage = 'start'
if 'quiz_mode' not in st.session_state:
    st.session_state.quiz_mode = 'normal' # 'normal' または 'silhouette'
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = 0
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'hints_shown' not in st.session_state:
    st.session_state.hints_shown = 0
if 'is_correct' not in st.session_state:
    st.session_state.is_correct = False
if 'earned_points' not in st.session_state:
    st.session_state.earned_points = 0
if 'history' not in st.session_state:
    st.session_state.history = []

# --- メインロジック ---
st.title("🔴 ポケモン クイズマスター ⚪")

# 1. スタート画面
if st.session_state.stage == 'start':
    st.write("### どの クイズに 挑戦（ちょうせん）する？")
    col1, col2 = st.columns(2)
    
    if col1.button("👤 シルエットクイズ\n（5問）", use_container_width=True):
        st.session_state.target_numbers = random.sample(range(1, 1025), 5)
        st.session_state.quiz_mode = 'silhouette'
        st.session_state.stage = 'playing'
        st.rerun()
        
    if col2.button("📖 ポケモンクイズ\n（5問）", use_container_width=True, type="primary"):
        st.session_state.target_numbers = random.sample(range(1, 1025), 5)
        st.session_state.quiz_mode = 'normal'
        st.session_state.stage = 'playing'
        st.rerun()

# 2. クイズ画面
elif st.session_state.stage == 'playing':
    scroll_to_top()
    
    idx = st.session_state.current_idx
    total = len(st.session_state.target_numbers)
    
    zukan_num = st.session_state.target_numbers[idx]
    pokemon = get_pokemon_data(zukan_num)
    
    if pokemon is None:
        st.error("ごめんね、このポケモンのデータをうまく取れなかったみたい。")
        if st.button("次の問題へスキップ", use_container_width=True):
            st.session_state.current_idx += 1
            st.rerun()
        st.stop()

    st.write(f"### 第 {idx + 1} 問 / 全 {total} 問  (現在のスコア: {st.session_state.score}点)")
    
    # --- 🌟 モードによる表示の切り替え ---
    if st.session_state.quiz_mode == 'silhouette':
        # 【シルエットクイズモード】
        st.write("#### だれだか わかるかな？")
        st.markdown(f"""
            <div style="text-align: center; background-color: white; border-radius: 15px; padding: 20px; margin-bottom: 20px;">
                <img src="{pokemon['image_url']}" style="width: 280px; filter: brightness(0%);">
            </div>
        """, unsafe_allow_html=True)
        # 獲得できる得点は1点固定
        current_potential_points = 1
        
    else:
        # 【ポケモンクイズ（通常）モード】
        masked_desc = pokemon['description'].replace(pokemon['name'], "〇〇〇")
        
        st.markdown(f"""
        <div class="question-box">
            <p class="pokemon-info"><strong>【ぶんるい】</strong>: {pokemon['category']}</p>
            <p class="pokemon-info"><strong>【たかさ】</strong>: {pokemon['height']}</p>
            <p class="pokemon-info"><strong>【せつめい】</strong>:<br>{masked_desc}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("---")
        
        if st.session_state.hints_shown == 0:
            if st.button("💡 1つめのヒント（タイプ・進化）を見る", use_container_width=True):
                st.session_state.hints_shown = 1
                st.rerun()
                
        if st.session_state.hints_shown >= 1:
            st.markdown(f'''
                <div class="hint-box">
                    【タイプ】: {pokemon["types"]}<br>
                    【しんか】: {pokemon["evolution_stage"]}
                </div>
            ''', unsafe_allow_html=True)
            
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
                    <img src="{pokemon['image_url']}" style="width: 200px; filter: brightness(0%);">
                </div>
            """, unsafe_allow_html=True)
            
        # 獲得できる得点は 4 - ヒント数
        current_potential_points = 4 - st.session_state.hints_shown

    st.write("---")
    
    # 共通の解答欄
    user_answer = st.text_input("ポケモンの 名前を いれてね！", key=f"ans_{idx}").strip()
    
    if st.button("これだ！ (判定)", use_container_width=True, type="primary"):
        is_correct = (user_answer == pokemon['name'])
        earned_points = current_potential_points if is_correct else 0
        
        st.session_state.history.append({
            "問題": f"第{idx + 1}問",
            "あなたのこたえ": user_answer if user_answer else "（むかいとう）",
            "せいかい": pokemon['name'],
            "はんてい": "⭕️" if is_correct else "❌",
            "ゲット": f"{earned_points} 点"
        })
        
        st.session_state.is_correct = is_correct
        st.session_state.earned_points = earned_points
        if is_correct:
            st.session_state.score += earned_points
            
        st.session_state.stage = 'result'
        st.rerun()

# 3. 結果発表ポップアップ画面
elif st.session_state.stage == 'result':
    scroll_to_top()
    
    idx = st.session_state.current_idx
    total = len(st.session_state.target_numbers)
    zukan_num = st.session_state.target_numbers[idx]
    pokemon = get_pokemon_data(zukan_num)
    
    if st.session_state.is_correct:
        st.balloons()
        st.success(f"大せいかい！！ ✨ {st.session_state.earned_points} 点 ゲットだぜ！")
    else:
        st.error(f"ざんねん！ こたえは 「{pokemon['name']}」 だよ。")

    st.markdown(f"""
        <div class="result-image-container">
            <img src="{pokemon['image_url']}" style="width: 220px; max-width: 100%;">
            <h2>{pokemon['name']}</h2>
        </div>
    """, unsafe_allow_html=True)
    
    if idx + 1 < total:
        if st.button("▶ 次の もんだい へ！", use_container_width=True, type="primary"):
            st.session_state.current_idx += 1
            st.session_state.hints_shown = 0
            st.session_state.stage = 'playing'
            st.rerun()
    else:
        if st.button("🏆 けっか はっぴょう を見る！", use_container_width=True, type="primary"):
            st.session_state.stage = 'finished'
            st.rerun()

# 4. 終了画面
elif st.session_state.stage == 'finished':
    scroll_to_top()
    
    # モードによって満点が変わる（シルエットは5点、通常は20点）
    max_score = len(st.session_state.target_numbers) * (1 if st.session_state.quiz_mode == 'silhouette' else 4)
    
    st.write("## 終了（しゅうりょう）！")
    st.info(f"### きみの さいしゅうスコアは...  {st.session_state.score} / {max_score} 点！！")
    
    st.write("### 📝 今回の せいせきひょう")
    df_history = pd.DataFrame(st.session_state.history)
    st.table(df_history)
    
    st.write("---")
    
    if st.button("もういちど あそぶ", use_container_width=True, type="primary"):
        st.session_state.stage = 'start'
        st.session_state.current_idx = 0
        st.session_state.score = 0
        st.session_state.hints_shown = 0
        st.session_state.history = [] 
        st.rerun()