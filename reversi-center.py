# Network을 위한 라이브러리 모듈
import socket
import select
import time
import math			# 수학 관련된 라이브러리 모듈
import os.path		# 파일을 읽고 쓰고, 관리할 목적의 라이브러리
import sys
import random
import pygame		# pygame을 위한 라이브러리 모듈
from pygame.locals import *

# 기본적인 상수들 정의
FPS = 30			# Frame Per Second (초당 프레임 수)
SpaceSize = 50		# 오델로 셀의 공간 크기 50x50 (pixelxpixel)
HalfSpace = SpaceSize//2
Margin = 10
WinWidth, WinHeight = SpaceSize*8+Margin+120, SpaceSize*8+Margin+40

# 기본적인 컬러값
White = (255, 255, 255)
Black = (0, 0, 0)
GridColor = (0, 0, 150)
TextColor = (255, 255, 255)
HintColor = (100, 255, 100)	 # Light green (밝은 초록색)

# Byte order
ByteOrder = 'little'
Encode = 'ascii'

def send(sock, mesg):
	pl = (len(mesg)).to_bytes(4, ByteOrder)
	try:
		sock.send(pl)
		sock.send(mesg.encode(Encode))
	except:
		print(f'send error {mesg}')

# 타일의 중앙값 찾기
# row = p//8, column = p%8 ==> p = row*8 + column
def getCenter(p):
	return Margin+(p%8)*SpaceSize+HalfSpace, Margin+(p//8)*SpaceSize+HalfSpace

# 보드 그리기
def drawBoard():
	# 배경을 먼저 그린다.
	displaySurf.blit(bgImage, bgImage.get_rect())

	# 보드의 줄을 친다.  8칸에 줄을 치기위해서 8+1개의 줄이 필요
	for i in range(8+1):
		t = i*SpaceSize+Margin
		pygame.draw.line(displaySurf, GridColor, (t, Margin), (t, Margin+8*SpaceSize))
		pygame.draw.line(displaySurf, GridColor, (Margin, t), (Margin+8*SpaceSize, t))

	# 돌을 그립니다.
	for i in range(8*8):
		cx, cy = getCenter(i)
		if board[i] == 1:
			pygame.draw.circle(displaySurf, White, (cx, cy), HalfSpace-4)
		elif board[i] == 2:
			pygame.draw.circle(displaySurf, Black, (cx, cy), HalfSpace-3)
		elif board[i] == 0:
			pygame.draw.rect(displaySurf, HintColor, (cx-4, cy-4, 8, 8))
			numSurf = normalFont.render(f'{i}', True, TextColor)
			numRect = numSurf.get_rect()
			numRect.bottomleft = (cx-8, cy+8)
			displaySurf.blit(numSurf, numRect)
	
# 정보를 표시하기
def drawInfo():
	scores = getScores()
	colors = ( "", "White", "Black" )
	# 표시할 문자열 만들기
	str = f"White : {scores[0]:2}  Black : {scores[1]:2}  Turn : {colors[turn]}"
	# 문자열을 이미지로 변환
	scoreSurf = normalFont.render(str, True, TextColor)
	scoreRect = scoreSurf.get_rect()
	scoreRect.bottomleft = (Margin, WinHeight-5)
	# 문자열 이미지를 디스플레이에 표시
	displaySurf.blit(scoreSurf, scoreRect)
	# 사용자 게임 버튼 정보 표시
	if players[1] != 'user' and players[2] != 'user':
		displaySurf.blit(userGameSurf, userGameRect)

# 뒤집을 타일 찾기
def getFlipTiles(board, p, t):
	dxy = ((1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1))
	x, y = p%8, p//8
	flips = []
	for dx, dy in dxy:
		isFlip = False
		tf = []		 # 해당방향에 flip될 타일들을 임시로 저장
		nx, ny = x+dx, y+dy
		while nx >= 0 and nx < 8 and ny >= 0 and ny < 8:
			np = nx+ny*8
			if board[np] == t:
				isFlip = True
				break
			if board[np] != t^3: break
			tf.append(np)
			nx, ny = nx+dx, ny+dy
		if isFlip: flips += tf	  # 임시저장된 타일들을 isFlip이 참인경우에 적용
	return flips

# 타일 뒤집기
def flipTiles(p):
	flips = getFlipTiles(board, p, turn)
	# 타일 뒤집기 애니메이션
	for rgb in range(0, 255, 90):
		color = tuple([rgb]*3) if turn == 1 else tuple([255-rgb]*3)
		for t in flips:
			cx, cy = getCenter(t)
			pygame.draw.circle(displaySurf, color, (cx, cy), HalfSpace-3)
		drawInfo()
		pygame.display.update()
		time.sleep(1/FPS)	   # 1/FPS초동안 아무것도 안하고 쉬기
	for t in flips: board[t] = turn

# 놓을 수 있는 위치 찾기
def getHints(board, turn):
	hintCount = 0
	for i in range(64):
		# 현재 돌이 있는 경우는 패스
		if board[i] == 1 or board[i] == 2: continue
		ft = getFlipTiles(board, i, turn)
		board[i] = 0 if len(ft) > 0 else 3
		hintCount += 1 if board[i] == 0 else 0
	return hintCount

# 클릭위치값이 주어졌을때, 클릭된 보드의 셀번호 반환
def getClickPosition(x, y):
	rx, ry = (x-Margin)//SpaceSize, (y-Margin)//SpaceSize
	return None if rx < 0 or rx >= 8 or ry < 0 or ry >= 8 else rx+ry*8

# 새로운 보드 만들기
def newBoard():
	board = [3]*64
	board[27], board[28], board[35], board[36] = 1, 2, 2, 1
	board[20], board[29], board[34], board[43] = 0, 0, 0, 0
	return board, 4

# 현재 점수 반환
def getScores():
	wCount, bCount = 0, 0
	for i in range(64):
		if board[i] == 1: wCount += 1
		elif board[i] == 2: bCount += 1
	return (wCount, bCount)

# send ready packet
def sendPlace(board, place, turn):
	mesg = "place "+"".join(map(str, board))+f" {place} {turn}"
	for i in range(1, 3):
		if players[i] != 'user': send(players[i], mesg)

# send ready packet
def sendReady():
	if players[turn] == 'user': return
	mesg = "ready "+"".join(map(str, board))
	send(players[turn], mesg)

# send the result of prerun
def sendPrerun(p):
	if board[p] != 0: return False
	pboard = board[:]
	pboard[p] = turn
	ft = GetFlipTiles(pboard, p, turn)
	for t in ft: pboard[t] = turn
	GetHints(pboard, turn^3)
	mesg = "prerun "+"".join(map(str, pboard))
	send(players[turn], mesg)
	return True

# when client request connect
def onConnect(sock):
	cSock, addr = sock.accept()
	print(f"Connected from {addr}")
	# if already players are full
	if players[0] == 2:
		cSock.close()
		return
	readSocks.append(cSock)
	c = random.choice([k for k in range(1, 3) if players[k] == None])
	players[c] = cSock
	players[0] += 1
	# when number of players is 2, start game
	if players[0] == 2: onStartGame()

# when receive
def onRecv(sock):
	buf = b""
	while len(buf) < 4:
		try: t = sock.recv(4-len(buf))
		except: return False
		if not len(t): return False
		buf += t
	# get length
	length = int.from_bytes(buf, ByteOrder)
	# 실제 데이터를 읽어옵니다.
	buf = b""
	while len(buf) < length:
		try: t = sock.recv(length-len(buf))
		except: return False
		if not len(t): return False
		buf += t
	# 데이터를 분리
	ss = buf.decode().split()
	if ss[0] == 'abort': onAbort()
	elif ss[0] == 'place': place(int(ss[1]))
	elif ss[0] == 'prerun': sendPrerun(int(ss[1]))
	return True

# 돌을 놓기
def place(p):
	global turn, hintCount
	if board[p] != 0: return False
	# p 위치에 돌을 놓기
	board[p] = turn
	# 보드를 그리기
	drawBoard()
	# 뒤집힐 타일들을 애니메이션하면서 그리기
	flipTiles(p)
	# 턴 바꾸기
	turn ^= 3
	hintCount = getHints(board, turn)
	# send result of place
	sendPlace(board, p, turn^3)
	if hintCount > 0:
		sendReady()
		return True
	# 턴 바꾸기
	turn ^= 3
	hintCount = getHints(board, turn)
	if hintCount > 0:
		sendReady()
		return True
	# 둘다 놓을 수 없는 경우
	onQuitGame()
	return False

# 게임 시작하기
def onStartGame():
	global board, hintCount, turn
	board, hintCount = newBoard()
	tboard = "".join(map(str, board))
	turn = 1
	for i in range(1, 3):
		if players[i] != 'user': send(players[i], f"start {i} {tboard}")
	sendReady()

# 게임이 끝난 경우
def onQuitGame():
	global players
	w, b = getScores()
	for i in range(1, 3):
		if players[i] == 'user': continue
		mesg = f"quit {w:02}{b:02}"
		send(players[i], mesg)
		readSocks.remove(players[i])
	players = [0, None, None]

# when abort this game
def onAbort():
	global players
	print('Abort game')
	mesg = f"abort"
	for i in range(1, 3):
		if players[i] != 'user': send(players[i], "abort")
		if players[i] in readSocks: readSocks.remove(players[i])
	players = [ 0, None, None ]
	
# when user is in this game
def onUserGame():
	# 사용자가 게임에 참여할 수 없는 경우
	if players[0] == 2 or 'user' in players: return
	c = random.choice([k for k in range(1, 3) if players[k] == None])
	players[c] = 'user'
	players[0] += 1
	if players[0] == 2: onStartGame()

# when user place a stone
def onUser(x, y):
	p = getClickPosition(x, y)
	print(f"onUser({x}, {y}) = {p}")
	if p == None or board[p] != 0: return
	place(p)

# when idle
def onIdle():
	drawBoard()
	drawInfo()
	pygame.display.update()	 # display 업데이트
	# 이벤트 처리 (PyGame에서 마우스, 키보드 또는 윈도우의 버튼들)
	for event in pygame.event.get():
		if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
			return False
		elif event.type == MOUSEBUTTONUP:
			mx, my = event.pos
			if userGameRect.collidepoint((mx, my)): onUserGame()
			elif players[turn] == 'user': onUser(mx, my)
	return True

# 리슨 소켓 만들기
listenSock = socket.create_server(('', 8791))
listenSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
listenSock.listen()
readSocks = [ listenSock ]

# pygame 초기화
pygame.init()

# 디스플레이 서피스(display surface) 만들기
displaySurf = pygame.display.set_mode( (WinWidth, WinHeight) )
pygame.display.set_caption("Reversi Game Center")

# 텍스를 위한 폰트
normalFont = pygame.font.Font("freesansbold.ttf", 16)
bigFont = pygame.font.Font("freesansbold.ttf", 32)

# 백그라운드 이미지 설정
boardImage = pygame.image.load('board.png')
boardImage = pygame.transform.smoothscale(boardImage, (8*SpaceSize, 8*SpaceSize))
boardImageRect = boardImage.get_rect()
boardImageRect.topleft = (Margin, Margin)
bgImage = pygame.image.load("bg.png")
bgImage = pygame.transform.smoothscale(bgImage, (WinWidth, WinHeight))
bgImage.blit(boardImage, boardImageRect)

# user game 버튼 생성
userGameSurf = normalFont.render("User Game", True, TextColor)
userGameRect = userGameSurf.get_rect()
userGameRect.topright = (WinWidth-8, Margin)

# 보드 생성
board, hintCount = newBoard()
players = [ 0, None, None ]
turn = 1

# 게임 실행하는 메인 모듈
while True:
	reads, _, _ = select.select(readSocks, [], [], 1/FPS)
	for s in reads:
		if s == listenSock: onConnect(s)
		elif not onRecv(s): onAbort()
	if not onIdle(): break

# quit pygame
pygame.quit()

listenSock.close()
