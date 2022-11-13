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
HCells, VCells = 4, 4
Cells = HCells*VCells
CellSize = min(Width//HCells, Height//VCells)
Black, White, Grey = (0, 0, 0), (250, 250, 250), (120, 120, 120)

ShuffleCount = 60

# puzzle class
class Puzzle:
	def __init__(self):
		# 퍼즐을 초기화합니다.
		self.board = [k+1 for k in range(Cells)]
		self.empty = Cells-1

		# shuffle
		k = 0
		while k < ShuffleCount or self.check() == 0:
			v = random.choice(list(Actions.values()))
			r, c = self.empty//HCells, self.empty%HCells
			nr, nc = r+v[0], c+v[1]
			k += 1
			# 옮겨야할 셀위치가 퍼즐 위치를 벗어나는 경우 무시
			if nr < 0 or nr >= VCells or nc < 0 or nc >= HCells: continue
			self.board[self.empty] = self.board[nr*HCells+nc]
			self.empty = nr*HCells+nc

		# 비어있는 칸의 숫자 넣기
		self.board[self.empty] = 0

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
		self.board[self.empty] = 0
		self.alpha = 0.0
		return self.check()

	def preAction(self, a):
		d = Actions[a]
		r, c = self.empty//HCells, self.empty%HCells
		nr, nc = r+d[0], c+d[1]
		if nr < 0 or nr >= VCells or nc < 0 or nc >= HCells: return None, 0
		board=[self.board[k] for k in range(Cells)]
		board[self.empty] = board[nr*HCells+nc]
		board[nr*HCells+nc] = 0
		return board, nr*HCells+nc

	def update(self):
		# 이벤트를 처리합니다.
		for e in pygame.event.get():
			if e.type == QUIT: return False
			if e.type == KEYUP and e.key == K_ESCAPE: return False
		return True

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
			if self.board[k] == 0 or k == self.last: continue
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
			if self.alpha < 0.95: self.alpha += 0.2
		# 디스플레이를 업데이를 합니다.
		pygame.display.update()
		# FPS에 맞게 잠을 잡니다.
		time.sleep(1/FPS)
		#기본은 True를 반환
		return True
		
import numpy as np
import tensorflow as tf
from tensorflow import keras
import os.path

CPath = "15puzzle-deep1/cp_{0:06}.ckpt"
Epochs = 5
BatchSize = 32
Alpha = 0.3
Gamma = 1.0
LSize = 2048

gameCount = 0

def BuildModel():
	global gameCount
	model = keras.Sequential([
		keras.layers.Dense(64, input_dim=16, activation='relu'),
		keras.layers.Dense(128, activation='relu'),
		keras.layers.Dense(256, activation='relu'),
		keras.layers.Dense(128, activation='relu'),
		keras.layers.Dense(1, activation='linear')
	])
	model.compile(loss='mean_squared_error',
		optimizer=keras.optimizers.Adam())
		
	# 학습한 데이터를 읽어서 모델에 적용합니다.
	dir = os.path.dirname(CPath)
	latest = tf.train.latest_checkpoint(dir)
	# 현재 학습한 것이 없는 경우는 무시토록 합니다.
	if latest:
		print(f"Load weights {latest}")
		# 현재 인공신경망 모델에 저장된 웨이트를 로드합니다.
		model.load_weights(latest)
		idx = latest.find("cp_")
		gameCount = int(latest[idx+3:idx+9])
	return model

def Save(model):
	saveFile = CPath.format(gameCount)
	print(f"Save weights {saveFile}")
	model.save_weights(saveFile)

solvedCount, puzzleCount, maxSolvedMove = 0, 0, 0
isQuit = False
model = BuildModel()
pygame.init()
# 그림을 그릴 디스플레이를 설정합니다.
display = pygame.display.set_mode(( Margin*2+HCells*CellSize,
	Margin*2+VCells*CellSize))
# 텍스트를 설정할 폰트 생성
font = pygame.font.Font('freesansbold.ttf', CellSize//2-1)
x, y = [], []
while not isQuit:
	gameCount += 1
	print(f"Game {gameCount}")
	puzzle = Puzzle()
	moveCount = 0
	maxMoveCount = min(ShuffleCount+1, 100)
	while moveCount <= maxMoveCount:
		if puzzle.update() == False:
			isQuit = True
			break
		st = np.array(puzzle.board)
		if puzzle.check() == 0:
			x.append(st)
			y.append(0.0)
			break
		a, maxv = '', -1000000
		for k in Actions:
			ps, e = puzzle.preAction(k)
			if ps == None or e == puzzle.last: continue
			nst = np.array(ps)
			v = model.predict(nst.reshape(1, 16), verbose=0)[0, 0]
			if maxv < v: a, maxv = k, v
		print(f"({a}, {maxv:.2f})", end=' ')
		v = model.predict(st.reshape(1, 16), verbose=0)[0, 0]
		v += Alpha*(Gamma*maxv-v-1)
		x.append(st)
		y.append(v)
		moveCount += 1
		puzzle.action(a)
		for _ in range(Delay): puzzle.draw()
	if not isQuit:
		puzzleCount += 1
		if moveCount <= maxMoveCount:
			solvedCount += 1
			if maxSolvedMove < moveCount: maxSolvedMove = moveCount
		if len(x) > LSize: x, y = x[-LSize:], y[-LSize:]
		model.fit(np.array(x), np.array(y), epochs=Epochs,
			batch_size=BatchSize)
		solveRate = solvedCount*100/puzzleCount
		print(f"{solvedCount}/{puzzleCount} {solveRate:.1f}%")
		print(f"Moves : {moveCount}/{maxSolvedMove}")
		if gameCount%10 == 0: Save(model)
	for _ in range(FPS): puzzle.draw()

pygame.quit()

