import socket
import random
import time
import numpy as np
import tensorflow as tf
from tensorflow import keras
import os.path
from collections import deque

MaxSize = 4096
MiniBatch = 256

class Game:
	# 학습한 데이터를 저장할 파일 패스를 설정합니다.
	cpPath = "reversi-deep4/cp_{0:06}.ckpt"
	
	def __init__(self):
		self.gameCount = 0

		# 머신러닝을 위한 파라미터들
		self.epochs = 3
		self.batch_size = 64

		# 강화학습을 위한 파라미터들
		self.alpha = 0.2		# 학습률
		self.gamma = 1.0		# 미래 가치 반영률

		# e-greedy(입실론 탐욕) 파라미터들
		self.epsilon = 1.0	  # 초기 입실론
		self.epsilonDecay = 0.999   # 입실론 값을 매 에피소드마다 얼마씩?
		self.epsilonMin = 0.01  # 학습이 계속될때 최소 입실론 값

		# 인공신경망을 만듭니다.
		self.buildModel()

		# 학습을 위해서 데이터 처리
		self.q = deque(maxlen=MaxSize)

	def connect(self):
		while True:
			self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			try:
				self.sock.connect(("127.0.0.1", 8791))
			except socket.error:
				print(f"connect : {socket.error.errno}")
				return False
			except socket.timeout:
				print("connect : socket timeout")
				time.sleep(1.0)
				continue
			break
		return True

	def close(self):
		self.sock.close()

	def recv(self):
		# 패킷의 길이를 읽어온다.
		buf = b""
		while len(buf) < 4:
			try:
				t = self.sock.recv(4-len(buf))
			except:
				return "et", str(socket.error)
			buf += t
		needed = int(buf.decode("ascii"))
		# 패킷 길이만큼 패킷을 읽어온다.
		buf = b""
		while len(buf) < needed:
			try:
				t = self.sock.recv(needed-len(buf))
			except:
				return "et", str(socket.error)
			buf += t
		ss = buf.decode("ascii").split()
		if ss[0] == "ab": return "ab", "abort"
		return ss[0], ss[1]

	def send(self, buf):
		try:
			self.sock.send(buf.encode("ascii"))
		except:
			print("Sending error")

	def preRun(self, p):
		try:
			self.send("%04d pr %04d"%(8, p))
		except:
			return False, None
		cmd, buf = self.recv()
		if cmd != "pr": return False, None
		return True, getStatus(buf)

	def onStart(self, buf):
		self.turn = int(buf)
		self.episode = []
		colors = ("", "White", "Black")
		print(f"Game {self.gameCount+1} {colors[self.turn]}")

	def onQuit(self, buf):
		self.gameCount += 1
		w, b = int(buf[:2]), int(buf[2:])
		win = (w > b) - (w < b)
		result = win+1 if self.turn == 1 else 1-win
		winText = ("Lose", "Draw", "Win")
		print(f"{winText[result]} W : {w}, B : {b}")
		# 최종 보상을 선택 : 1 : White win, -1 : Black win, 0 : Draw
		reward = win
		# 에피소드를 거꾸로 거슬러 올라가야한다.
		for st, v, nst, nv in self.episode[::-1]:
			rw = (1-self.alpha)*nv + self.alpha*reward
			self.q.append( (nst, rw) )
			rw = (1-self.alpha)*v + self.alpha*-reward
			self.q.append( (st, rw) )
			reward *= self.gamma
		# 에피소드값을 이용하여 리플레이를 하도록 합니다.
		if len(self.q) > MiniBatch: self.replay()
		return result

	def onBoard(self, buf):
		st, v, nst, nv, p = self.action(buf)
		if p < 0: return False
		self.send("%04d pt %4d"%(8, p))
		self.episode.append((st, v, nst, nv))
		return True

	def action(self, board):
		# hints : 이번턴에서 놓을 수 있는 자리
		hints = [i for i in range(64) if board[i] == "0"]
		st = getStatus(board)
		v = self.model.predict(np.array(st).reshape(1,64),verbose=0)[0,0]

		# e-greedy에 의해 입실론값 확률로 랜덤하게 선택
		if np.random.rand() <= self.epsilon:
			p = random.choice(hints)
			ret, nst = self.preRun(p)
			if not ret: return None, -1, 0
			nv = self.model.predict(np.array(nst).reshape(1,64),verbose=0)[0,0]
			return st, v, nst, nv, p

		# 놓을 수 있는 자리 중 가장 높은 값을 주는 것을 선택
		maxp, maxnst, maxv = -1, None, -100
		for h in hints:
			ret, nst = self.preRun(h)
			if not ret: return None, -1, 0
			nv = self.model.predict(np.array(nst).reshape(1,64),verbose=0)[0,0]
			if nv > maxv: maxp, maxnst, maxv = h, nst, nv
		return st, v, nst, maxv, maxp

	# 인공신경망 모델을 생성합니다.
	def buildModel(self):
		# keras sequential을 만드는데,
		self.model = keras.Sequential([
			keras.layers.Dense(1024, input_dim=64, activation='relu'),
			keras.layers.Dense(1024, activation='relu'),
			keras.layers.Dense(1, activation='tanh'),
		])
		# 설정한 모델을 컴파일합니다.
		self.model.compile(loss='mean_squared_error',
						   optimizer=keras.optimizers.Adam())

		# 학습한 데이터를 읽어서 모델에 적용합니다.
		dir = os.path.dirname(Game.cpPath)
		latest = tf.train.latest_checkpoint(dir)
		# 현재 학습한 것이 없는 경우는 무시토록 합니다.
		if not latest: return
		print(f"Load weights {latest}")
		# 현재 인공신경망 모델에 저장된 웨이트를 로드합니다.
		self.model.load_weights(latest)
		# cp_000000.ckpt, cp_001001.ckpt  뒤에 있는 숫자는 현재 학습한 횟수
		idx = latest.find("cp_")
		self.gameCount = int(latest[idx+3:idx+9])
		# e-greedy의 입실론 값을 gameCount를 이용해서 업데이트 합니다.
		self.epsilon *= self.epsilonDecay**self.gameCount
		if self.epsilon < self.epsilonMin: self.epsilon = self.epsilonMin

	# 인공신경망으로 학습을 하기 위한 리플레이
	def replay(self):
		# xarray 입력, yarray 출력을 이용하여 학습 진행
		v = random.sample(self.q, MiniBatch)
		xarray = np.array([ c[0] for c in v ])
		yarray = np.array([ c[1] for c in v ])
		r = self.model.fit(xarray, yarray,
				verbose=1 if self.gameCount%10==0 else 0,
				epochs = self.epochs,
				batch_size = self.batch_size)

		# e-greedy에서 입실론 값을 업데이트 합니다.
		if self.epsilon >= self.epsilonMin: self.epsilon *= self.epsilonDecay

		# 현재까지 학습한 데이터를 자동 저장합니다.
		if self.gameCount%10 != 0: return
		saveFile = Game.cpPath.format(self.gameCount)
		print(f"Save weights {saveFile}")
		self.model.save_weights(saveFile)
		
def getStatus(board):
	ref = (0.0, 1.0, -1.0, 0.0)
	return [ref[int(board[i])] for i in range(64)]

quitFlag = False
winlose = [0, 0, 0]
game = Game()

while not quitFlag:
	if not game.connect(): break

	episode = []
	while True:
		cmd, buf = game.recv()
		if cmd == "et":
			print(f"[et]Network Error!! : {buf}")
			break
		if cmd == "qt":
			w = game.onQuit(buf)
			winlose[w] += 1
			print(f"Wins: {winlose[2]}, Loses: {winlose[0]},",
				f"Draws: {winlose[1]}, {winlose[2]*100/(winlose[0]+winlose[1]+winlose[2]):.2f}%" )
			break
		if cmd == "ab":
			print("Game Abort!!")
			break
		if cmd == "st":
			game.onStart(buf)
		elif cmd == "bd":
			if not game.onBoard(buf): break

	game.close()
	time.sleep(1.0)

