# nxm 슬라이딩 퍼즐 섞어놓기
import random
import time
import pygame
from pygame.locals import *
from collections import deque
import sys
import math
import matplotlib.pyplot as plt

HCells, VCells = 4, 4
if len(sys.argv) == 3:
	HCells = int(sys.argv[1])
	VCells = int(sys.argv[2])

Margin = 10
FPS = 30
Actions = ( (0, -1), (-1, 0), (0, 1), (1, 0) )
Delay = 10
Cells = HCells*VCells
CellSize = 100
Black, White, Grey = (0, 0, 0), (250, 250, 250), (120, 120, 120)
InitScores = [1, 1, 1, 0]*10
MaxMoveCount = VCells*HCells**2+HCells*VCells**2
PlotRange, PlotInt = 200, 100

# puzzle class
class Puzzle:
	def __init__(self, gameCount, shuffleCount):
		# Set window caption
		caption = f"DQN8 : Game {gameCount} shuffle {shuffleCount}"
		pygame.display.set_caption(caption)

		# 퍼즐을 초기화합니다.
		self.board = [k+1 for k in range(Cells)]
		self.empty = Cells-1

		# shuffle
		k = 0
		while k < shuffleCount or self.check() == 0:
			v = random.choice(Actions)
			r, c = self.empty//HCells, self.empty%HCells
			nr, nc = r+v[0], c+v[1]
			k += 1
			# 옮겨야할 셀위치가 퍼즐 위치를 벗어나는 경우 무시
			if nr < 0 or nr >= VCells or nc < 0 or nc >= HCells: continue
			self.board[self.empty] = self.board[nr*HCells+nc]
			self.empty = nr*HCells+nc

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
		if nr < 0 or nr >= VCells or nc < 0 or nc >= HCells: return
		self.last = self.empty
		self.empty = nr*HCells+nc
		self.board[self.last] = self.board[self.empty]
		self.board[self.empty] = Cells
		self.alpha = 0.0

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
		
import numpy as np
import tensorflow as tf
from tensorflow import keras
import os.path

CPath = "npuzzle-dqn8/cp_{0:07}.ckpt"
Epochs = 3
BatchSize = 32
Alpha = 0.4
Gamma = 1.0
LSize = 10000
MiniBatch = 256
Neighbors = ( (-1, -1), (-1, 0), (-1, 1), 
		(0, -1), (0, 1), 
		(1, -1), (1, 0), (1, 1),
		(-2, -1), (-2, 0), (-2, 1),
		(-1, -2), (0, -2), (1, 2),
		(-1, 2), (0, 2), (1, 2),
		(2, -1), (2, 0), (2, 1),
		(-2, -2), (-2, 2), (2, 2), (2, -2),
		(-3, 0), (0, -3), (3, 0), (0, 3), 
		(-3, -1), (-3, 1), (-1, -3), (1, -3),
		(3, -1), (3, 1), (-1, 3), (1, 3))
InputSize = len(Neighbors)*3

gameCount = 0

def BuildModel():
	global gameCount
	model = keras.Sequential([
		keras.layers.Dense(512, input_dim=InputSize, activation='relu'),
		keras.layers.Dense(1024, activation='relu'),
		keras.layers.Dense(512, activation='relu'),
		keras.layers.Dense(4, activation='sigmoid')
	])
	model.compile(loss='mean_squared_error', optimizer=keras.optimizers.Adam())
		
	# 학습한 데이터를 읽어서 모델에 적용합니다.
	dir = os.path.dirname(CPath)
	latest = tf.train.latest_checkpoint(dir)
	# 현재 학습한 것이 없는 경우는 무시토록 합니다.
	if latest:
		print(f"Load weights {latest}")
		# 현재 인공신경망 모델에 저장된 웨이트를 로드합니다.
		model.load_weights(latest)
		idx = latest.find("cp_")
		gameCount = int(latest[idx+3:idx+10])
	return model

def Save(model):
	saveFile = CPath.format(gameCount)
	print(f"Save weights {saveFile}")
	model.save_weights(saveFile)

def GetStatus(board):
	for i in range(Cells):
		if board[i]==Cells: empty = i
	er, ec = empty//HCells, empty%HCells
	s = []
	for r, c in Neighbors:
		nr, nc = er+r, ec+c
		if nr < 0 or nr >= VCells or nc < 0 or nc >= HCells:
			s.append(0)
			s.append(0)
			s.append(0)
		else:
			n = nr*HCells+nc
			tr, tc = (board[n]-1)//HCells, (board[n]-1)%HCells
			s.append(1)
			s.append(tr-nr)
			s.append(tc-nc)
	return s

def GetEvent():
	# 이벤트를 처리합니다.
	for e in pygame.event.get():
		if e.type == QUIT: return 1
		if e.type == KEYUP and e.key == K_ESCAPE: return 1
		if e.type == KEYUP and e.key == K_x: return 2
		if e.type == KEYUP and e.key == K_z: return 3
	return 0

def Normalize(v):
	s = 0.00001
	for k in v: s += k**2
	s = math.sqrt(s)
	for i in range(len(v)): v[i] /= s

solvedCount, puzzleCount, maxSolvedMove = 0, 0, 0
isQuit, isShow, isShowGraph = False, True, True
model = BuildModel()
pygame.init()
# 그림을 그릴 디스플레이를 설정합니다.
display = pygame.display.set_mode(( Margin*2+HCells*CellSize,
	Margin*2+VCells*CellSize))
# 텍스트를 설정할 폰트 생성
font = pygame.font.Font('freesansbold.ttf', CellSize//2-1)

queue = deque(maxlen=LSize)
shuffleCount = 90
scores = deque(InitScores, maxlen=50)
meanMoves = deque(maxlen=PlotInt*20)
movePlot = deque(maxlen=PlotRange)
shufflePlot = deque(maxlen=PlotRange)
indexPlot = deque(maxlen=PlotRange)
fig, ax = plt.subplots(figsize=(6.5, 3.8))
axr = ax.twinx()
plt.style.use(['bmh'])
while not isQuit:
	gameCount += 1
	puzzle = Puzzle(gameCount, shuffleCount)
	moveCount = 0
	maxMoveCount = min(shuffleCount+10, MaxMoveCount)
	epx, epv, epa = [], [], []
	while moveCount <= maxMoveCount:
		ev = GetEvent()
		if ev == 1:
			isQuit = True
			break
		if ev == 2: isShow = not isShow
		if ev == 3: isShowGraph = not isShowGraph
		if puzzle.check() == 0: break
		st = GetStatus(puzzle.board)
		v = model.predict(np.array([st]), verbose=0)[0]
		a = np.argmax(v)
		if st in epx:
			moveCount = maxMoveCount
		else:
			epx.append(st)
			epv.append(v)
			epa.append(a)
		moveCount += 1
		puzzle.action(a)
		if isShow:
			for _ in range(Delay): puzzle.draw()
	if not isQuit:
		puzzleCount += 1
		dest = 0
		if moveCount <= maxMoveCount:
			solvedCount += 1
			if maxSolvedMove < moveCount: maxSolvedMove = moveCount
			dest = 1
			meanMoves.append(moveCount)
			plt.get_current_fig_manager().set_window_title(
				f'move graph {solvedCount} {isShowGraph}')
			if solvedCount%PlotInt == 0:
				movePlot.append(sum(meanMoves)/len(meanMoves))
				shufflePlot.append(shuffleCount)
				indexPlot.append(gameCount/1000)
				ax.clear()
				axr.clear()
				ax.plot(indexPlot, movePlot, 'b-')
				axr.plot(indexPlot, shufflePlot, 'k--')
				plt.tight_layout(pad=0.5)
				if isShowGraph: plt.pause(0.01)
		scores.append(dest)
		for i in range(len(epv)):
			v = epv[i]
			a = epa[i]
			v[a] += (dest-v[a])*Alpha
			#Normalize(v)
			for xx, yy in queue:
				if xx == epx[i]:
					queue.remove((xx, yy))
					break
			queue.append( (epx[i], v) )
		rs = random.sample(queue, min(MiniBatch, len(queue)))
		xx = np.array([rs[i][0] for i in range(len(rs))])
		yy = np.array([rs[i][1] for i in range(len(rs))])
		model.fit(xx, yy, epochs=Epochs, batch_size=BatchSize, 
			verbose=0 if gameCount%50!=0 else 1)
		solveRate = solvedCount*100/puzzleCount
		print(f"{solvedCount}/{puzzleCount} {solveRate:.2f}%",
			f"Moves : {moveCount}/{maxSolvedMove} ({sum(scores)})")
		if gameCount%50 == 0: Save(model)
		count = sum(scores)
		if count < 25 or count > 39: 
			scores = deque(InitScores, maxlen=50)
			shuffleCount += 1 if count > 37 else -1
			print(f"Shuffle Count to {shuffleCount}")
	if isShow:
		for _ in range(FPS): puzzle.draw()

pygame.quit()

