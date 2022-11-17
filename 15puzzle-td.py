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
Delay = 3
HCells, VCells = 4, 4
Cells = HCells*VCells
CellSize = min(Width//HCells, Height//VCells)
Black, White, Grey = (0, 0, 0), (250, 250, 250), (120, 120, 120)

# puzzle class
class Puzzle:
	def __init__(self, gameCount, shuffleCount):
		# Set window caption
		caption = f"TD : Game {gameCount} shuffle {shuffleCount}"
		pygame.display.set_caption(caption)

		# 퍼즐을 초기화합니다.
		self.board = [k+1 for k in range(Cells)]
		self.empty = Cells-1

		# shuffle
		k = 0
		while k < shuffleCount or self.check() == 0:
			v = random.choice(list(Actions.values()))
			r, c = self.empty//HCells, self.empty%HCells
			nr, nc = r+v[0], c+v[1]
			# 옮겨야할 셀위치가 퍼즐 위치를 벗어나는 경우 무시
			if nr < 0 or nr >= VCells or nc < 0 or nc >= HCells: continue
			self.board[self.empty] = self.board[nr*HCells+nc]
			self.empty = nr*HCells+nc
			k += 1

		# 비어있는 칸의 숫자 넣기
		self.board[self.empty] = Cells

		# 마지막 움직인 퍼즐
		self.last = None

	# 퍼즐이 다 맞았는지 검사합니다.
	def check(self):
		for k in range(Cells-1):
			if self.board[k] != k+1: return 1
		return 0
	
	def action(self, a):
		d = Actions[a]
		r, c = self.empty//HCells, self.empty%HCells
		nr, nc = r+d[0], c+d[1]
		self.last = self.empty
		self.empty = nr*HCells+nc
		self.board[self.last] = self.board[self.empty]
		self.board[self.empty] = Cells
		self.alpha = 0.0
		return self.check()

	def preAction(self, a):
		d = Actions[a]
		r, c = self.empty//HCells, self.empty%HCells
		nr, nc = r+d[0], c+d[1]
		if nr < 0 or nr >= VCells or nc < 0 or nc >= HCells: return None, 0
		board=[self.board[k] for k in range(Cells)]
		board[self.empty] = board[nr*HCells+nc]
		board[nr*HCells+nc] = Cells
		return board, self.getMaxValue(board)

	def getStatus(self, board):
		s = ""
		for k in range(Cells):
			if board[k] >= 10: s += chr(ord('a')+board[k]-10)
			else: s += str(board[k])
		return s

	def update(self):
		# 이벤트를 처리합니다.
		for e in pygame.event.get():
			if e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
				return False
		return True

	def getMaxValue(self, board):
		v = 0.0
		for k in range(Cells):
			r, c = k//HCells, k%HCells
			if board[k] == k+1: continue
			x = board[k]-1
			er, ec = x//3, x%3
			v -= abs(r-er) + abs(c-ec)
		return v

	# 그림을 그립니다.
	def draw(self):
		display.fill( White )
		pygame.draw.rect(display, Grey,
			(Margin, Margin, CellSize*HCells, CellSize*VCells))
		pygame.draw.rect(display, Black,
			(Margin, Margin, CellSize*HCells, CellSize*VCells), 1)

		# 슬라이딩 퍼즐 그림을 그립니다.
		for k in range(Cells):
			r, c = k//HCells, k%HCells
			# 박스 그리기
			color = White
			if self.board[k] == Cells or k == self.last: continue
			pygame.draw.rect(display, color, (Margin+c*CellSize,
				Margin+r*CellSize, CellSize, CellSize))
			pygame.draw.rect(display, Black, (Margin+c*CellSize,
				Margin+r*CellSize, CellSize, CellSize), 1)
			# 박스 안에 글자 쓰기
			text = font.render(str(self.board[k]), True, (0, 0, 0))
			rect = text.get_rect()
			rect.center = (Margin+c*CellSize+CellSize//2,
						   Margin+r*CellSize+CellSize//2)
			display.blit(text, rect)
		# 애니메이션 셀 그리기
		if self.last != None:
			r, c = self.last//HCells, self.last%HCells
			er, ec = self.empty//HCells, self.empty%HCells
			x = Margin+(self.alpha*c+(1-self.alpha)*ec)*CellSize
			y = Margin+(self.alpha*r+(1-self.alpha)*er)*CellSize
			pygame.draw.rect(display, White, (x, y, CellSize, CellSize))
			pygame.draw.rect(display, Black, (x, y, CellSize, CellSize), 1)
			# 박스 안에 글자 쓰기
			s = str(self.board[self.last])
			text = font.render(s, True, Black)
			rect = text.get_rect()
			rect.center = (x+CellSize//2, y+CellSize//2)
			display.blit(text, rect)
			if self.alpha < 0.95: self.alpha += 0.1
		# 디스플레이를 업데이를 합니다.
		pygame.display.update()
		# FPS에 맞게 잠을 잡니다.
		time.sleep(1/FPS)
		#기본은 True를 반환
		return True
		
# 상태값 저장용
ss = dict()
with open("15puzzle-td.dat", "r") as f:
	while True:
		line = f.readline()
		if not line: break
		dt = line.split()
		ss[dt[0]] = float(dt[1])
ss['123456789abcdef0'] = 0.0

solvedCount, puzzleCount, maxSolvedMove = 0, 0, 0
isQuit = False
pygame.init()
# 그림을 그릴 디스플레이를 설정합니다.
display = pygame.display.set_mode(( Margin*2+HCells*CellSize,
	Margin*2+VCells*CellSize))
# 텍스트를 설정할 폰트 생성
font = pygame.font.Font('freesansbold.ttf', CellSize//2-1)
x, y = [], []
shuffleCount = 5
learning = 0.5
while not isQuit:
	puzzle = Puzzle(puzzleCount+1, shuffleCount)
	moveCount = 0
	maxMoveCount = min(shuffleCount+1, 100)
	while moveCount <= maxMoveCount:
		if puzzle.update() == False:
			isQuit = True
			break
		if puzzle.check() == 0: break
		status = puzzle.getStatus(puzzle.board)
		if status not in ss: ss[status] = puzzle.getMaxValue(puzzle.board)
		a, maxv = '', -1000000
		for k in Actions:
			ps, mv = puzzle.preAction(k)
			if ps == None: continue
			ps = puzzle.getStatus(ps)
			v = ss[ps] if ps in ss else mv
			if maxv < v: a, maxv = k, v
		ss[status] += learning*(-1+maxv-ss[status])
		moveCount += 1
		puzzle.action(a)
		for _ in range(Delay): puzzle.draw()
	if not isQuit:
		puzzleCount += 1
		solvedCount += 1 if moveCount <= maxMoveCount else 0
		solveRate = solvedCount*100/puzzleCount
		print(f"{solvedCount}/{puzzleCount}:{moveCount}mvs {solveRate:.1f}%")
		if solveRate > 75.0 and puzzleCount >= 10:
			solvedCount, puzzleCount = 0, 0
			shuffleCount += 1
	for _ in range(FPS): puzzle.draw()

pygame.quit()

with open("15puzzle-td.dat", "w") as f:
	for k in ss:
		f.write(f"{k} {ss[k]:.2f}\n")
