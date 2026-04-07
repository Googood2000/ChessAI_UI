import chess
from typing import Tuple, Optional, Dict
from functools import lru_cache

# 棋子估值表
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

# 转置表：缓存已评估的棋位
TRANSPOSITION_TABLE: Dict[int, Tuple[int, int, int]] = {}  # {zobrist_hash: (score, depth, flag)}

# 位置估值表（中局）
POSITION_WEIGHTS = {
    chess.PAWN: [
        0, 0, 0, 0, 0, 0, 0, 0,
        5, 10, 10, -20, -20, 10, 10, 5,
        5, -5, -10, 0, 0, -10, -5, 5,
        0, 0, 0, 20, 20, 0, 0, 0,
        5, 5, 10, 25, 25, 10, 5, 5,
        10, 10, 20, 30, 30, 20, 10, 10,
        50, 50, 50, 50, 50, 50, 50, 50,
        0, 0, 0, 0, 0, 0, 0, 0
    ],
    chess.KNIGHT: [
        -50, -40, -30, -30, -30, -30, -40, -50,
        -40, -20, 0, 5, 5, 0, -20, -40,
        -30, 5, 10, 15, 15, 10, 5, -30,
        -30, 0, 15, 20, 20, 15, 0, -30,
        -30, 5, 15, 20, 20, 15, 5, -30,
        -30, 0, 10, 15, 15, 10, 0, -30,
        -40, -20, 0, 0, 0, 0, -20, -40,
        -50, -40, -30, -30, -30, -30, -40, -50
    ],
    chess.BISHOP: [
        -20, -10, -10, -10, -10, -10, -10, -20,
        -10, 5, 0, 0, 0, 0, 5, -10,
        -10, 10, 10, 10, 10, 10, 10, -10,
        -10, 0, 10, 10, 10, 10, 0, -10,
        -10, 5, 5, 10, 10, 5, 5, -10,
        -10, 0, 5, 10, 10, 5, 0, -10,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -20, -10, -10, -10, -10, -10, -10, -20
    ],
    chess.ROOK: [
        0, 0, 0, 5, 5, 0, 0, 0,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        5, 5, 5, 5, 5, 5, 5, 5,
        0, 0, 0, 0, 0, 0, 0, 0
    ],
    chess.QUEEN: [
        -20, -10, -10, -5, -5, -10, -10, -20,
        -10, 0, 5, 0, 0, 0, 0, -10,
        -10, 5, 5, 5, 5, 5, 0, -10,
        0, 0, 5, 5, 5, 5, 0, -5,
        -5, 0, 5, 5, 5, 5, 0, -5,
        -10, 0, 5, 5, 5, 5, 0, -10,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -20, -10, -10, -5, -5, -10, -10, -20
    ],
    chess.KING: [
        20, 30, 10, 0, 0, 10, 30, 20,
        20, 20, 0, 0, 0, 0, 20, 20,
        -10, -20, -20, -20, -20, -20, -20, -10,
        -20, -30, -30, -40, -40, -30, -30, -20,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30
    ]
}


def evaluate_board(board: chess.Board) -> int:
    """
    评估棋盘位置的价值（优化版）
    正值表示白方更优，负值表示黑方更优
    """
    # 检查游戏是否结束
    if board.is_checkmate():
        return -20000 if board.turn == chess.WHITE else 20000
    
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    
    score = 0
    
    # 直接评估棋盘状态，避免遍历所有格子
    # 使用棋盘的棋子列表而不是遍历所有64个方格
    for piece_type in chess.PIECE_TYPES:
        # 白方棋子
        white_pieces = board.pieces(piece_type, chess.WHITE)
        for square in white_pieces:
            piece_value = PIECE_VALUES[piece_type]
            position_bonus = POSITION_WEIGHTS[piece_type][square]
            score += piece_value + position_bonus
        
        # 黑方棋子
        black_pieces = board.pieces(piece_type, chess.BLACK)
        for square in black_pieces:
            piece_value = PIECE_VALUES[piece_type]
            position_bonus = POSITION_WEIGHTS[piece_type][square]
            score -= piece_value + position_bonus
    
    return score


def _score_move(board: chess.Board, move: chess.Move) -> int:
    """
    为着法评分，用于排序（MVV-LVA 启发式）
    优先评估能吃子的着法，特别是用小子吃大子的着法
    """
    try:
        # 如果是吃子着法，优先考虑
        if board.is_capture(move):
            # 对于 en passant 和普通吃子都适用
            captured_piece = board.piece_at(move.to_square)
            # en passant 时被吃子在其他位置
            if captured_piece is None and board.ep_square == move.to_square:
                captured_piece = board.piece_at(board.ep_square - 8 if board.turn == chess.WHITE else board.ep_square + 8)
            
            attacking_piece = board.piece_at(move.from_square)
            
            if captured_piece and attacking_piece:
                return PIECE_VALUES.get(captured_piece.piece_type, 0) * 100 - PIECE_VALUES.get(attacking_piece.piece_type, 0)
            return 50  # 吃子着法基础分
        
        # 如果是升变，给高分
        if move.promotion:
            return 1000 + PIECE_VALUES.get(move.promotion, 0)
        
        # 其他着法给低分
        return 0
    except:
        # 安全处理，遇到异常返回 0
        return 0


def _order_moves(board: chess.Board, moves: list) -> list:
    """
    对着法进行排序（启发式排序以提高 Alpha-Beta 剪枝效率）
    """
    return sorted(moves, key=lambda m: _score_move(board, m), reverse=True)


def minimax_alpha_beta(
    board: chess.Board,
    depth: int,
    alpha: int,
    beta: int,
    is_maximizing: bool,
    max_depth: int = 4
) -> Tuple[int, Optional[chess.Move]]:
    """
    Alpha-Beta 剪枝的 Minimax 算法（优化版本）
    
    Args:
        board: 当前棋盘状态
        depth: 当前搜索深度
        alpha: Alpha 值（最大化者的最低保证值）
        beta: Beta 值（最小化者的最高保证值）
        is_maximizing: 是否是最大化层
        max_depth: 最大搜索深度
    
    Returns:
        (评估值, 最佳着法)
    """
    # 检查转置表（使用 FEN 哈希）
    board_hash = hash(board.fen())
    if board_hash in TRANSPOSITION_TABLE:
        cached_score, cached_depth, cached_flag = TRANSPOSITION_TABLE[board_hash]
        if cached_depth >= depth:
            return cached_score, None
    
    # 终止条件：达到最大深度或游戏结束
    if depth == 0 or board.is_game_over():
        return evaluate_board(board), None
    
    legal_moves = list(board.legal_moves)
    
    # 如果没有合法着法
    if not legal_moves:
        return evaluate_board(board), None
    
    # 对着法进行排序，以提高剪枝效率
    legal_moves = _order_moves(board, legal_moves)
    
    best_move = None
    
    if is_maximizing:
        # 最大化层（白方）
        max_eval = float('-inf')
        for move in legal_moves:
            board.push(move)
            eval_score, _ = minimax_alpha_beta(
                board, depth - 1, alpha, beta, False, max_depth
            )
            board.pop()
            
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break  # Beta 剪枝
        
        # 存入转置表
        TRANSPOSITION_TABLE[board_hash] = (max_eval, depth, 'exact')
        return max_eval, best_move
    else:
        # 最小化层（黑方）
        min_eval = float('inf')
        for move in legal_moves:
            board.push(move)
            eval_score, _ = minimax_alpha_beta(
                board, depth - 1, alpha, beta, True, max_depth
            )
            board.pop()
            
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            
            beta = min(beta, eval_score)
            if beta <= alpha:
                break  # Alpha 剪枝
        
        # 存入转置表
        TRANSPOSITION_TABLE[board_hash] = (min_eval, depth, 'exact')
        return min_eval, best_move


def get_best_move(board: chess.Board, depth: int = 4, clear_cache: bool = False) -> Optional[chess.Move]:
    """
    获取当前棋盘位置的最佳着法
    使用 Alpha-Beta 剪枝的 Minimax 算法（优化版）
    
    Args:
        board: 当前棋盘状态
        depth: 搜索深度（默认为 4，越深越强但速度越慢）
        clear_cache: 是否清空转置表（默认不清空，可在新游戏时清空）
    
    Returns:
        最佳着法，如果没有合法着法则返回 None
    """
    # 清空转置表（可选，节省内存）
    if clear_cache:
        TRANSPOSITION_TABLE.clear()
    
    legal_moves = list(board.legal_moves)
    
    if not legal_moves:
        return None
    
    # 如果只有一个合法着法，直接返回
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    # 初始化 Alpha-Beta 值
    alpha = float('-inf')
    beta = float('inf')
    
    # 根据当前着法者确定是最大化还是最小化
    is_maximizing = (board.turn == chess.WHITE)
    
    _, best_move = minimax_alpha_beta(
        board, depth, alpha, beta, is_maximizing, max_depth=depth
    )
    
    return best_move if best_move else legal_moves[0]
