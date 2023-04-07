import socket
import random
import time
import numpy as np
from queue import Queue

ByteOrder='little'

class ReversiClient:
	Commands = { 
		'start' : 'onStart', 
		'quit' : 'onQuit', 
		'ready' : 'onReady',
		'place' : 'onPlace',
	}
	def __init__(self):
		self.buf = b''
		self.needed = 0

	def connect(self, hostname, port=8791):
		self.queue = Queue()
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.settimeout(2)
		for _ in range(10):
			try:
				self.sock.connect((hostname, port))
			except socket.error:
				print(f"connect : {socket.error.errno}")
				return False
			except socket.timeout:
				time.sleep(1.0)
			else: return True
		print("connect : maximum trials is exceed")
		return True

	def close(self):
		self.sock.close()

	def getEvent(self):
		self.recv()
		if self.queue.empty(): return None, []
		return self.queue.get()

	def recv(self):
		# read packet header
		if self.needed == 0:
			try: t = self.sock.recv(4-len(self.buf))
			except socket.timeout: return
			except:
				self.queue.put(('ErrorSocket', ['recv header']))
				return
			if not len(t):
				self.queue.put(('ErrorSocket', ['peer connection closed']))
				return
			self.buf += t
			if len(self.buf) < 4: return
			self.needed = int.from_bytes(self.buf, ByteOrder)
			self.buf = b''

		# read packet data those length is needed
		if len(self.buf) < self.needed:
			try: t = self.sock.recv(self.needed-len(self.buf))
			except socket.Timeouterror: return
			except:
				self.queue.put((ReversiClient.ErrorSocket, ['recv message']))
				return
			if not len(t):
				self.queue.put(('ErrorSocket', ['peer connection closed']))
				return
			self.buf += t
			if len(self.buf) < self.needed: return
			self.needed = 0
			cmd, *args = self.buf.decode("ascii").split()
			self.buf = b''
			if cmd not in ReversiClient.Commands:
				self.queue.put((cmd, args))
				return
			getattr(self, ReversiClient.Commands[cmd])(*args)

	def send(self, mesg):
		pl = (len(mesg)).to_bytes(4, ByteOrder)
		try:
			self.sock.send(pl)
			self.sock.send(mesg.encode("ascii"))
		except:
			self.queue.put(('ErrorSocket', ['send']))

	def place(self, place):
		self.send(f"place {place}")

	def prerun(board, place, turn):
		if place != -1:
			board[place] = turn
			ft = ReversiClient.getFlipTiles(board, place, turn)
			for t in ft: board[t] = turn
		ReversiClient.findHints(board, turn^3)

	def onStart(self, tturn, tboard):
		self.turn = int(tturn)
		self.queue.put(('start', [ list(map(int, tboard)), self.turn ]))

	def onReady(self, tboard):
		self.queue.put(('ready', [ list(map(int, tboard)), self.turn ]))

	def onPlace(self, tboard, tplace, tturn):
		self.queue.put(('place', [ list(map(int, tboard)), int(tplace), int(tturn) ]))

	def onQuit(self, buf):
		w, b = int(buf[:2]), int(buf[2:])
		win = (w > b) - (w < b)
		result = win+1 if self.turn == 1 else 1-win
		self.queue.put(('quit', [w, b, result]))

	def getFlipTiles(board, place, turn):
		dxy = ((1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1))
		x, y, antiturn = place%8, place//8, turn^3
		flips = []
		for dx, dy in dxy:
			isFlip = False
			tf = []
			nx, ny = x+dx, y+dy
			while nx >= 0 and nx < 8 and ny >= 0 and ny < 8:
				np = nx+ny*8
				if board[np] == turn:
					isFlip = True
					break
				if board[np] != antiturn: break
				tf.append(np)
				nx, ny = nx+dx, ny+dy
			if isFlip: flips += tf
		return flips

	def findHints(board, turn):
		hintCount = 0
		for i in range(64):
			if board[i] == 1 or board[i] == 2: continue
			ft = ReversiClient.getFlipTiles(board, i, turn)
			board[i] = 0 if len(ft) > 0 else 3
			hintCount += 1 if board[i] == 0 else 0
		return hintCount

	def getHints(board):
		return [ k for k in range(64) if board[k] == 0 ]

	def getScores(board):
		w, b = 0, 0
		for c in board:
			if c == 1: w += 1
			if c == 2: b += 1
		return w, b

if __name__ == "__main__":
	game = ReversiClient()
	while True:
		if not game.connect('localhost'): break
		while True:
			cmd, args = game.getEvent()
			if cmd == None: continue
			if cmd.startswith('Error'):
				print(cmd, args)
				break
			if cmd == 'start': turn = args[1]
			elif cmd == 'ready':
				hints = ReversiClient.getHints(args[0])
				game.place(random.choice(hints))
			elif cmd == 'quit':
				print(*args)
				break
			elif cmd == 'abort':
				print(*args)
				break
			elif cmd == 'place':
				print(*args)
			else:
				print(f'Unknown command {cmd}')
				break
		game.close()
