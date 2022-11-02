# nxm 슬라이딩 퍼즐 섞어놓기
import random
import time
import pygame
from pygame.locals import *

Margin = 10
FPS = 30
Actions = { 'Left':(0, -1), 'Right':(0, 1), 'Up':(-1, 0), 'Down':(1, 0) }
Width = 600
Height = 400
Delay = FPS//15
ShuffleCount = 30

# puzzle class
class Puzzle:
    # n : 세로칸의 크기, m : 가로칸의 크기
    def __init__(self, n, m):
        self.n = n
        self.m = m

        # 셀의 크기를 결정하도록 합니다.
        self.size = min(Width//m, Height//n)

        # 퍼즐을 초기화합니다.
        puzzle = [ [ r*m+c+1 for c in range(m) ] for r in range(n) ]

        # 비어있는 곳의 위치 설정
        self.emptyr, self.emptyc = n-1, m-1

		# shuffle
        for _ in range(ShuffleCount):
            v = random.randrange(4)
            r, c = self.emptyr, self.emptyc
            drc = ( (0, 1), (1, 0), (0, -1), (-1, 0) )
            nr, nc = r+drc[v][0], c+drc[v][1]
            # 옮겨야할 셀위치가 퍼즐 위치를 벗어나는 경우 무시
            if nr < 0 or nr >= n or nc < 0 or nc >= m: continue
            puzzle[r][c] = puzzle[nr][nc]
            # 비어있는 위치 업데이트
            self.emptyr, self.emptyc = nr, nc

        # 비어있는 칸의 숫자 넣기
        puzzle[self.emptyr][self.emptyc] = 0
        self.board = puzzle

        # pygame을 초기화합니다.
        pygame.init()

        # 그림을 그릴 디스플레이를 설정합니다.
        self.display = pygame.display.set_mode((Margin*2+m*self.size,
            Margin*2+n*self.size))

        # 텍스트를 설정할 폰트 생성
        self.font = pygame.font.Font('freesansbold.ttf', self.size//2-1)
        
        # 마지막 움직인 퍼즐
        self.last = None
        self.alpha = 1.0

    # 퍼즐이 다 맞았는지 검사합니다.
    def check(self):
        for r in range(self.n):
            for c in range(self.m):
                if (r != self.n-1 or c != self.m-1) and \
                   self.board[r][c] != r*self.m+c+1: return 1
        return 0
    
    def action(self, a):
        d = Actions[a]
        nr, nc = (self.emptyr+d[0], self.emptyc+d[1])
        self.board[self.emptyr][self.emptyc] = self.board[nr][nc]
        self.board[nr][nc] = 0
        self.last = (self.emptyr, self.emptyc)
        self.emptyr, self.emptyc = nr, nc
        self.alpha = 0.0
        return self.check()

    def preAction(self, a):
        d = Actions[a]
        nr, nc = (self.emptyr+d[0], self.emptyc+d[1])
        if nr < 0 or nr >= self.n or nc < 0 or nc >= self.m: return None, 0.0
        board=[[self.board[r][c] for c in range(self.m)] for r in range(self.n)]
        board[self.emptyr][self.emptyc] = board[nr][nc]
        board[nr][nc] = 0
        return self.getStatus(board), self.getMaxValue(board)

    def getStatus(self, board):
        s = ""
        for r in range(self.n):
            for c in range(self.m):
                if board[r][c] >= 10: s += chr(ord('a')+board[r][c]-10)
                else: s += str(board[r][c])
        return s

    def update(self):
        # 이벤트를 처리합니다.
        for e in pygame.event.get():
            if e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
                return False
        return True

    def getMaxValue(self, board):
        v = 0.0
        for r in range(self.n):
            for c in range(self.m):
                if board[r][c] != r*self.m+c+1:
                    if board[r][c] == 0: continue
                    x = board[r][c]-1
                    er, ec = x//3, x%3
                    v -= abs(r-er) + abs(c-ec)
        return v

    # 그림을 그립니다.
    def draw(self):
        # 윈도우를 하얀색으로 클리어
        display = self.display
        display.fill( (255, 255, 255) )

        # 슬라이딩 퍼즐 그림을 그립니다.
        puzzle = self.board
        for r in range(self.n):
            for c in range(self.m):
                # 박스 그리기
                color = (250, 250, 250)
                if puzzle[r][c] == 0 or (r, c) == self.last: color = (100, 100, 100)
                pygame.draw.rect(display, color, (Margin+c*self.size,
                    Margin+r*self.size, self.size, self.size))
                pygame.draw.rect(display, (0, 0, 0), (Margin+c*self.size,
                    Margin+r*self.size, self.size, self.size), 1)
                # 박스 안에 글자 쓰기
                if puzzle[r][c] == 0 or (r, c) == self.last: continue
                text = self.font.render(str(puzzle[r][c]), True, (0, 0, 0))
                rect = text.get_rect()
                rect.center = (Margin+c*self.size+self.size//2,
                               Margin+r*self.size+self.size//2)
                display.blit(text, rect)
        # 애니메이션 셀 그리기
        if self.last != None:
            x = Margin+(self.alpha*self.last[1]+(1-self.alpha)*self.emptyc)*self.size
            y = Margin+(self.alpha*self.last[0]+(1-self.alpha)*self.emptyr)*self.size
            pygame.draw.rect(display, (250, 250, 250), (x, y, self.size, self.size))
            pygame.draw.rect(display, (0, 0, 0), (x, y, self.size, self.size), 1)
            # 박스 안에 글자 쓰기
            text = self.font.render(str(puzzle[self.last[0]][self.last[1]]), True, (0, 0, 0))
            rect = text.get_rect()
            rect.center = (x+self.size//2, y+self.size//2)
            display.blit(text, rect)
            if self.alpha < 0.95: self.alpha += 0.2
        # 디스플레이를 업데이를 합니다.
        pygame.display.update()
        # FPS에 맞게 잠을 잡니다.
        time.sleep(1/FPS)
        #기본은 True를 반환
        return True

    # 종료를 합니다.
    def shutdown(self):
        pygame.quit()
        
ss = { '123456789abcdef0':0.0 }
with open("15-puzzle.dat", "r") as f:
	while True:
		line = f.readline()
		if not line: break
		dt = line.split()
		ss[dt[0]] = float(dt[1])
learning = 0.5
isQuit = False
while not isQuit:
    puzzle = Puzzle(4, 4)
    while True:
        if puzzle.update() == False:
            isQuit = True
            break
        status = puzzle.getStatus(puzzle.board)
        if status not in ss: ss[status] = puzzle.getMaxValue(puzzle.board)
        a, maxv = '', -1000000
        for k in Actions:
            ps, mv = puzzle.preAction(k)
            if ps == None: continue
            v = ss[ps] if ps in ss else mv
            if maxv < v: a, maxv = k, v
        ss[status] += learning*(-1+maxv-ss[status])
        if puzzle.action(a) == 0: break
        for _ in range(Delay): puzzle.draw()
    for _ in range(FPS*3): puzzle.draw()
    print("solved")
    puzzle.shutdown()

with open("15-puzzle.dat", "w") as f:
	for k in ss:
		f.write("%s %s\n"%(k, ss[k]))
