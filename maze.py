# 미로 만들기
import random

# 각각의 방향에 대한 값 (4방향 모두 꽉 차있다고 하면 15란 값을 가진다.)
UP = 8
RIGHT = 4
DOWN = 2
LEFT = 1
MULTIPASS = 1

# maze에 통로를 만드는 함수
def mazesplit(maze, lt, rb):
    # 가로와 세로의 크기가 모두 1이면 종료
    if lt == rb: return
    # 통로를 만들 선택이 세로인 경우
    if lt[0] == rb[0] or (lt[1] != rb[1] and random.randrange(0, 2) == 0):
        u = random.randrange(lt[1], rb[1])
        for _ in range(MULTIPASS):
            v = random.randrange(lt[0], rb[0]+1)
            if (maze[u][v] & DOWN) == 0: continue
            # 위에 있는 칸에서는 아래쪽에 통로를 만들고
            maze[u][v] -= DOWN
            # 아래에 있는 칸에서는 위쪽에 통로를 만듭니다.
            maze[u+1][v] -= UP
        # 나누어진 칸에 대해서 mazesplit을 실행합니다.
        mazesplit(maze, lt, (rb[0], u))
        mazesplit(maze, (lt[0], u+1), rb)
    # 통로를 만들 선택이 가로인 경우
    else:
        v = random.randrange(lt[0], rb[0])
        for _ in range(MULTIPASS):
            u = random.randrange(lt[1], rb[1]+1)
            if (maze[u][v] & RIGHT) == 0: continue
            # 왼쪽에 있는 칸에서는 오른쪽에 통로를 만들고
            maze[u][v] -= RIGHT
            # 오른쪽에 있는 칸에서는 왼쪽에 통로를 만듭니다.
            maze[u][v+1] -= LEFT
        mazesplit(maze, lt, (v, rb[1]))
        mazesplit(maze, (v+1, lt[1]), rb)

def mazeprint(maze, n, m):
    for r in range(n):
        str = "+"
        for c in range(m):
            if (maze[r][c] & UP) != 0: str += "--+"
            else: str += "  +"
        print(str)
        str = "|"
        for c in range(m):
            if (maze[r][c] & RIGHT) != 0: str += "  |"
            else: str += "   "
        print(str)
    print("+"+"--+"*m)

n, m = map(int, input("세로의 크기와 가로의 크기 입력 :  ").split())
print(n, m)

# maze 생성
maze = [ [15]*m for _ in range(n) ]

# maze에 통로를 만듭니다.
mazesplit(maze, (0, 0), (m-1, n-1))

# maze를 출력합니다.
mazeprint(maze, n, m)
