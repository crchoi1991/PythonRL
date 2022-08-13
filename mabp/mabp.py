import numpy as np
import random

# e-greedy 클래스
class EpsilonGreedy:
    # Initialize
    def __init__(self, epsilon):
        self.epsilon = epsilon    # 탐색 확률

    # nArms : 슬롯머신의 개수
    def initialize(self, nArms):
        self.n = np.zeros(nArms)
        self.v = np.zeros(nArms)
        self.m = np.zeros(nArms)

    # Select arm
    def selectArm(self):
        if random.random() < self.epsilon:
            return np.random.randint(0, len(self.v))
        return np.argmax(self.m)

    # Update parameters
    def update(self, chosenArm, reward):
        self.n[chosenArm] += 1
        self.v[chosenArm] += reward
        self.m[chosenArm] = self.v[chosenArm]/self.n[chosenArm]

    # Get rewards
    def reward(self):
        return sum(self.v)/sum(self.n)

# Slot arm 클래스
class SlotArm:
    # Initialize
    def __init__(self, p):
        self.p = p

    # Get a reward for chosen arm
    def draw(self):
        return 1.0 if random.random() < self.p else 0.0

# run
def play(epsilon, arms, nTimes):
    times = np.zeros(nTimes)
    rewards = np.zeros(nTimes)

    algo = EpsilonGreedy(epsilon)
    algo.initialize(len(arms))
    for t in range(nTimes):
        times[t] = t+1
        chosenArm = algo.selectArm()
        reward = arms[chosenArm].draw()
        algo.update(chosenArm, reward)
        rewards[t] = algo.reward()
    return times, rewards

"""
import matplotlib.pyplot as plt
import matplotlib.style

t = int(input("Number of times : "))
a = int(input("Number of arms : "))
it = int(input("Number of iterations : "))
e = float(input("epsilon : "))

# Make arms
arms = [SlotArm(random.random()) for _ in range(a)]

# Simulation
times = np.arange(1, t+1)
rewards = np.zeros(t)
for _it in range(it):
    _, r = play(e, arms, t)
    rewards += r/float(it)

# Plot chart
matplotlib.style.use('bmh')
_, ax = plt.subplots(1, 1)
ax.plot(times, rewards)
plt.show()
"""


import matplotlib.pyplot as plt
import matplotlib.style
s = int(input("Number of simulations : "))
t = int(input("Number of times : "))
a = int(input("Number of arms : "))
it = int(input("Number of iterations : "))
# Make arms
arms = [SlotArm(random.random()) for _ in range(a)]
epsilons = np.zeros(s)
rewards = np.zeros(s)
e = 0.01
# Simulation
for sim in range(s):
    epsilons[sim] = e
    for _it in range(it):
        _, r = play(e, arms, t)
        rewards[sim] += r[-1]/float(it)
    e += 0.99/float(s+1)
# Plot chart
matplotlib.style.use('bmh')
_, ax = plt.subplots(1, 1)
ax.plot(epsilons, rewards)
plt.title(f"arms={a}, times={t}")
plt.xlabel("epsilon")
plt.show()

