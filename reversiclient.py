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
		'abort' : 'onAbort',
	}
	def __init__(self):
		self.buf = b''
		self.needed = 0

	def connect(self, hostname, port=8791):
		self.queue = Queue()
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
			except:
				self.queue.put(('ErrorSocket', ['recv header']))
				return
			self.buf += t
			if len(self.buf) < 4: return
			self.needed = int.from_bytes(self.buf, ByteOrder)
			self.buf = b''

		# read packet data those length is needed
		if len(self.buf) < self.needed:
			try: t = self.sock.recv(self.needed-len(self.buf))
			except:
				queue.put((ReversiClient.ErrorSocket, ['recv message']))
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
			queue.put(('ErrorSocket', ['send']))

	def action(self, place):
		self.send(f"place {place}")

	def onStart(self, buf):
		self.turn = int(buf)
		self.queue.put(('start', [self.turn]))

	def onQuit(self, buf):
		w, b = int(buf[:2]), int(buf[2:])
		win = (w > b) - (w < b)
		result = win+1 if self.turn == 1 else 1-win
		self.queue.put(('quit', [w, b, result]))

if __name__ == "__main__":
	game = ReversiClient()
	while True:
		if not game.connect('localhost'): break
		while True:
			cmd, args = game.getEvent()
			if cmd == None: continue
			if cmd.startswith('Error'): break
			if cmd == 'start': turn = args[0]
			elif cmd == 'ready':
				hints = [k for k in range(64) if args[0][k] == '0']
				game.action(random.choice(hints))
			elif cmd == 'quit':
				print(*args)
				break
			else:
				print(f'Unknown command {cmd}')
				break
		game.close()
