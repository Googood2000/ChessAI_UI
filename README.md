# Chess AI Game

A Python chess game with AI opponent using minimax algorithm, featuring a GUI built with Pygame.

## Features
- Play against an AI using minimax search with alpha-beta pruning
- Piece-square table evaluation for position assessment
- Undo/Redo moves
- Select player color (White or Black)
- Flip board view (vertical and horizontal)

## AI Engine
The AI uses the **minimax algorithm** with **alpha-beta pruning** for move selection:
- **Evaluation**: Piece values and position bonuses using piece-square tables
- **Search**: Minimax with alpha-beta pruning for efficiency
- **Depth**: Configurable search depth (default 4)

## Requirements
- Python 3.x
- pygame
- python-chess

## Installation
1. Install dependencies: `pip install -r requirements.txt`
2. Run: `python main.py`

## Controls
- Click on pieces to select and move
- Use buttons for undo, redo, flip, and color selection