import socket
import random
import time
import os
import numpy as np      # 텐서플로 입력, 출력을 numpy를 통해서 수행
import tensorflow as tf
from tensorflow import keras

# Game 클래스
class Game:
    # 가중치값을 저장할 폴더 이름 지정
    # 파일이름은 gameCount 100인 경우 cp_000100.ckpt
    cpPath = "reversi-single/cp_{0:06}.ckpt"
    
    # 생성자
    def __init__(self):
        self.gameCount = 0  # 게임이 몇번 이루어졌는지 통계용

        # 학습을 위한 파라미터
        self.epochs = 5     # 데이터를 몇번 학습할것인지
        self.batchSize = 32 # 한번학습할때 몇개를 동시에 할 것인지

        # 강화학습 위한 파라미터
        self.alpha = 0.3    # 학습률
        self.gamma = 0.9    # 미래의 가치 반영률

        # e-greedy 파라미터
        self.epsilon = 1.0  # 초기 입실론값
        self.epsilonDecay = 0.999   # 매 게임마다, 0.1% 입실론 확률 감소
        self.epsilonMin = 0.01  # 무조건 랜덤으로 할 확률
        
        # 신경망회로를 생성
        self.buildModel()

    # 신경망 회로 생성
    def buildModel(self):
        # 단순 신경망(simple neural network : 은닉층이 없는 신경망)
        #   --> 입력과 출력만 존재하는 신경망
        #   64x1 신경망 --> 간선의 갯수가 64x1, 바이어스의 갯순 1개
        self.model = keras.Sequential( [
            keras.layers.Dense(1, input_dim=64, activation='tanh')
        ] )
        # 설정한 모델을 컴파일
        self.model.compile( loss='mean_squared_error',
                            optimizer=keras.optimizers.Adam() )

        # 학습한 데이터를 읽어서 모델에 적용
        # 저장된 폴더 이름 가져오기
        dir = os.path.dirname(Game.cpPath)
        # 가장 최근에 저장된 파일 이름을 찾기
        latest = tf.train.latest_checkpoint(dir)
        # 저장된 파일이 없는 경우
        if not latest: return
        print(f"Load weights {latest}")
        # latest 파일로부터 학습데이터를 가져옵니다.
        self.model.load_weights(latest)

        # 입실론 탐욕법을 위한 처리
        idx = latest.find("cp_")
        self.gameCount = int(latest[idx+3:idx+9])
        # 입실론 값에 적용
        self.epsilon *= self.epsilonDecay**self.gameCount
        if self.epsilon < self.epsilonMin: self.epsilon = self.epsilonMin

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

        # e-greedy 알고리즘에 의해서 랜덤하게 선택
        if np.random.rand() <= self.epsilon:
            # 무작위로 선택
            p = random.choice(hints)
            ret, nst = self.preRun(p)
            if not ret: return None, -1, 0
            v = self.model.predict(nst.reshape(1, 64))[0, 0]
            return nst, p, v

        # 랜덤하게 힌트값들을 섞는다.
        random.shuffle(hints)

        ref = (0.0, 1.0, -1.0, 0.0) if self.turn==1 else (0.0, -1.0, 1.0, 0.0)
        st = np.array( [ref[int(buf[i])] for i in range(64)] )
        
        # 놓을 수 있는 자리 중에 가장 높은 값을 주는 것을 선택
        maxp, maxnst, maxv = -1, None, -1000
        for h in hints:
            # nst는 h 위치에 돌을 놓았을 때의 보드 상태 값
            ret, nst = self.preRun(h)
            if not ret: return None, -1, -1000
            # nst는 64개의 원소를 갖는 배열 --> 2차원배열인 1x64로 바꿈
            # predict의 출력값도 2차원 배열 1x1
            v = self.model.predict(nst.reshape(1, 64))[0, 0]
            if v > maxv: maxp, maxnst, maxv = h, nst, v

        return maxnst, maxp, maxv

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

        # 보상을 episode에서 처리
        # 보상을 계산 (Win : 1, Lose : -1, Draw : 0)
        reward = win-1
        # 학습할 데이터를 위해 x, y를 준비
        x, y = [], []
        # 에피소드를 거꾸로 거슬러서 처리
        for st, v in self.episode[::-1]:
            rw = (1-self.alpha)*v + self.alpha*reward
            x.append(st)
            y.append(rw)
            reward *= self.gamma
        # 인공신경망 학습
        xarray, yarray = np.array(x), np.array(y)
        # xarray, yarray를 이용해서 학습
        r = self.model.fit(xarray, yarray,
                           epochs = self.epochs,
                           batch_size = self.batchSize)
        # weights 출력
        weights = self.model.get_weights()[0]
        for i in range(8):
            for j in range(8):
                print(f"{weights[i*8+j, 0]:5.2f}", end=' ')
            print('')
        # 현재까지 학습한 데이터를 자동 저장
        if self.gameCount%10 == 0:
            saveFile = Game.cpPath.format(self.gameCount)
            print(f"Save weights {saveFile}")
            self.model.save_weights(saveFile)
        return win, result


    # 준비가 되었다고 명령을 받았을 때 처리
    def onBoard(self, buf):
        # packet = LEN bd <결과>
        nst, p, v = self.action(buf)
        if p < 0: return False
        self.send("0008 pt %04d"%p)
        self.episode.append( (nst, v) )
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















        
