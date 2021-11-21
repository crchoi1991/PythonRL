# nxm 슬라이딩 퍼즐 섞어놓기
import random





n, m = map(int, input("세로와 가로의 크기 입력 : ").split())

# 퍼즐을 초기화하고 퍼즐을 랜덤하게 섞어놓도록 합니다.
puzzle = [ [ r*m+c+1 for c in range(m) ] for r in range(n) ]
puzzle[n-1][m-1] = 0

# 비어있는 곳의 위치 설정
emptyr, emptyc = n-1, m-1

# n*m*100번에 걸쳐서 섞어놓기
for _ in range(n*m*100):
    v = random.randrange(4)
    # 왼쪽의 숫자를 옮겨오기
    if v == 0 and emptyc > 0:
        puzzle[emptyr][emptyc] = puzzle[emptyr][emptyc-1]
        emptyc -= 1
    # 오른쪽의 숫자를 옮겨오기
    elif v == 1 and emptyc < m-1:
        puzzle[emptyr][emptyc] = puzzle[emptyr][emptyc+1]
        emptyc += 1
    # 위의 숫자를 옮겨오기
    elif v == 2 and emptyr > 0:
        puzzle[emptyr][emptyc] = puzzle[emptyr-1][emptyc]
        emptyr -= 1
    # 아래의 숫자를 옮겨오기
    elif v == 3 and emptyr < n-1:
        puzzle[emptyr][emptyc] = puzzle[emptyr+1][emptyc]
        emptyr += 1

# 비어있는 칸의 숫자 넣기
puzzle[emptyr][emptyc] = 0


# 퍼즐을 출력합니다.
fmt = "{:^3}|"
for r in range(n):
    print("+" + "---+"*m)
    s = "|"
    for c in range(m):
        if r == emptyr and c == emptyc: s += fmt.format("")
        else: s += fmt.format(puzzle[r][c])
    print(s)
print("+" + "---+"*m)




