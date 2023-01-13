# Network을 위한 라이브러리 모듈
import socket
import select
import time
# 수학 관련된 라이브러리 모듈
import math
# 파일을 읽고 쓰고, 관리할 목적의 라이브러리
import os.path
import sys
# 난수 발생용 라이브러리 모듈
import random
# pygame을 위한 라이브러리 모듈
import pygame
from pygame.locals import *
import copy

# 기본적인 상수들 정의
FPS = 40			# Frame Per Second (초당 프레임 수)
SpaceSize = 50	  # 오델로 셀의 공간 크기 50x50 (pixelxpixel)
HalfSpace = SpaceSize//2
Margin = 10
WinWidth, WinHeight = SpaceSize*8+Margin+120, SpaceSize*8+Margin+40

# 기본적인 컬러값
White = (255, 255, 255)
Black = (0, 0, 0)
GridColor = (0, 0, 150)
TextColor = (255, 255, 255)
HintColor = (100, 255, 100)	 # Light green (밝은 초록색)

# 타일의 중앙값 찾기
# row = p//8, column = p%8 ==> p = row*8 + column
def GetCenter(p):
	return Margin+(p%8)*SpaceSize+HalfSpace, Margin+(p//8)*SpaceSize+HalfSpace

# 보드 그리기
def DrawBoard():
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
def DrawInfo():
	scores = GetScores()
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
def GetFlipTiles(board, p, t):
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
def FlipTiles(p):
	flips = GetFlipTiles(board, p, turn)
	# 타일 뒤집기 애니메이션
	for rgb in range(0, 255, 90):
		color = tuple([rgb]*3) if turn == 1 else tuple([255-rgb]*3)
		for t in flips:
			cx, cy = GetCenter(t)
			pygame.draw.circle(displaySurf, color, (cx, cy), HalfSpace-3)
		DrawInfo()
		pygame.display.update()
		time.sleep(1/FPS)	   # 1/FPS초동안 아무것도 안하고 쉬기
	for t in flips: board[t] = turn

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
def GetScores():
	wCount, bCount = 0, 0
	for i in range(64):
		if board[i] == 1: wCount += 1
		elif board[i] == 2: bCount += 1
	return (wCount, bCount)

# 준비가 되었다고 표시
def SendReady():
	if players[turn] == 'user': return
	mesg = "0068 bd "
	for i in range(64): mesg += str(board[i])
	players[turn].send(mesg.encode())

# 미리 실행했을때의 보드 상태를 전달
def SendPrerun(p):
	global turn
	pboard = [ k for k in board ]
	if pboard[p] != 0: return False
	pboard[p] = turn
	ft = GetFlipTiles(pboard, p, turn)
	for t in ft: pboard[t] = turn
	GetHints(pboard, turn^3)
	mesg = "0068 pr "
	for i in range(64): mesg += str(pboard[i])
	players[turn].send(mesg.encode())
	return True

# 접속 요청이 왔을 때
def OnConnect(sock):
	cSock, addr = sock.accept()
	print(f"Connected from {addr}")
	# 접속인원이 꽉 찼을 때
	if players[0] == 2:
		cSock.close()
		return
	readSocks.append(cSock)
	while True:
		c = random.randrange(1, 3)
		if players[c] == None: break
	players[c] = cSock
	players[0] += 1
	# 두명의 플레이가 완성되면 게임을 시작
	if players[0] == 2: OnStartGame()

# 데이터를 받았을 경우
def OnRecv(sock):
	buf = b""	   #  "".encode() 한 것과 같다.
	while len(buf) < 4:
		try:
			t = sock.recv(4-len(buf))
			buf += t
		except:
			return False
	# 패킷의 길이를 가져옵니다.
	length = int(buf.decode())
	# 실제 데이터를 읽어옵니다.
	buf = b""
	while len(buf) < length:
		try:
			t = sock.recv(length-len(buf))
			buf += t
		except:
			return False
	# 데이터를 분리
	ss = buf.decode().split()
	if ss[0] == 'ab': OnAbort()
	elif ss[0] == 'pt':
		p = int(ss[1])
		Place(p)
	elif ss[0] == 'pr':
		p = int(ss[1])
		SendPrerun(p)
	return True

# 돌을 놓기
def Place(p):
	global turn, hintCount
	if board[p] != 0: return False
	# p 위치에 돌을 놓기
	board[p] = turn
	# 보드를 그리기
	DrawBoard()
	# 뒤집힐 타일들을 애니메이션하면서 그리기
	FlipTiles(p)
	# 턴 바꾸기
	turn ^= 3
	hintCount = GetHints(board, turn)
	if hintCount > 0:
		SendReady()
		return True
	# 턴 바꾸기
	turn ^= 3
	hintCount = GetHints(board, turn)
	if hintCount > 0:
		SendReady()
		return True
	# 둘다 놓을 수 없는 경우
	OnQuitGame()
	return False

# 게임 시작하기
def OnStartGame():
	global board, hintCount, turn
	board, hintCount = NewBoard()
	turn = 1
	for i in range(1, 3):
		if players[i] == 'user': continue
		mesg = f"0008 st 000{i}"
		players[i].send(mesg.encode())
	SendReady()

# 게임이 끝난 경우
def OnQuitGame():
	global players
	w, b = GetScores()
	for i in range(1, 3):
		if players[i] == 'user': continue
		mesg = f"0008 qt {w:02}{b:02}"
		players[i].send(mesg.encode())
		readSocks.remove(players[i])
	players = [0, None, None]


# 게임이 중간에 포기하는 경우
def OnAbort():
	global players
	w, b = GetScores()
	mesg = f"0004 ab "
	for i in range(1, 3):
		if players[i] == 'user': continue
		try:
			players[i].send(mesg.encode())
		except:
			print("send error")
		if players[i] in readSocks: readSocks.remove(players[i])
	players = [ 0, None, None ]
	
# 사용자가 게임에 참여하는 경우
def OnUserGame():
	# 사용자가 게임에 참여할 수 없는 경우
	if players[0] == 2 or players[1] == 'user' or players[2] == 'user': return
	while True:
		c = random.randrange(1, 3)
		if players[c] == None: break
	players[c] = 'user'
	players[0] += 1
	if players[0] == 2: OnStartGame()

# 사용자가 마우스를 돌을 놓을 위치를 지정한 경우
def OnUser(x, y):
	p = GetClickPosition(x, y)
	print(f"OnUser({x}, {y}) = {p}")
	# 해당 위치가 셀이 아니거나, 해당 위치의 셀이 힌트 셀이 아닌 경우
	if p == None or board[p] != 0: return
	Place(p)


# 네트워크가 쉬는 기간동안 처리하는 일들
def OnIdle():
	DrawBoard()
	DrawInfo()
	pygame.display.update()	 # display 업데이트
	# 이벤트 처리 (PyGame에서 마우스, 키보드 또는 윈도우의 버튼들)
	for event in pygame.event.get():
		if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
			return False
		elif event.type == MOUSEBUTTONUP:
			mx, my = event.pos
			if userGameRect.collidepoint((mx, my)): OnUserGame()
			elif players[turn] == 'user': OnUser(mx, my)
	return True

# 리슨 소켓 만들기
listenSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listenSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
listenSock.bind( ('', 8791) )
listenSock.listen(5)
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
board, hintCount = NewBoard()
players = [ 0, None, None ]
turn = 1

# 게임 실행하는 메인 모듈
while True:
	reads, _, _ = select.select(readSocks, [], [], 1/FPS)
	for s in reads:
		if s == listenSock: OnConnect(s)
		elif not OnRecv(s): OnAbort()
	if not OnIdle(): break

# quit pygame
pygame.quit()

