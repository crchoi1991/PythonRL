# n-puzzle pygame class
import pygame
from pygame.locals import *
import random

Margin = 10
Actions = ( (0, -1), (-1, 0), (0, 1), (1, 0) )

HCells, VCells = 4, 4
Cells = HCells*VCells
CellSize = 100

Black, White, Grey = (0, 0, 0), (250, 250, 250), (120, 120, 120)

# n-puzzle class
class NPuzzle:
	# constructor
	def __init__(self, cells=(4, 4), fps=30):
		# init pygame
		pygame.init()

		# set cell dimension
		HCells, VCells = cells[0], cells[1]
		Cells = HCells*VCells

		# set clock and fps
		self.fps = fps
		self.clock = pygame.time.Clock()

		# make display
		self.display = pygame.display.set_mode(( Margin*2+HCells*CellSize,
		    Margin*2+VCells*CellSize))

		# set text font
		self.font = pygame.font.Font('freesansbold.ttf', CellSize//2-1)

	# destructor
	def __del__(self):
		print("quit n-puzzle")
		pygame.quit()

	# new gmae
	def newGame(self, gameCount, shuffleCount):
		# Set window caption
		caption = f"DQN 12 : Game {gameCount} shuffle {shuffleCount}"
		pygame.display.set_caption(caption)

		# initialize n-puzzle
		self.board = [k+1 for k in range(Cells)]
		self.empty = Cells-1

		# shuffle
		k = 0
		while k < shuffleCount or self.check() == 0:
			v = random.choice(Actions)
			r, c = self.empty//HCells, self.empty%HCells
			nr, nc = r+v[0], c+v[1]
			k += 1
			# ignore when next cell is out of puzzle
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
	
	# action
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

	# draw n-puzzle
	def draw(self):
		self.display.fill( White )
		pygame.draw.rect(self.display, Grey,
			(Margin, Margin, CellSize*HCells, CellSize*VCells))
		pygame.draw.rect(self.display, Black,
			(Margin, Margin, CellSize*HCells, CellSize*VCells), 1)

		# 슬라이딩 퍼즐 그림을 그립니다.
		for k in range(Cells):
			r, c = k//HCells, k%HCells
			# 박스 그리기
			color = White
			if self.board[k] == Cells or k == self.last: continue
			pygame.draw.rect(self.display, color, (Margin+c*CellSize,
				Margin+r*CellSize, CellSize, CellSize))
			pygame.draw.rect(self.display, Black, (Margin+c*CellSize,
				Margin+r*CellSize, CellSize, CellSize), 1)
			# 박스 안에 글자 쓰기
			text = self.font.render(str(self.board[k]), True, (0, 0, 0))
			rect = text.get_rect()
			rect.center = (Margin+c*CellSize+CellSize//2,
						   Margin+r*CellSize+CellSize//2)
			self.display.blit(text, rect)
		# 애니메이션 셀 그리기
		if self.last != None:
			r, c = self.last//HCells, self.last%HCells
			er, ec = self.empty//HCells, self.empty%HCells
			x = Margin+(self.alpha*c+(1-self.alpha)*ec)*CellSize
			y = Margin+(self.alpha*r+(1-self.alpha)*er)*CellSize
			pygame.draw.rect(self.display, White, (x, y, CellSize, CellSize))
			pygame.draw.rect(self.display, Black, (x, y, CellSize, CellSize), 1)
			# 박스 안에 글자 쓰기
			s = str(self.board[self.last])
			text = self.font.render(s, True, Black)
			rect = text.get_rect()
			rect.center = (x+CellSize//2, y+CellSize//2)
			self.display.blit(text, rect)
			if self.alpha < 0.95: self.alpha += 0.1

		# flip display
		pygame.display.flip()
		self.clock.tick(self.fps)

		return True

	# get user input
	def getEvent(self):
		for e in pygame.event.get():
			if e.type == QUIT: return 1
			if e.type == KEYUP and e.key == K_ESCAPE: return 1
			if e.type == KEYUP and e.key == K_x: return 2
			if e.type == KEYUP and e.key == K_z: return 3
		return 0
		
if __name__ == '__main__':
	puzzle = NPuzzle()
	for game in range(5):
		puzzle.newGame(game, 100)
		for _ in range(200):
			ev = puzzle.getEvent()
			if ev == -1: break
			puzzle.draw()
