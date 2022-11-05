import socket
import random
import time
import numpy as np      # 텐서플로 입력, 출력을 numpy를 통해서 수행

# Game 클래스
class Game:
    # 생성자
    def __init__(self):
        self.gameCount = 0  # 게임이 몇번 이루어졌는지 통계용

    # <통신 함수들>

    # 접속 요청
    def connect(self):
        while True:
            # 접속을 실행할 소켓을 TCP/IP로 생성
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            try:
                self.sock.connect( ('127.0.0.1', 8791) )
            except socket.timeout:
                time.sleep(1.0)
                continue
            except:
                return False
            # 정상적으로 접속요청이 성공한 경우
            break
        return True

    # 접속 종료
    def close(self):
        self.sock.close()


    # 서버로부터 데이터를 받는 함수
    def recv(self):
        # 패킷의 길이를 읽어온다.
        buf = b""
        while len(buf) < 4:
            try:
                t = self.sock.recv(4-len(buf))
            except:
                return "et", "recv length error"
            buf += t
        length = int(buf.decode())
        buf = b""
        while len(buf) < length:
            try:
                t = self.sock.recv(length-len(buf))
            except:
                return "et", "recv packet error"
            buf += t
        # 읽은 내용을 공백으로 분리
        # pr 0001 --> ss[0] = 'pr', ss[1] = '0001'
        ss = buf.decode().split()
        if ss[0] == 'ab': return "ab", "abort from server"
        return ss[0], ss[1]

    # 서버로 데이터를 보내는 함수
    def send(self, buf):
        self.sock.send(buf.encode())

    # <수행 함수들>

    # 미리 두기 함수
    def preRun(self, p):
        # 서버로 prerun을 실행하도록 명령어 전달
        self.send("0008 pr %04d"%p)

        # 서버로부터 prerun 결과를 전달 받는다.
        cmd, buf = self.recv()
        # 서버로부터 전달받은 결과가 pr 명령이 아닌 경우 실패
        if cmd != 'pr': return False, None
        ref = (0.0, 1.0, -1.0, 0.0) if self.turn==1 else (0.0, -1.0, 1.0, 0.0)
        st = np.array( [ref[int(buf[i])] for i in range(64)] )
        return True, st

    # 돌을 두기 함수
    def action(self, board):
        # hints : 이번턴에서 놓을 수 있는 자리
        hints = [ p for p in range(64) if board[p] == '0' ]

        ref = (0.0, 1.0, -1.0, 0.0) if self.turn==1 else (0.0, -1.0, 1.0, 0.0)
        st = np.array( [ref[int(buf[i])] for i in range(64)] )
        
        # 랜덤 두기에서는 선택을 무작위로 하나 선택합니다.
        p = random.choice(hints)

        # p를 선택했을때의 상태값(next status) V(nst) == q(st, p)
        _, nst = self.preRun(p)

        return st, nst, p

    # <핸들러 함수들>

    # 시작 명령을 받았을 때 처리
    def onStart(self, buf):
        #  packet = LEN st turn
        self.turn = int(buf)
        # 에피소드 기록을 위한 리스트
        self.episode = []
        colors = ( "", "White", "Black" )
        print(f"Game {self.gameCount+1} {colors[self.turn]}")

    # 종료 명령을 받았을 때 처리
    def onQuit(self, buf):
        # packet = LEN qt <결과>
        self.gameCount += 1
        w, b = int(buf[:2]), int(buf[2:])
        result = w-b if self.turn==1 else b-w
        winText = ( "You Lose", "Draw", "You Win" )
        win = 2 if result > 0 else 0 if result < 0 else 1
        print(f"{winText[win]} W : {w}, B : {b}")
        return win, result


    # 준비가 되었다고 명령을 받았을 때 처리
    def onBoard(self, buf):
        # packet = LEN bd <결과>
        st, nst, p = self.action(buf)
        if p < 0: return False
        self.send("0008 pt %04d"%p)
        self.episode.append( (st, self.turn^3) )
        self.episode.append( (nst, self.turn) )
        print(f"({p//8}, {p%8})", end="")
        return True

# 게임이 끝났는지 검사하는 플래그
quitFlag = False
# 통계용으로 몇판을 이겼고, 몇판을 졌는지, 몇판을 비겼는지
# winlose = [ Lose, Draw, Win ]
winlose = [ 0, 0, 0 ]

# game 클래스 오브젝트 생성
game = Game()

# 전체 반복문
while not quitFlag:
    if not game.connect(): break
    episode = []
    while True:
        cmd, buf = game.recv()
        if cmd == 'et':
            print(f"Network error!! : {buf}")
            break
        if cmd == 'qt':
            w, r = game.onQuit(buf)
            winlose[w] += 1
            print(f"Wins:{winlose[2]}, Loses:{winlose[0]}, Draws:{winlose[1]}")
            print(f"Win ratio:{winlose[2]*100/sum(winlose):.2f}%")
            break
        if cmd == 'ab':
            print("Game Abort!!")
            break
        if cmd == 'st':
            game.onStart(buf)
        elif cmd == 'bd':
            if not game.onBoard(buf): break
    # 게임을 종료
    game.close()
    # 종료후 바로 끝내지 않고 1초간 대기
    time.sleep(1.0)















        
