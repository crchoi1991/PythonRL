import math
import random as pr
import cv2 as cv
import numpy as np

LEFT = -1
STAY = 0
RIGHT = 1

q = [[[1.0,1.0,1.0] for i in range(800)] for j in range(200)]

def animate(t, hose):
    print( len(t) )
    vid = cv.VideoWriter("pos_cos0"+str(hose)+".avi",-1,500,(500,500),True)
    almu = 0
    for i in t:
        if almu%1 == 0:
            img = np.zeros((500, 500, 3), np.uint8)
            th = i[0][2]
            x = int(250.0 + math.sin(th)*250.0)
            y = int(400.0 - math.cos(th)*250.0)
            cv.line(img,(250,400), (x,y), (212,255,127), 5, lineType=cv.LINE_AA)
            vid.write(img)
        almu += 1



def mouse_click(event, x, y, flags, param):
    if event == cv.EVENT_LBUTTONDOWN:
        mouse = True
        print( q[x-100][y-400] )

def show_time(time):
    img = np.zeros((820,len(time),3), np.uint8)
    maks = max(time)
    for i in range(len(time)):
        img[int(800*time[i]/maks),i] = [255,255,255]

    cv.imshow("Times", img)
    while True:
        k = cv.waitKey(1)&0xFF
        if k == ord('q'):
            break

def show_values():
    img = np.zeros((800,200,3), np.uint8)
    for i in range(-400,400):
        for j in range(-100,100):
            if q[j][i] == [1.0,1.0,1.0]:
                continue
            elif q[j][i][LEFT] >= q[j][i][STAY] and q[j][i][LEFT] >= q[j][i][RIGHT]:    #LEFT
                img[i+400,j+100] = [0,255,0]                                            #GREEN
            elif q[j][i][STAY] >= q[j][i][LEFT] and q[j][i][STAY] >= q[j][i][RIGHT]:
                img[i+400,j+100] = [255,255,255]
            else:                                                                       #RIGHT
                img[i+400,j+100] = [0,0,255]                                            #RED
    img[:,100] = [255,0,0]
    img[400,:] = [255,0,0]
    cv.imshow("The best action", img)
    cv.imwrite("depression.png", img)
    while True:
        k = cv.waitKey(1)&0xFF
        if k == ord('q'):
            break

#CartPole class based on https://github.com/stober/cartpole
class CartPole(object):

    def __init__(self, x = 0.0, xdot = 0.0, theta = 0.0, thetadot = 0.0):
        self.x = x
        self.xdot = xdot
        self.theta = theta
        self.thetadot = thetadot

        self.alpha = 0.4
        self.gamma = 1.0

        self.asdf = 0.0

        # some constants
        self.gravity = 9.8
        self.masscart = 1.0
        self.masspole = 0.1
        self.total_mass = (self.masspole + self.masscart)
        self.length = 0.5		  # actually half the pole's length
        self.polemass_length = (self.masspole * self.length)
        self.force_mag = 10.0
        self.tau = 0.02		  # seconds between state updates
        self.fourthirds = 1.3333333333333

    def failure(self):
        angle = math.pi/2
        if not -angle < self.theta < angle:
            return True
        else:
            return False

    def reset(self):
        self.x,self.xdot,self.theta,self.thetadot = (0.0,0.0,0.01,0.0)

    def random_policy(self, *args):
        return pr.randint(-1,1)

    def single_episode(self, policy = None, eta=1.0, neg=0):
        self.reset()
        if policy is None: policy = self.random_policy

        self.asdf = neg

        trace = []
        eps = 0.0
        if eta == 0.0:
            eps=0.0
        else:
            eps = 1.0/eta
        next_action = policy(self.x,self.xdot,self.theta,self.thetadot,eps)
        while not self.failure() and len(trace)<150000:
            pstate, paction, reward, state = self.move(next_action)
            next_action = policy(self.x,self.xdot,self.theta,self.thetadot,eps)

            pang = int(pstate[2]*180/math.pi)
            pspd = int(pstate[3]*180/math.pi)
            ang = int(state[2]*180/math.pi)
            spd = int(state[3]*180/math.pi)
            q[pang][pspd][paction] += self.alpha*(reward + self.gamma*q[ang][spd][next_action] - q[pang][pspd][paction])

            trace.append([pstate, paction, reward, state, next_action])

        return trace

    def state(tmp):
        angle = math.pi/2
        if not -angle < tmp < angle:
            return -1

        return int(act*180/math.pi)

    def reward(self):
        if False:#self.failure():
            return 0
        else:
            return math.cos(self.theta)-self.asdf

    def move(self, action, boxed=False): # binary L/R action
        force = 0.0
        if action > 0:
            force = self.force_mag
        elif action < 0:
            force = -self.force_mag
        else:
            force = 0.0

        costheta = math.cos(self.theta)
        sintheta = math.sin(self.theta)

        tmp = (force + self.polemass_length * (self.thetadot ** 2) * sintheta) / self.total_mass;
        thetaacc = (self.gravity * sintheta - costheta * tmp) / (self.length * (self.fourthirds - self.masspole * costheta ** 2 / self.total_mass))
        xacc = tmp - self.polemass_length * thetaacc * costheta / self.total_mass

        (px,pxdot,ptheta,pthetadot) = (self.x, self.xdot, self.theta, self.thetadot)

        self.x += self.tau * self.xdot
        self.xdot += self.tau * xacc
        self.theta += self.tau * self.thetadot
        self.thetadot += self.tau * thetaacc

        return [px,pxdot,ptheta,pthetadot],action,self.reward(),[self.x,self.xdot, self.theta, self.thetadot]

if __name__ == '__main__':

    cp = CartPole()

    def greedy_policy(x,xdot,theta,thetadot, eps):
        tmp1 = int(theta*180/math.pi)
        tmp2 = int(thetadot*180/math.pi)
        if pr.random() < eps:
            return pr.randint(-1,1)
        else:
            max_a = STAY
            for i in range(-1,2):
                if q[tmp1][tmp2][i] > q[tmp1][tmp2][max_a]:
                    max_a = i
            return max_a
    time = []

    for j in [10]:
        q = [[[1.0,1.0,1.0] for r in range(800)] for t in range(200)]
        for i in range(10000):
            t = cp.single_episode(greedy_policy,2.0,j/10.0)
            print (i)
        for i in range(10):
            t = cp.single_episode(greedy_policy,10.0,j/10.0)
            print (i)
            print (len(t))

        t = cp.single_episode(greedy_policy,0.0,j/10.0)
        animate(t,j)

    #show_values()
    #show_time(time)
    cv.destroyAllWindows()
