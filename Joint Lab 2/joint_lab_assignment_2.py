# -*- coding: utf-8 -*-
"""Joint Lab Assignment 1.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1W4o4-IuhJQwfN1WZm6yabAqdDIYxzJKh

Author: Yu Bai, Yutian Chen, Tianxiao Wei
"""

import numpy as np
import matplotlib.pyplot as plt
np.set_printoptions(precision=2)

delta_t = 0.00001
pi = np.pi

def pwm2rot(pwm):
        # maps from PWM to rotational speed in rad/s
        return pwm * 100 * 2 * pi / 60

class envir:
    # the environment is a rectangular consisting 4 walls bounding an open space
    # the positions of the walls are x=0, y=0, x=length, y=width
    def __init__(self, length, width):
        self.length = length
        self.width = width

class robot:

    def __init__(self, envir, width, diameter, x0 = 0, y0 = 0, theta0 = 0, ifOutput = True, ifPlot = True):
        self.envir = envir
        self.width = width
        self.diameter = diameter
        self.x = x0
        self.y = y0
        self.theta = theta0
        self.front_dist = 0
        self.right_dist = 0
        self.rot_speed = 0
        self.ns_mag_field = 0
        self.ew_mag_field = 0
        self.update_sensor()
        self.measure()
        if ifOutput:
            self.output()
        if ifPlot:
            self.plot()

    def move(self, pwm_l, pwm_r, ifOutput = True, ifPlot = True):
        width = self.width
        theta = self.theta
        # map from PWM to rotation speed
        rot_l = pwm2rot(pwm_l)
        rot_r = pwm2rot(pwm_r)

        # B is the matrix in x(t+1) = A*x(t) + B*u(t)
        B = delta_t * self.diameter/2 * np.array([[1/2 * np.cos(theta), 1/2 * np.cos(theta)],[1/2 * np.sin(theta), 1/2 * np.sin(theta)], [-1/width, 1/width]])
        # input is the input vector u(t)
        input = np.array([[rot_l],[rot_r]])

        # if the potential destination is out of the envrionment (blocked by a wall), it will not move
        [[pot_x], [pot_y], [pot_theta]] = [[self.x], [self.y], [self.theta]] + B.dot(input)
        # if pot_x < 0 or pot_x > self.envir.length or pot_y < 0 or pot_y > self.envir.width:
        #     # print("The robot didn't move because it is out of bound")
        #     if ifOutput:
        #         self.output()
        #     if ifPlot:
        #         self.plot()
        #     return

        # updates the system state with x(t+1) = A*x(t) + B*u(t)
        [self.x, self.y, self.theta] = [pot_x, pot_y, pot_theta]

        # reduce theta to be in the range of [0,2*pi)
        self.theta = np.remainder(self.theta, 2*pi)

        # self.update_sensor() # update the sensors
        # updates the rotational speed
        self.rot_speed = self.diameter/(2 * width) * (rot_r - rot_l)
        # self.measure() # provide sensor outputs
        if ifOutput:
            self.output()
        if ifPlot:
            self.plot()

    def update_sensor(self):
        # update the equations for the sensor lasers
        # y = mf*x + bf describes the laser from the front sensor
        # note that np.tan() will never be undefined due to the limitations of computer calculation,
        # thus we will have always have the function y = mf*x + bf for all states
        self.mf = np.tan(self.theta)
        self.bf = self.y - self.mf * self.x
        # y = mr*x + br describes the laser from the right sensor
        self.mr = np.tan(self.theta - pi/2)
        self.br = self.y - self.mr * self.x

    def measure(self):
        # in simulation, instead of directly obtaining outputs from the sensors, we calculate the sensor outputs with current state, input, and noise
        # calculate the intersection and distance between the front laser and the rectangular walls
        # if we know the x-coordinate of the wall, y = mx + b
        # if we know the y-coordinate of the wall, x = (y-b)/m
        l = self.envir.length
        w = self.envir.width
        mf = self.mf
        bf = self.bf
        mr = self.mr
        br = self.br

        # front_inter[0] to front_inter[4] are the intersections with the walls on the right, top, left, buttom, right
        # front_inter[4] is used to simply future calculations
        front_inter = np.zeros((5,2))
        if l*mf+bf >=0 and l*mf+bf <= w:
            front_inter[0] = [l, l*mf+bf]
            front_inter[4] = [l, l*mf+bf]
        if (w-bf)/mf >= 0 and (w-bf)/mf <= l: 
            front_inter[1] = [(w-bf)/mf, w]
        if bf >=0 and bf <= w:
            front_inter[2] = [0, bf]
        if -bf/mf >= 0 and -bf/mf <= l:
            front_inter[3] = [-bf/mf, 0]

        # if 0 <= theta < pi/2, we only need to consider the intersection with the right or top wall
        # if pi/2 <= theta < pi, we only need to consider the intersection with the top or left wall
        # if pi <= theta < 3pi/2, we only need to consider the intersection with the left or buttom wall
        # if 3pi/2 <= theta < 2pi, we only need to consider the intersection with the buttom or right wall
        # therefore, we use np.floor(theta/(pi/2)) to determine which walls need to be considered
        # since the laser y=mx+b will only intersect with one of the two adajacent walls, and the coordinate is set to [0,0] if there is no intersection,
        # we can directly compute the intersection by adding the values of adjacent rows in front_inter
        idx = int(np.floor(self.theta/(pi/2)))
        front_inter_loc = front_inter[idx] + front_inter[idx+1]
        self.front_dist = np.sqrt(np.power(self.x-front_inter_loc[0],2) + np.power(self.y-front_inter_loc[1],2))

        # right_inter[0] to right_inter[4] are the intersections with the walls on the buttom, right, top, left, buttom
        # right_inter[4] is used to simply future calculations  
        right_inter = np.zeros((5,2))
        if -br/mr >= 0 and -br/mr <= l:
            right_inter[0] = [-br/mr, 0]
            right_inter[4] = [-br/mr, 0]
        if l*mr+br >=0 and l*mr+br <= w:
            front_inter[1] = [l, l*mr+br]
        if (w-br)/mr >= 0 and (w-br)/mr <= l: 
            front_inter[2] = [(w-br)/mr, w]
        if br >=0 and br <= w:
            front_inter[3] = [0, br]

        # similar to the calculation of the front intersection
        idx = int(np.floor(self.theta/(pi/2)))
        right_inter_loc = right_inter[idx] + right_inter[idx+1]
        self.right_dist = np.sqrt(np.power(self.x-right_inter_loc[0],2) + np.power(self.y-right_inter_loc[1],2))


        # calculate the north-south and east-west magnetic field
        self.ns_mag_field = np.sin(self.theta)
        self.ew_mag_field = np.cos(self.theta)


    def output(self):
        print("x, y, theta                = ", ', '.join(str(i) for i in [self.x, self.y, self.theta]))
        print("front distance             = ", self.front_dist)
        print("right distance             = ", self.right_dist)
        print("rotational speed           = ", self.rot_speed)
        print("north-south magnetic field = ", self.ns_mag_field)
        print("east-west magnetic field   = ", self.ew_mag_field)

    def plot(self):
        plt.figure(figsize = (10,10))
        # plot the rectangular environment
        plt.vlines(x=[0, self.envir.length], ymin=0, ymax=self.envir.width)
        plt.hlines(y=[0, self.envir.width], xmin=0, xmax=self.envir.length)
        # plot the position of the robot
        plt.plot(self.x, self.y, 'ro')
        # plot the front and right sensor
        plt.quiver([self.x, self.x], [self.y, self.y],[np.cos(self.theta), np.sin(self.theta)], [np.cos(self.theta-pi/2), np.sin(self.theta-pi/2)], 
                   angles='xy', scale_units='xy', scale=1)
        plt.show()

"""Simulate with the computational model"""

from google.colab import auth
auth.authenticate_user()

import gspread
from oauth2client.client import GoogleCredentials

gc = gspread.authorize(GoogleCredentials.get_application_default())
wb = gc.open_by_url('https://docs.google.com/spreadsheets/d/1Jv4ateZAPZhsDAL9saXa3-0c4lD2703_EIYd3hE8Tuc/edit?usp=sharing')
sheet = wb.worksheet('Sheet1') # Sheet1 contains the inputs for the five trajectories to be tested
data = np.array(sheet.get_all_values())
pwm_l = np.array(data[5:26,27], dtype=np.float)/600 # get the pwm for the left wheel
pwm_r = np.array(data[5:26,28], dtype=np.float)/600 # get the pwm for the right wheel

e = envir(10,10)
paperbot = robot(e,width=90,diameter=50,x0=122.48,y0=201.4,theta0=pi/4,ifOutput=False,ifPlot=False) # initial conditions for robots

x_py = np.zeros((500,1)) # stores the x state values over time
y_py = np.zeros((500,1)) # stores the y state values over time
theta_py = np.zeros((500,1)) # stores the theta state values over time
t_py = np.zeros((500,1)) # stores time
index = 0

for i in range(20):
    l_init = pwm_l[i]
    l_end = pwm_l[i+1]
    r_init = pwm_r[i]
    r_end = pwm_r[i+1]
    for j in range(25000):
        # record states every 0.01 seconds
        if j % 1000 == 0:
            x_py[index] = paperbot.x
            y_py[index] = paperbot.y
            theta_py[index] = paperbot.theta
            t_py[index] = i*0.25 + j/100000
            index = index + 1
        # the wheels' angular velocities change linearly with time 
        l = l_init + (l_end-l_init)*j/25000
        r = r_init + (r_end-r_init)*j/25000
        paperbot.move(l,r,ifOutput=False,ifPlot=False)

theta_py = theta_py * 360 / (2*pi) # converts angular displacement to degrees

sheet = wb.worksheet('Sheet2')
data = np.array(sheet.get_all_values())
x_sw = np.array(data[7:226,44], dtype=np.float)
y_sw = np.array(data[7:226,43], dtype=np.float)
theta_sw = np.array(data[7:226,45], dtype=np.float)
t_sw = np.array(data[7:226,42], dtype=np.float)

plt.plot(t_py, x_py)
plt.plot(t_sw, x_sw)
plt.legend(['Python','SolidWorks'])
plt.title('x State Trajectory 4')
plt.show()

plt.plot(t_py, y_py)
plt.plot(t_sw, y_sw)
plt.legend(['Python','SolidWorks'])
plt.title('y State Trajectory 4')
plt.show()

plt.plot(t_py, theta_py)
plt.plot(t_sw, theta_sw)
plt.legend(['Python','SolidWorks'])
plt.title('theta State Trajectory 4')
plt.show()

plt.plot(x_py, y_py)
plt.plot(x_sw, y_sw)
plt.legend(['Python','SolidWorks'])
plt.title('x-y State Trajectory 4')
plt.show()

from google.colab import drive
drive.mount('/content/gdrive/')

with open('/content/gdrive/My Drive/Trajectory4_sw.txt', 'w') as outfile:
    outfile.write(" ".join(str(item) for item in t_sw))
    outfile.write("\n")
    outfile.write(" ".join(str(item) for item in x_sw))
    outfile.write("\n")
    outfile.write(" ".join(str(item) for item in y_sw))
    outfile.write("\n")
    outfile.write(" ".join(str(item) for item in theta_sw)) 

with open('/content/gdrive/My Drive/Trajectory4_py.txt', 'w') as outfile:
    outfile.write(" ".join(str(item) for item in t_py))
    outfile.write("\n")
    outfile.write(" ".join(str(item) for item in x_py))
    outfile.write("\n")
    outfile.write(" ".join(str(item) for item in y_py))
    outfile.write("\n")
    outfile.write(" ".join(str(item) for item in theta_py))

