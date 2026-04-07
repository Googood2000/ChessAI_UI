import chess
from typing import Tuple, Optional, Dict
from functools import lru_cache

# Chess Piece Valuation Table
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

# Transposition table: cache evaluated positions
TRANSPOSITION_TABLE: Dict[int, Tuple[int, int, int]] = {}  # {zobrist_hash: (score, depth, flag)}

# Position Evaluation Table (Midgame)
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
    Evaluate board position (optimized).
    Positive values favor White, negative values favor Black.
    """
    # Check for terminal game state
    if board.is_checkmate():
        return -20000 if board.turn == chess.WHITE else 20000
    
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    
    score = 0
    
    # Evaluate the board directly without scanning all 64 squares
    # Use the board's piece lists instead of iterating over every square
    for piece_type in chess.PIECE_TYPES:
        # White pieces
        white_pieces = board.pieces(piece_type, chess.WHITE)
        for square in white_pieces:
            piece_value = PIECE_VALUES[piece_type]
            position_bonus = POSITION_WEIGHTS[piece_type][square]
            score += piece_value + position_bonus
        
        # Black pieces
        black_pieces = board.pieces(piece_type, chess.BLACK)
        for square in black_pieces:
            piece_value = PIECE_VALUES[piece_type]
            position_bonus = POSITION_WEIGHTS[piece_type][square]
            score -= piece_value + position_bonus
    
    return score


def _score_move(board: chess.Board, move: chess.Move) -> int:
    """
    Score a move for ordering (MVV-LVA heuristic).
    Prioritize capture moves, especially when a smaller piece captures a larger one.
    """
    try:
        # Prioritize captures
        if board.is_capture(move):
            # For en passant and regular captures
            captured_piece = board.piece_at(move.to_square)
            # For en passant, the captured pawn is on a different square
            if captured_piece is None and board.ep_square == move.to_square:
                captured_piece = board.piece_at(board.ep_square - 8 if board.turn == chess.WHITE else board.ep_square + 8)
            
            attacking_piece = board.piece_at(move.from_square)
            
            if captured_piece and attacking_piece:
                return PIECE_VALUES.get(captured_piece.piece_type, 0) * 100 - PIECE_VALUES.get(attacking_piece.piece_type, 0)
            return 50  # Base score for captures
        
        # Give promotions a high score
        if move.promotion:
            return 1000 + PIECE_VALUES.get(move.promotion, 0)
        
        # Assign low score to other moves
        return 0
    except:
        # Safe fallback: return 0 on exceptions
        return 0


def _order_moves(board: chess.Board, moves: list) -> list:
    """
    Order moves to improve Alpha-Beta pruning efficiency.
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
    Optimized Minimax algorithm with Alpha-Beta pruning.
    
    Args:
        board: current board state
        depth: current search depth
        alpha: alpha value (lower bound for maximizing side)
        beta: beta value (upper bound for minimizing side)
        is_maximizing: whether this is a maximizing node
        max_depth: maximum search depth
    
    Returns:
        (evaluation score, best move)
    """
    # Check the transposition table (using FEN hash)
    board_hash = hash(board.fen())
    if board_hash in TRANSPOSITION_TABLE:
        cached_score, cached_depth, cached_flag = TRANSPOSITION_TABLE[board_hash]
        if cached_depth >= depth:
            return cached_score, None
    
    # Termination condition: reached max depth or game over
    if depth == 0 or board.is_game_over():
        return evaluate_board(board), None
    
    legal_moves = list(board.legal_moves)
    
    # If there are no legal moves
    if not legal_moves:
        return evaluate_board(board), None
    
    # Order moves to improve pruning efficiency
    legal_moves = _order_moves(board, legal_moves)
    
    best_move = None
    
    if is_maximizing:
        # Maximizing layer (White)
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
                break  # Beta cutoff
        
        # Store in transposition table
        TRANSPOSITION_TABLE[board_hash] = (max_eval, depth, 'exact')
        return max_eval, best_move
    else:
        # Minimizing layer (Black)
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
                break  # Alpha cutoff
        
        # Store in transposition table
        TRANSPOSITION_TABLE[board_hash] = (min_eval, depth, 'exact')
        return min_eval, best_move


def get_best_move(board: chess.Board, depth: int = 4, clear_cache: bool = False) -> Optional[chess.Move]:
    """
    Get the best move for the current board position.
    Uses an optimized Minimax algorithm with Alpha-Beta pruning.
    
    Args:
        board: current board state
        depth: search depth (default 4; deeper search is stronger but slower)
        clear_cache: whether to clear the transposition table (default false)
    
    Returns:
        best move, or None if no legal move exists
    """
    # Clear transposition table if requested
    if clear_cache:
        TRANSPOSITION_TABLE.clear()
    
    legal_moves = list(board.legal_moves)
    
    if not legal_moves:
        return None
    
    # If only one legal move exists, return it directly
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    # 初始化 Alpha-Beta 值
    alpha = float('-inf')
    beta = float('inf')
    
    # Determine whether this is a maximizing or minimizing position based on current turn
    is_maximizing = (board.turn == chess.WHITE)
    
    _, best_move = minimax_alpha_beta(
        board, depth, alpha, beta, is_maximizing, max_depth=depth
    )
    
    return best_move if best_move else legal_moves[0]
