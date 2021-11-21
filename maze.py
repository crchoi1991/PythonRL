# 미로 만들기
import random

# 각각의 방향에 대한 값 (4방향 모두 꽉 차있다고 하면 15란 값을 가진다.)
UP = 8
RIGHT = 4
DOWN = 2
LEFT = 1

# maze에 통로를 만드는 함수
def mazesplit(maze, r, c, n, m):
    # 가로와 세로의 크기가 모두 1이면 종료
    if n == 1 and m == 1: return
    select = 0
    if n == 1: select = 1
    elif m == 1: select = 0
    else: select = random.randrange(0, 2)
    # 통로를 만들 선택이 세로인 경우
    if select == 0:
        u = random.randrange(0, n-1)
        for _ in range(2):
            v = random.randrange(0, m)
            if (maze[u+r][v+c] & DOWN) == 0: continue
            # 위에 있는 칸에서는 아래쪽에 통로를 만들고
            maze[u+r][v+c] -= DOWN
            # 아래에 있는 칸에서는 위쪽에 통로를 만듭니다.
            maze[u+r+1][v+c] -= UP
        # 나누어진 칸에 대해서 mazesplit을 실행합니다.
        mazesplit(maze, r, c, u+1, m)
        mazesplit(maze, r+u+1, c, n-u-1, m)
    # 통로를 만들 선택이 가로인 경우
    else:
        u = random.randrange(0, m-1)
        for _ in range(2):
            v = random.randrange(0, n)
            if (maze[v+r][u+c] & RIGHT) == 0: continue
            # 왼쪽에 있는 칸에서는 오른쪽에 통로를 만들고
            maze[v+r][u+c] -= RIGHT
            # 오른쪽에 있는 칸에서는 왼쪽에 통로를 만듭니다.
            maze[v+r][u+c+1] -= LEFT
        mazesplit(maze, r, c, n, u+1)
        mazesplit(maze, r, c+u+1, n, m-u-1)

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
mazesplit(maze, 0, 0, n, m)

# maze를 출력합니다.
mazeprint(maze, n, m)
