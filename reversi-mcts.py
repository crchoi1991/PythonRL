import socket
import random
import time
import math
from reversiclient import ReversiClient

SimulationCount = 49
SelectCount = 14
class TreeNode:
	def __init__(self, parent, board, place, turn):
		self.board = board
		self.place = place
		self.turn = turn
		self.win, self.visit = 0, 0
		self.hints = ReversiClient.getHints(board)
		random.shuffle(self.hints)
		self.children = []
		self.parent = parent
		if parent: parent.children.append(self)

	def __str__(self):
		return f'place={self.place} turn={self.turn} w/v={self.win}/{self.visit} childs={len(self.children)}'
	
	def simulate(self):
		board = self.board[:]
		turn = self.turn
		hints = self.hints
		while True:
			place = -1 if len(hints) == 0 else random.choice(hints)
			board = ReversiClient.prerun(board, place, turn)
			hints = ReversiClient.getHints(board)
			turn ^= 3
			if len(hints) == 0:
				board = ReversiClient.prerun(board, -1, turn)
				hints = ReversiClient.getHints(board)
				turn ^= 3
			if len(hints) == 0:
				w, b = ReversiClient.getScores(board)
				return 0 if w == b else int(w > b) if self.turn == 2 else int(b > w)

class MCTree:
	def __init__(self, board, turn):
		self.root = TreeNode(None, board, -2, turn)

	def select(self, root=None):
		if root==None: root = self.root
		# if this node is terminal, pass
		if root.place == -1 and root.parent != None and root.parent.place == -1: return
		# select
		if len(root.hints) == 0 and len(root.children) != 0:
			maxchild, maxv = None, 0
			for child in root.children:
				v = child.win/(child.visit+1)
				u = math.sqrt(2.0*math.log(root.visit)/(child.visit+1))
				if maxv < u+v: maxchild, maxv = child, u+v
			self.select(child)
			return
		# expand
		if len(root.hints) == 0:
			node = TreeNode(root, root.board, -1, root.turn^3)
		else:
			place = root.hints.pop()
			board = ReversiClient.prerun(root.board, place, root.turn)
			node = TreeNode(root, board, place, root.turn^3)
		# simultion
		win = 0
		for _ in range(SimulationCount):
			if node.simulate(): win += 1
		# update
		while node != None:
			node.win += win
			node.visit += SimulationCount
			node = node.parent
			win = SimulationCount-win

	def getMaxChild(self):
		if len(self.root.children)==0: return random.choice(self.root.hints)
		maxchild, maxv = None, -1
		for child in self.root.children:
			v = child.win/(child.visit+1)
			if maxv < v: maxchild, maxv = child, v
		return maxchild.place

	def place(self, board, place, turn):
		# if no simulation is occurred
		if len(self.root.children) == 0:
			self.root = TreeNode(None, board, place, turn^3)
			return
		# skip when no place
		if self.root.children[0].place == -1:
			tmp = self.root
			self.root = child
			child.parent = None
			del(tmp)
		# find placed child and set the child as a root
		for child in self.root.children:
			if child.place == place:
				tmp = self.root
				self.root = child
				child.parent = None
				del(tmp)
				return
		
Colors = ('', 'White', 'Black')
WinText = ('Lose', 'Draw', 'Win')
game = ReversiClient()
gameCount = 0
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
			turn = args[1]
			print(f'start a new game {gameCount+1} with color {Colors[turn]}')
		elif cmd == 'ready':
			mcts = MCTree(args[0], args[1])
			for _ in range(SelectCount): mcts.select()
			place = mcts.getMaxChild()
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
