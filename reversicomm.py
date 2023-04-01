import socket
import random
import time
import numpy as np
import os.path
from collections import deque

MaxSize = 4096
MiniBatch = 256

class ReversiComm:
	def __init__(self):
		self.gameCount = 0
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	def __del__(self):
		self.sock.close()

	def connect(self, hostname, port=8791):
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

	def recv(self):
		# read packet header
		buf = b""
		while len(buf) < 4:
			try:
				t = self.sock.recv(4-len(buf))
			except:
				return "et", str(socket.error)
			buf += t
		needed = int(buf.decode("ascii"))
		# read packet data those length is needed
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
		return result

	def onBoard(self, buf):
		st, v, nst, nv, p = self.action(buf)
		if p < 0: return False
		self.send("%04d pt %4d"%(8, p))
		self.episode.append((st, v, nst, nv))
		return True

if __name__ == "__main__":
	game = ReversiComm()
	if not game.connect('localhost'): break
