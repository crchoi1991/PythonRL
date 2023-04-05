import socket
import random
import time
import numpy as np
import tensorflow as tf
from tensorflow import keras
from reversiclient import ReversiClient

# 인공신경망 모델을 생성합니다.
def buildModel():
	# keras sequential을 만드는데,
	# 첫번째 레이어는 64x1 형태이고
	# 활성함수는 linear(선형)로 설정합니다.
	model = keras.Sequential([
		keras.layers.Dense(1, input_dim=64, activation='linear'),
	])
	# 설정한 모델을 컴파일합니다.
	model.compile(loss='mean_squared_error', optimizer=keras.optimizers.Adam())
	# 현재 모델의 웨이트값을 읽어옵니다.
	#print(self.model.layers[0].get_weights()[0].shape)
	#print(self.model.layers[0].get_weights()[1].shape)
	# 현재 모델의 웨이트값을 설정합니다.
	w = (
		10, 1, 3, 2, 2, 3, 1, 10,
		1, -5, -1, -1, -1, -1, -5, 1,
		3, -1, 0, 0, 0, 0, -1, 3,
		2, -1, 0, 0, 0, 0, -1, 2,
		2, -1, 0, 0, 0, 0, -1, 2,
		3, -1, 0, 0, 0, 0, -1, 3,
		1, -5, -1, -1, -1, -1, -5, 1,
		10, 1, 3, 2, 2, 3, 1, 10)
	weights = np.array(w, dtype=float).reshape(64, 1)
	bias = np.zeros( (1, ) )
	model.layers[0].set_weights([weights, bias])
	return model

def getStatus(board, turn):
	# ref는 현재 인공지능이 흰돌이든 검은돌이든 모두 자기턴이
	# 흰돌인 것으로 변환하도록 하는 참조
	ref = (0.0, (turn==1)*2-1.0, (turn==2)*2-1.0, 0.0)
	return np.array([ref[board[i]] for i in range(64)])

def getNextMove(model, board, turn):
	hints = ReversiClient.getHints(board)
	# Randomized hints in order to prevent frequently occurring patterns.
	random.shuffle(hints)

	# Select maximum value's place
	maxp, maxnst, maxv = -1, None, -100
	for h in hints:
		ret = ReversiClient.prerun(board, h, turn)
		nst = getStatus(ret, turn)
		v = model.predict(nst.reshape(1, 64), verbose=0)[0, 0]
		if v > maxv: maxp, maxnst, maxv = h, nst, v
	return maxp, maxnst

Colors = ('', 'White', 'Black')
WinText = ('Lose', 'Draw', 'Win')
game = ReversiClient()
gameCount = 0
model = buildModel()
win = [0]*3
while True:
	if not game.connect('localhost'): break
	while True:
		cmd, args = game.getEvent()
		if cmd == None: continue
		if cmd.startswith('Error'):
			print(cmd, args)
			break
		if cmd == 'start':
			turn = args[0]
			print(f'start a new game {gameCount+1} with color {Colors[turn]}')
		elif cmd == 'ready':
			place, _ = getNextMove(model, args[0], turn)
			game.place(place)
		elif cmd == 'quit':
			gameCount += 1
			win[args[2]] += 1
			print(f'turn : {Colors[turn]}, White : {args[0]}, Black : {args[1]}, {WinText[args[2]]}')
			print(f'statistics : Lose : {win[0]}, Draw : {win[1]}, Win : {win[2]}, ratio : {win[2]*100/gameCount:.1f}%')
			break
		elif cmd == 'abort':
			print(*args)
			break
	game.close()
