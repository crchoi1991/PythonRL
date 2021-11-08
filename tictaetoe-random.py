# Tic-Tae-Toe Random Game
# Random module import
import random

class TicTaeToe:
    def __init__(self):
        self.board = [0]*9
        self.aiTurn = random.randrange(1, 3)

    # turn이 pos 위치에 놓는다.
    def Put(self, turn, pos):
        self.board[pos] = turn

    # 경기가 끝났는지 검사
    def IsFinished(self):
        #  가로 검사
        for i in range(3):
            x = self.board[i*3]
            if x == 0: continue
            isFinish = True
            for j in range(3):
                if x != self.board[i*3+j]:
                    isFinish = False
                    break
            if isFinish: return x
        #   세로 검사
        for i in range(3):
            x = self.board[i]
            if x == 0: continue
            isFinish = True
            for j in range(3):
                if x != self.board[i+j*3]:
                    isFinish = False
                    break
            if isFinish: return x
        #  대각선 검사
        isFinish = True
        x = self.board[0]
        if x != 0:
            for i in range(3):
                if x != self.board[i*4]:
                    isFinish = False
                    break
            if isFinish: return x
        #  대각선 검사
        isFinish = True
        x = self.board[2]
        if x != 0:
            for i in range(3):
                if x != self.board[i*2+2]:
                    isFinish = False
                    break
            if isFinish: return x
        # all board is full
        isFinish = True
        for i in range(9):
            if self.board[i] == 0:
                isFinish = False
                break
        if isFinish: return 0
        return -1

    def Print(self):
        tt = (" ", "O", "X")
        print("+---+---+---+")
        print(f"| {tt[self.board[0]]} | {tt[self.board[1]]} | {tt[self.board[2]]} |") 
        print("+---+---+---+")
        print(f"| {tt[self.board[3]]} | {tt[self.board[4]]} | {tt[self.board[5]]} |") 
        print("+---+---+---+")
        print(f"| {tt[self.board[6]]} | {tt[self.board[7]]} | {tt[self.board[8]]} |") 
        print("+---+---+---+")

#  무한하게 게임 진행
while True:
    game = TicTaeToe()
    turn = 1
    while game.IsFinished() == -1:
        game.Print()
        cand = []
        for i in range(9):
            if game.board[i] == 0: cand.append(i)
        if turn == game.aiTurn:
            p = random.choice(cand)
            game.Put(turn, p)
        else:
            while True:
                p = int(input("pos : "))
                if p in cand: break
            game.Put(turn, p)
        turn ^= 3
    game.Print()
    rtext = ("Draw", "O Win", "X Win")
    print(rtext[game.IsFinished()])
    yn = input("Do you want more game : ")
    if yn != 'y' and yn != 'Y': break

    
