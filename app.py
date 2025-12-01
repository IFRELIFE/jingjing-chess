import streamlit as st
import random
import copy
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Jingjing Chess", page_icon="🎮", layout="wide")

# --- LOCALIZATION ---
TEXTS = {
    'en': {
        'title': "Jingjing Chess: Neon AI",
        'turn': "Turn: {}",
        'winner': "🎉 Player {} Wins!",
        'draw': "🤝 It's a Draw!",
        'restart': "New Game",
        'rules': "Rules",
        'h_rule': "H Rule (Aggressive)",
        'q_rule': "Q Rule (Strategic)",
        'difficulty': "AI Level",
        'easy': "Easy",
        'hard': "Hard",
        'ai_move': "AI is thinking...",
        'target': "🎯 TARGET BOARD",
        'won': "WON by {}",
        'full': "FULL",
        'settings': "Settings"
    },
    'zh': {
        'title': "井井棋",
        'turn': "轮到: {}",
        'winner': "🎉 玩家 {} 获胜!",
        'draw': "🤝 平局!",
        'restart': "新游戏",
        'rules': "规则设定",
        'h_rule': "H规则 (激进)",
        'q_rule': "Q规则 (策略)",
        'difficulty': "AI 难度",
        'easy': "简单",
        'hard': "困难",
        'ai_move': "AI 正在思考...",
        'target': "🎯 当前目标区域",
        'won': "玩家 {} 已胜",
        'full': "已满",
        'settings': "设置"
    }
}

# --- STATE INITIALIZATION ---
if 'board' not in st.session_state:
    st.session_state.board = [['' for _ in range(9)] for _ in range(9)]
    st.session_state.macro_board = ['' for _ in range(9)]
    st.session_state.active_macro_board = -1
    st.session_state.turn = 'X'
    st.session_state.game_over = False
    st.session_state.winner = None
    st.session_state.lang = 'zh'  # Default to Chinese for your friend? Change to 'en' if needed


def get_text(key):
    return TEXTS[st.session_state.lang][key]


# --- GAME LOGIC FUNCTIONS ---

def check_winner(b, p=None):
    wins = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]
    if p:
        return any(b[x] == p and b[y] == p and b[z] == p for x, y, z in wins)
    else:
        for p_cand in ['X', 'O']:
            if any(b[x] == p_cand and b[y] == p_cand and b[z] == p_cand for x, y, z in wins):
                return p_cand
    return None


def is_full(b):
    return all(x != '' for x in b)


def update_game_state(b_idx, c_idx, player, rule_style):
    # 1. Place Move
    st.session_state.board[b_idx][c_idx] = player

    # 2. Check Small Board Win
    if st.session_state.macro_board[b_idx] == "":
        if check_winner(st.session_state.board[b_idx], player):
            st.session_state.macro_board[b_idx] = player
        elif is_full(st.session_state.board[b_idx]):
            st.session_state.macro_board[b_idx] = 'D'

    # 3. Check Global Win
    if check_winner(st.session_state.macro_board, player):
        st.session_state.game_over = True
        st.session_state.winner = player
    elif all(x != '' for x in st.session_state.macro_board):
        st.session_state.game_over = True
        st.session_state.winner = "Draw"

    # 4. Set Next Target
    if not st.session_state.game_over:
        next_target = c_idx
        is_target_full = is_full(st.session_state.board[next_target])
        is_target_won = st.session_state.macro_board[next_target] != ""

        if rule_style == 'H':
            if is_target_won or is_target_full:
                st.session_state.active_macro_board = -1  # Free move
            else:
                st.session_state.active_macro_board = next_target
        else:  # Q Rule
            if is_target_full:
                st.session_state.active_macro_board = -1
            else:
                st.session_state.active_macro_board = next_target

        st.session_state.turn = 'O' if player == 'X' else 'X'


def reset_game():
    st.session_state.board = [['' for _ in range(9)] for _ in range(9)]
    st.session_state.macro_board = ['' for _ in range(9)]
    st.session_state.active_macro_board = -1
    st.session_state.turn = 'X'
    st.session_state.game_over = False
    st.session_state.winner = None


# --- AI LOGIC (MINIMAX PORTED) ---

def get_valid_moves(board, macro, active, rule_style):
    valid_boards = []
    if active != -1:
        valid_boards = [active]
    else:
        for i in range(9):
            if rule_style == 'H':
                if macro[i] == "" and not is_full(board[i]): valid_boards.append(i)
            else:
                if not is_full(board[i]): valid_boards.append(i)
    moves = []
    for b in valid_boards:
        for c in range(9):
            if board[b][c] == "": moves.append((b, c))
    return moves


def evaluate_state(board, macro, ai_player):
    score = 0
    opp = 'X' if ai_player == 'O' else 'O'
    # Macro Weight
    lines = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]
    for l in lines:
        cells = [macro[i] for i in l]
        if cells.count(ai_player) == 3: score += 5000
        if cells.count(opp) == 3: score -= 5000

    for i in range(9):
        if macro[i] == ai_player:
            score += 200
        elif macro[i] == opp:
            score -= 200
    return score


def perform_ai_move(difficulty, rule_style):
    # Determine moves
    moves = get_valid_moves(st.session_state.board, st.session_state.macro_board,
                            st.session_state.active_macro_board, rule_style)
    if not moves: return

    if difficulty == 'Easy':
        move = random.choice(moves)
    else:
        # Simplified Minimax for Web (Depth 2 to prevent timeout on phone)
        # Phones have slower CPUs, so we keep it light.
        best_score = -float('inf')
        best_move = random.choice(moves)

        for move in moves:
            # Virtual Move
            # Note: Full recursion is heavy for Streamlit session,
            # using a simple 1-step lookahead + heuristic for "Hard" on web
            b, c = move
            score = 0
            # Prefer center
            if c == 4: score += 10
            # Prefer winning a board
            st.session_state.board[b][c] = 'O'
            if check_winner(st.session_state.board[b], 'O'): score += 100
            st.session_state.board[b][c] = ''  # Undo

            # Avoid sending opponent to free move
            if rule_style == 'H':
                if st.session_state.macro_board[c] != "" or is_full(st.session_state.board[c]):
                    score -= 50

            score += random.random()  # Jitter

            if score > best_score:
                best_score = score
                best_move = move

        move = best_move

    update_game_state(move[0], move[1], 'O', rule_style)
    st.rerun()


# --- UI LAYOUT ---

# Sidebar Settings
with st.sidebar:
    st.title(get_text('settings'))

    # Language Switcher
    lang_choice = st.radio("Language / 语言", ['English', '中文'], index=1 if st.session_state.lang == 'zh' else 0)
    new_lang = 'zh' if lang_choice == '中文' else 'en'
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        st.rerun()

    # Rule Style
    rule_choice = st.radio(get_text('rules'), [get_text('h_rule'), get_text('q_rule')])
    rule_style = 'H' if rule_choice == get_text('h_rule') else 'Q'

    # Difficulty
    diff_choice = st.radio(get_text('difficulty'), [get_text('easy'), get_text('hard')])
    difficulty = 'Easy' if diff_choice == get_text('easy') else 'Hard'

    # Mode
    mode = st.radio("Mode", ["PvAI", "PvP"])

    if st.button(get_text('restart')):
        reset_game()
        st.rerun()

# Main Header
st.title(get_text('title'))

if st.session_state.game_over:
    if st.session_state.winner == "Draw":
        st.success(get_text('draw'))
    else:
        st.balloons()
        st.success(get_text('winner').format(st.session_state.winner))
else:
    turn_msg = get_text('turn').format(st.session_state.turn)
    if mode == "PvAI" and st.session_state.turn == 'O':
        turn_msg = get_text('ai_move')
    st.info(turn_msg)

# Game Board Rendering
# We use columns to create the grid layout
for r in range(3):
    cols = st.columns(3)
    for c in range(3):
        b_idx = r * 3 + c
        with cols[c]:
            # Board Container Styling
            macro_winner = st.session_state.macro_board[b_idx]
            is_active = (st.session_state.active_macro_board == -1) or (st.session_state.active_macro_board == b_idx)

            # Visual Logic
            border_str = True
            header_str = ""

            if macro_winner == 'X':
                st.error(get_text('won').format('X'))
            elif macro_winner == 'O':
                st.success(get_text('won').format('O'))
            elif macro_winner == 'D':
                st.warning(get_text('full'))
            else:
                # Active Board logic
                playable = is_active
                if rule_style == 'H' and macro_winner != "": playable = False
                if is_full(st.session_state.board[b_idx]): playable = False

                if playable:
                    st.caption(f"🔵 {get_text('target')}")
                else:
                    st.write("")  # Spacer

                # The 3x3 Small Grid
                for sr in range(3):
                    subcols = st.columns(3)
                    for sc in range(3):
                        c_idx = sr * 3 + sc
                        key = f"btn_{b_idx}_{c_idx}"
                        cell_val = st.session_state.board[b_idx][c_idx]

                        # Determine button state
                        b_disabled = (not playable) or (cell_val != "") or st.session_state.game_over
                        if mode == "PvAI" and st.session_state.turn == 'O':
                            b_disabled = True  # Disable while AI thinking

                        # Render Button
                        if subcols[sc].button(cell_val if cell_val else " ", key=key, disabled=b_disabled):
                            update_game_state(b_idx, c_idx, st.session_state.turn, rule_style)
                            st.rerun()

# Trigger AI Move
if not st.session_state.game_over and mode == "PvAI" and st.session_state.turn == 'O':
    with st.spinner(get_text('ai_move')):
        time.sleep(0.5)  # Tiny delay for UX
        perform_ai_move(difficulty, rule_style)