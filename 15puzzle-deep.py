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
ShuffleCount = 20

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
		self.board = puzzle

		# 비어있는 곳의 위치 설정
		self.emptyr, self.emptyc = n-1, m-1

		# shuffle
		while self.check() == 0:
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

		# pygame을 초기화합니다.
		pygame.init()

		# 그림을 그릴 디스플레이를 설정합니다.
		self.display = pygame.display.set_mode((Margin*2+m*self.size,
			Margin*2+n*self.size))

		# 텍스트를 설정할 폰트 생성
		self.font = pygame.font.Font('freesansbold.ttf', self.size//2-1)
		
		# 마지막 움직인 퍼즐
		self.last = None


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
		if nr < 0 or nr >= self.n or nc < 0 or nc >= self.m: return None
		board=[[self.board[r][c] for c in range(self.m)] for r in range(self.n)]
		board[self.emptyr][self.emptyc] = board[nr][nc]
		board[nr][nc] = 0
		return board

	def update(self):
		# 이벤트를 처리합니다.
		for e in pygame.event.get():
			if e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
				return False
		return True

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
			s = str(puzzle[self.last[0]][self.last[1]])
			text = self.font.render(s, True, (0, 0, 0))
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
		
import numpy as np
import tensorflow as tf
from tensorflow import keras
import os.path

CPath = "15puzzle-deep/cp_{0:06}.ckpt"
Epochs = 5
BatchSize = 32
Alpha = 0.1
Gamma = 1.0

gameCount = 0

def BuildModel():
	global gameCount
	model = keras.Sequential([
		keras.layers.Dense(32, input_dim=16, activation='relu'),
		keras.layers.Dense(64, activation='relu'),
		keras.layers.Dense(128, activation='relu'),
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

solvedCount = 0
puzzleCount = 0
isQuit = False
model = BuildModel()
while not isQuit:
	gameCount += 1
	print(f"Game {gameCount}")
	puzzle = Puzzle(4, 4)
	moveCount = 0
	x, y = [], []
	while moveCount <= min(ShuffleCount, 100):
		if puzzle.update() == False:
			isQuit = True
			break
		st = np.array([float(puzzle.board[r][c]) for r in range(4) for c in range(4)])
		if puzzle.check() == 0:
			x.append(st)
			y.append(0.0)
			break
		a, maxv = '', -1000000
		for k in Actions:
			ps = puzzle.preAction(k)
			if ps == None: continue
			nst = np.array([float(ps[r][c]) for r in range(4) for c in range(4)])
			v = model.predict(nst.reshape(1, 16), verbose=0)[0, 0]
			if maxv < v: a, maxv = k, v
		v = model.predict(st.reshape(1, 16), verbose=0)[0, 0]
		v += Alpha*(maxv-v-1)
		x.append(st)
		y.append(v)
		moveCount += 1
		puzzle.action(a)
		for _ in range(Delay): puzzle.draw()
	if not isQuit:
		puzzleCount += 1
		solvedCount += 1 if moveCount <= ShuffleCount else 0
		model.fit(np.array(x), np.array(y), epochs=Epochs, batch_size=BatchSize)
		solveRate = solvedCount*100/puzzleCount
		print(f"{solvedCount}/{puzzleCount}:{moveCount}mvs {solveRate:.1f}%")
		if gameCount%10 == 0: Save(model)
	for _ in range(FPS*3): puzzle.draw()
	puzzle.shutdown()

