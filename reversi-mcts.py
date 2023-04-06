import socket
import random
import time
from reversiclient import ReversiClient

SimulationCount = 32
class TreeNode:
	def __init__(self, parent, board, turn):
		self.board = board
		self.turn = turn
		self.win, self.visit = 0, 0
		self.hints = ReversiClient.getHints(board)
		random.shuffle(self.hints)
		self.children = []
		self.parent = parent
		if parent: parent.children.append(self)

class MCTree:
	def __init__(self, board, turn):
		self.root = TreeNode(None, board, turn)

	def select(self, root=None):
		if root==None: root = self.root
		# select
		if len(root.hints) == 0 and len(root.children) != 0:
			maxchild, maxv = None, 0
			for i in root.children:
				v = child.win/(child.visit+1)
				u = math.sqrt(2.0*log(root->visit)/(child.visit+1))
				if maxv < u+v: maxchild, maxv = child, u+v
			self.select(child)
			return
		# expand
		if len(root.hints) == 0:
			node = TreeNode(root, root.board, root.turn^3)
		else:
			place = rooot.hints.pop()
			board = ReversiClient.prerun(root.board, place, root.turn)
			node = TreeNode(root, board, root.turn^3)
		# simultion
		win = 0
		for _ in range(SimultionCount):
			if node.simultion(): win += 1
		# update
		while node != None:
			node.win += win
			node.visit += SimulationCountt
			node = node.parent
		
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
