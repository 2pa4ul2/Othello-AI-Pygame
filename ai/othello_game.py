#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module contains the main Othello game which maintains the board, score, and 
players.  

Thanks to original author Daniel Bauer, Columbia University
"""
import sys
import subprocess
from threading import Timer
from ai.display import Images, Draw, Fonts
from ai.othello_shared import find_lines, get_possible_moves, play_move, get_score

class InvalidMoveError(RuntimeError):
    pass

class AiTimeoutError(RuntimeError):
    pass

class Player(object):
    def __init__(self, color, name="Human"):
        self.name = name
        self.color = color

    def get_move(self, manager):
        pass  

class AiPlayerInterface(Player):

    TIMEOUT = 60

    def __init__(self, filename, player):
        
        l = 5   #limit
        m = 0   #minimax
        c = 0   #caching
        o = 1   #ordering

        self.process = subprocess.Popen([sys.executable, filename], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        name = self.process.stdout.readline().decode("ASCII").strip()
        print("AI introduced itself as: {}".format(name))
        #print(f"Subprocess PID: {self.process.pid}")
        
        self.name = name
        
        print(f"{player},{l},{m},{c},{o}\n")
        self.process.stdin.write(f"{player},{l},{m},{c},{o}\n".encode("ASCII"))
        self.process.stdin.flush()

    def timeout(self): 
        sys.stderr.write("{} timed out.".format(self.name))
        self.process.kill() 
        self.timed_out = True

    def get_move(self, manager):
        white_score, dark_score = get_score(manager.board)
        print(f"SCORE: W -> {white_score} B -> {dark_score}\n")
        #print(f"BOARD: {manager.board}\n")
        
        self.process.stdin.write(f"SCORE {white_score} {dark_score}\n".encode("ASCII"))
        self.process.stdin.flush()
        self.process.stdin.write(f"{manager.board}\n".encode("ASCII"))
        self.process.stdin.flush()
        

        timer = Timer(AiPlayerInterface.TIMEOUT, lambda: self.timeout())
        self.timed_out = False
        timer.start()

        # Wait for the AI call
        move_s = self.process.stdout.readline().decode("ASCII")
        print("MOVE_S:", move_s)
        if self.timed_out:  
            raise AiTimeoutError
        timer.cancel()
        i_s, j_s = move_s.strip().split()
        i = int(i_s)
        j = int(j_s)
        return i,j 
    
    def kill(self, manager):
        print("Subprocess KILL")
        white_score, dark_score = get_score(manager.board)
        self.process.stdin.write("FINAL {} {}\n".format(white_score, dark_score).encode("ASCII"))
        self.process.kill() 


class OthelloGameManager(object):

    def __init__(self, screen, current_state):
        self.dimension = 8
        self.board = self.create_initial_board()
        self.current_player = 1
        self.current_state = current_state
        self.black_score = 0
        self.white_score = 0
        self.img = Images(screen)
        self.draw = Draw(screen)
        self.font = Fonts()
        self.first_player = 'mcts'

    def clear_game(self):
        self.black_score = 0
        self.white_score = 0
        self.board = self.create_initial_board()
        self.current_player = 1

    def get_state(self):
        return self.current_state
    
    def set_state(self, state):
        self.current_state = state

    def set_scores(self, black_score, white_score):
        self.black_score = black_score
        self.white_score = white_score
            
    def create_initial_board(self):
        board = []
        for i in range(self.dimension): 
            row = []
            for j in range(self.dimension):
                row.append(0)
            board.append(row) 

        i = self.dimension // 2 -1
        j = self.dimension // 2 -1
        board[i][j] = 2
        board[i+1][j+1] = 2
        board[i+1][j] = 1
        board[i][j+1] = 1
        final = []
        for row in board: 
            final.append(tuple(row))
        return board

    def print_board(self):
        for row in self.board: 
            print(" ".join([str(x) for x in row]))
                   
    def play(self, i,j):
        if self.board[j][i] != 0:
           raise InvalidMoveError("Occupied square.")
        lines = find_lines(self.board, i,j, self.current_player)
        
        if not lines:  
           raise InvalidMoveError("Invalid Move.")
     
        self.board = play_move(self.board, self.current_player, i, j) 
        self.current_player = 1 if self.current_player == 2 else 2

    def get_possible_moves(self):
        return get_possible_moves(self.board, self.current_player)



def play_game(game, player1, player2):

    players = [None, player1, player2]

    while True: 
        player_obj = players[game.current_player]
        possible_moves = game.get_possible_moves() 
        if not possible_moves: 
            p1score, p2score = get_score(game.board)
            print("FINAL: {} (dark) {}:{} {} (light)".format(player1.name, p1score, p2score, player2.name))
            player1.kill(game)
            player2.kill(game)
            break 
        else: 
            color = "dark" if game.current_player == 1 else "light"
            try: 
                i, j = player_obj.get_move(game)
                print("{} ({}) plays {},{}".format(player_obj.name, color, i,j))
                game.play(i,j)
            except AiTimeoutError:
                print("{} ({}) timed out!".format(player_obj.name, color))
                print("FINAL: {} (dark) {}:{} {} (light)".format(player_obj.name, p1score, p2score, player2.name))
                player1.kill(game)
                player2.kill(game)
                break


