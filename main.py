import pygame
import chess
import sys
from gui import ChessGUI

def main():
    pygame.init()
    gui = ChessGUI()
    gui.run()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()