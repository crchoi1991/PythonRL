import random
import time
import numpy as np
import tensorflow as tf
from tensorflow import keras
import os.path
from reversiclient import ReversiClient

cpPath = "reversi-shallow/cp_{0:06}.ckpt"

def getNextMove(model, board, turn):
	# hints : 이번턴에서 놓을 수 있는 자리
	hints = ReversiClient.getHints(board)

	# e-greedy에 의해 입실론값 확률로 랜덤하게 선택
	if random.random() <= epsilon:
		return random.choice(hints)

	# 놓을 수 있는 자리 중 가장 높은 값을 주는 것을 선택
	maxp, maxv = -1, -100
	for h in hints:
		ReversiClient.prerun(board[:], h, turn)
		state = getState(board, turn)
		v = model.predict(state.reshape(1, 64), verbose=0)[0, 0]
		if v > maxv: maxp, maxv = h, v
	return maxp

# 인공신경망 모델을 생성합니다.
def buildModel():
	global epsilon, gameCount
	# keras sequential을 만드는데,
	model = keras.Sequential([
		keras.layers.Dense(128, input_dim=64, activation='relu'),
		keras.layers.Dense(128, activation='relu'),
		keras.layers.Dense(1, activation='tanh'),
	])
	# 설정한 모델을 컴파일합니다.
	model.compile(loss='mean_squared_error',
					   optimizer=keras.optimizers.Adam())

	# 학습한 데이터를 읽어서 모델에 적용합니다.
	dir = os.path.dirname(cpPath)
	latest = tf.train.latest_checkpoint(dir)
	# 현재 학습한 것이 없는 경우는 무시토록 합니다.
	if not latest: return model
	print(f"Load weights {latest}")
	# 현재 인공신경망 모델에 저장된 웨이트를 로드합니다.
	model.load_weights(latest)
	# cp_000000.ckpt, cp_001001.ckpt  뒤에 있는 숫자는 현재 학습한 횟수
	idx = latest.find("cp_")
	gameCount = int(latest[idx+3:idx+9])
	# e-greedy의 입실론 값을 gameCount를 이용해서 업데이트 합니다.
	epsilon *= EpsilonDecay**gameCount
	if epsilon < EpsilonMin: epsilon = EpsilonMin
	return model

def learn(model, result, episode):
	# 최종 보상을 선택 : 1 : 이겼다, 0 : 졌다, 0.5 : 비겼을 경우
	reward = result-1
	# 학습을 위해서 데이터 처리
	print(episode.shape)
	y = model.predict(episode)
	# 에피소드를 거꾸로 거슬러 올라가야한다.
	for i in range(len(y)-1, -1, -1):
		y[i] += Alpha*(reward-y[i])
		reward *= -Gamma
	# 에피소드값을 이용하여 리플레이를 하도록 합니다.
	replay(model, episode, y)

# 인공신경망으로 학습을 하기 위한 리플레이
def replay(model, x, y):
	global epsilon
	# xarray 입력, yarray 출력을 이용하여 학습 진행
	r = model.fit(x, y, epochs = Epochs, batch_size = BatchSize)

	# e-greedy에서 입실론 값을 업데이트 합니다.
	if epsilon >= EpsilonMin: epsilon *= EpsilonDecay

	# 현재까지 학습한 데이터를 자동 저장합니다.
	if gameCount%10 != 0: return
	saveFile = cpPath.format(gameCount)
	print(f"Save weights {saveFile}")
	model.save_weights(saveFile)
		
def getState(board, turn):
	ref = ( 0, 1 if turn==1 else -1, 1 if turn==2 else -1, 0 )
	return np.array([ ref[x] for x in board ])

# 머신러닝을 위한 파라미터들
Epochs = 5
BatchSize = 32

# 강화학습을 위한 파라미터들
Alpha = 0.2				# 학습률
Gamma = 0.99			# 미래 가치 반영률

# e-greedy(입실론 탐욕) 파라미터들
epsilon = 1.0			# 초기 입실론
EpsilonDecay = 0.999	# 입실론 값을 매 에피소드마다 얼마씩?
EpsilonMin = 0.01  		# 학습이 계속될때 최소 입실론 값

Colors = ('', 'White', 'Black')
WinText = ('Lose', 'Draw', 'Win')
game = ReversiClient()
gameCount = 0
model = buildModel()
win = [0]*3
while True:
	if not game.connect('localhost'): break
	episode = np.empty((0, 64))
	while True:
		cmd, args = game.getEvent()
		if cmd == None: continue
		if cmd.startswith('Error'):
			print(cmd, args)
			break
		if cmd == 'start':
			turn = args[1]
			print(f'start a new game {gameCount+1} with color {Colors[turn]}')
		elif cmd == 'ready':
			place = getNextMove(model, args[0], turn)
			game.place(place)
		elif cmd == 'place':
			state = getState(args[0], args[2])
			episode = np.append( episode, state.reshape(1, 64), axis=0 )
		elif cmd == 'quit':
			gameCount += 1
			win[args[2]] += 1
			print(f'turn : {Colors[turn]},',
				f'White : {args[0]}, Black : {args[1]},',
				f'{WinText[args[2]]}')
			print(f'statistics : Lose : {win[0]},',
				f'Draw : {win[1]}, Win : {win[2]},',
				f'ratio : {win[2]*100/gameCount:.1f}%')
			learn(model, args[2], episode)
			break
		elif cmd == 'abort':
			print(*args)
			break
	game.close()
