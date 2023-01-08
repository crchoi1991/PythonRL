import math		# 수학 관련된 라이브러리 모듈
import sys
import random	# 난수 발생용 라이브러리 모듈
import pygame	# pygame을 위한 라이브러리 모듈
from pygame.locals import *

# 기본적인 상수들 정의
FPS = 30		# Frame Per Second (초당 프레임 수)
WaitFrame = 1000//FPS
SpaceSize = 80	# 오델로 셀의 공간 크기 50x50 (pixelxpixel)
HalfSpace = SpaceSize//2
Margin = 20
WinWidth, WinHeight = SpaceSize*8+Margin*2, SpaceSize*8+Margin+40

# 인공지능을 위한 점수판
ScoreBoard = (
	1, 1, 1, 1, 1, 1, 1, 1,
	1, 1, 1, 1, 1, 1, 1, 1,
	1, 1, 1, 1, 1, 1, 1, 1,
	1, 1, 1, 1, 1, 1, 1, 1,
	1, 1, 1, 1, 1, 1, 1, 1,
	1, 1, 1, 1, 1, 1, 1, 1,
	1, 1, 1, 1, 1, 1, 1, 1,
	1, 1, 1, 1, 1, 1, 1, 1 )

# 기본적인 컬러값
White = (255, 255, 255)
Black = (0, 0, 0)
GridColor = (0, 0, 150)
TextColor = (255, 255, 200)
TextOutlineColor = (0, 0, 0)
HintColor = (100, 100, 255)

# 타일의 중앙값 찾기
def GetCenter(p):
	r, c = p//8, p%8	#  세로위치(r), 가로위치(c)
	return Margin+c*SpaceSize+HalfSpace, Margin+r*SpaceSize+HalfSpace

# 보드 그리기
def DrawBoard(board):
	# 배경을 먼저 그린다.
	displaySurf.blit(bgImage, bgImage.get_rect())

	# 보드의 줄을 친다.  8칸에 줄을 치기위해서 8+1개의 줄이 필요
	for i in range(8+1):
		t = i*SpaceSize+Margin
		pygame.draw.line(displaySurf, GridColor, (t, Margin), (t, Margin+8*SpaceSize))
		pygame.draw.line(displaySurf, GridColor, (Margin, t), (Margin+8*SpaceSize, t))

	# 돌을 그립니다.
	for i in range(8*8):
		cx, cy = GetCenter(i)
		if board[i] == 1:
			pygame.draw.circle(displaySurf, White, (cx, cy), HalfSpace-4)
		elif board[i] == 2:
			pygame.draw.circle(displaySurf, Black, (cx, cy), HalfSpace-3)
		elif board[i] == 0:
			pygame.draw.rect(displaySurf, HintColor, (cx-4, cy-4, 8, 8))
	
# 정보를 표시하기
def DrawInfo(board):
	scores = GetScores(board)
	colors = ( "", "White", "Black" )
	# 표시할 문자열 만들기
	str = f"White : {scores[0]:2}  Black : {scores[1]:2}  Turn : {colors[turn]}"
	# 문자열을 이미지로 변환
	scoreSurf = normalFont.render(str, True, TextColor)
	scoreRect = scoreSurf.get_rect()
	scoreRect.bottomleft = (Margin, WinHeight-5)
	# 문자열 이미지를 디스플레이에 표시
	displaySurf.blit(scoreSurf, scoreRect)

# 뒤집을 타일 찾기
def GetFlipTiles(board, p, turn):
	dxy = ((1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1))
	x, y = p%8, p//8
	flips = []
	for dx, dy in dxy:
		isFlip = False
		tf = []		 # 해당방향에 flip될 타일들을 임시로 저장
		nx, ny = x+dx, y+dy
		while nx >= 0 and nx < 8 and ny >= 0 and ny < 8:
			np = nx+ny*8
			if board[np] == turn:
				isFlip = True
				break
			if board[np] != turn^3: break
			tf.append(np)
			nx, ny = nx+dx, ny+dy
		if isFlip: flips += tf	  # 임시저장된 타일들을 isFlip이 참인경우에 적용
	return flips

# 타일 뒤집기
def FlipTiles(board, p, turn):
	flips = GetFlipTiles(board, p, turn)
	# 타일 뒤집기 애니메이션
	for rgb in range(0, 255, 90):
		color = tuple([rgb]*3) if turn == 1 else tuple([255-rgb]*3)
		for t in flips:
			cx, cy = GetCenter(t)
			pygame.draw.circle(displaySurf, color, (cx, cy), HalfSpace-3)
		pygame.display.update()
		pygame.time.wait(WaitFrame)
	for t in flips: board[t] = turn
	DrawInfo(board)

# 놓을 수 있는 위치 찾기
def GetHints(board, turn):
	hintCount = 0
	for i in range(64):
		# 현재 돌이 있는 경우는 패스
		if board[i] == 1 or board[i] == 2: continue
		ft = GetFlipTiles(board, i, turn)
		board[i] = 0 if len(ft) > 0 else 3
		hintCount += 1 if board[i] == 0 else 0
	return hintCount

# 클릭위치값이 주어졌을때, 클릭된 보드의 셀번호 반환
def GetClickPosition(x, y):
	rx, ry = (x-Margin)//SpaceSize, (y-Margin)//SpaceSize
	return None if rx < 0 or rx >= 8 or ry < 0 or ry >= 8 else rx+ry*8

# 새로운 보드 만들기
def NewBoard():
	board = [3]*64
	board[27], board[28], board[35], board[36] = 1, 2, 2, 1
	board[20], board[29], board[34], board[43] = 0, 0, 0, 0
	return board, 4

# 현재 점수 반환
def GetScores(board):
	wCount, bCount = 0, 0
	for i in range(64):
		if board[i] == 1: wCount += 1
		elif board[i] == 2: bCount += 1
	return (wCount, bCount)

# 미리 실행했을때의 보드 상태를 전달
def GetPrerunScore(board, p, turn):
	pboard = [ k for k in board ]
	pboard[p] = turn
	ft = GetFlipTiles(pboard, p, turn)
	for t in ft: pboard[t] = turn
	score = 0
	ref = ( 0, 1 if turn==1 else -1, 1 if turn==2 else -1, 0 )
	for k in range(64):
		score += ScoreBoard[k]*ref[pboard[k]]
	return score

# 돌을 놓기
def Place(board, p, turn):
	# p 위치에 돌을 놓기
	board[p] = turn
	# 보드를 그리기
	DrawBoard(board)
	pygame.time.wait(WaitFrame)
	# 뒤집힐 타일들을 애니메이션하면서 그리기
	FlipTiles(board, p, turn)
	# 턴 바꾸기
	turn ^= 3
	hintCount = GetHints(board, turn)
	if hintCount > 0: return turn
	# 턴 바꾸기
	turn ^= 3
	hintCount = GetHints(board, turn)
	if hintCount > 0: return turn
	# 둘다 놓을 수 없는 경우
	return 0

# 사용자 입력 기다리기
def WaitForInput(board, turn):
	while True:
		DrawBoard(board)
		DrawInfo(board)
		pygame.display.update()	 # display 업데이트
		# 이벤트 처리 (PyGame에서 마우스, 키보드 또는 윈도우의 버튼들)
		for event in pygame.event.get():
			if event.type == QUIT: return None 
			if event.type == KEYUP and event.key == K_ESCAPE: return None 
			if event.type == MOUSEBUTTONUP:
				p = GetClickPosition(event.pos[0], event.pos[1])
				if p != None and board[p] == 0: return p

# 컴퓨터 두기
def WaitForComputer(board, turn):
	maxp, maxScore = None, -1000
	hints = [ k for k in range(64) if board[k]==0 ]
	random.shuffle(hints)
	for p in hints:
		DrawBoard(board)
		DrawInfo(board)
		pygame.display.update()	 # display 업데이트
		# 이벤트 처리 (PyGame에서 마우스, 키보드 또는 윈도우의 버튼들)
		for event in pygame.event.get():
			if event.type == QUIT: return None
			if event.type == KEYUP and event.key == K_ESCAPE: return None
		score = GetPrerunScore(board, p, turn)
		if maxScore < score: maxp, maxScore = p, score
		pygame.time.wait(WaitFrame)
	return maxp

# 시작 버튼 기다리기
def WaitForStart():
	# start game button 생성
	startGameSurf = bigFont.render("Start Game", True, TextColor)
	startGameRect = startGameSurf.get_rect()
	startGameRect.center = (WinWidth//2, WinHeight//2)
	while True:
		displaySurf.blit(bgImage, bgImage.get_rect())
		# 사용자 게임 버튼 정보 표시
		DrawOutlineText(displaySurf, "Start Game", bigFont, 
			(WinWidth//2, WinHeight//2), TextColor, TextOutlineColor)
		pygame.display.update()	 # display 업데이트
		# 이벤트 처리 (PyGame에서 마우스, 키보드 또는 윈도우의 버튼들)
		for event in pygame.event.get():
			if event.type == QUIT: return False
			if event.type == KEYUP and event.key == K_ESCAPE: return False
			if event.type == MOUSEBUTTONUP:
				if startGameRect.collidepoint(event.pos): return True
		pygame.time.wait(WaitFrame)

# 결과 출력
def ShowResult(board, turn):
	scores = GetScores(board)
	result = (scores[turn==2]>scores[turn==1])*2+(scores[turn==1]>scores[turn==2])
	msg = ( "Draw", "You lose!!", "You Win!!" )
	for _ in range(FPS*5):
		DrawBoard(board)
		DrawInfo(board)
		DrawOutlineText(displaySurf, msg[result], bigFont, 
			(WinWidth//2, WinHeight//2), TextColor, TextOutlineColor)
		pygame.display.update()	 # display 업데이트
		for event in pygame.event.get():
			if event.type == QUIT: return False
			if event.type == KEYUP and event.key == K_ESCAPE: return False
			if event.type == MOUSEBUTTONUP: return True
		pygame.time.wait(WaitFrame)

def DrawOutlineText(ds, text, font, pos, c, o):
	d = ( (-2, 0), (0, -2), (2, 0), (0, 2) )
	for x, y in d:
		ts = font.render(text, True, o)
		tr = ts.get_rect()
		tr.center = (pos[0]+x, pos[1]+y)
		ds.blit(ts, tr)
	ts = font.render(text, True, c)
	tr = ts.get_rect()
	tr.center = pos
	ds.blit(ts, tr)
	

# pygame 초기화
pygame.init()

# 디스플레이 서피스(display surface) 만들기
displaySurf = pygame.display.set_mode( (WinWidth, WinHeight) )
pygame.display.set_caption("Reversi AI Game")

# 텍스를 위한 폰트
normalFont = pygame.font.Font("freesansbold.ttf", 16)
bigFont = pygame.font.Font("freesansbold.ttf", 64)

# 백그라운드 이미지 설정
boardImage = pygame.image.load('board.png')
boardImage = pygame.transform.smoothscale(boardImage, (8*SpaceSize, 8*SpaceSize))
boardImageRect = boardImage.get_rect()
boardImageRect.topleft = (Margin, Margin)
bgImage = pygame.image.load("bg.png")
bgImage = pygame.transform.smoothscale(bgImage, (WinWidth, WinHeight))
bgImage.blit(boardImage, boardImageRect)

# 게임 메인 루프(game main loop)
while True:
	ret = WaitForStart()
	if not ret: break

	# 보드 생성
	board, hintCount = NewBoard()
	turn = 1
	userTurn = random.randrange(1, 3)

	# 게임 실행하는 메인 모듈
	while turn != 0:
		if turn == userTurn: p = WaitForInput(board, turn)
		else: p = WaitForComputer(board, turn)
		if p == None:
			pygame.quit()
			quit()
		turn = Place(board, p, turn)

	ShowResult(board, userTurn)
