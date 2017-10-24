# System
import sys
import re
import os
# Third party
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
import matplotlib

DIR = os.path.dirname(os.path.abspath(__file__))
style.use(os.path.join(DIR, 'style.mplstyle'))

skipPosition = 10
data_file = 'data.csv'
vehicle_number = 1
for arg in sys.argv:
    print(arg)
    if re.match("^-d=|^--data=", arg):  # Use -d="data.csv"
        data_file = re.split("=", arg)[-1]
    elif re.match("^-v=|^--vehicle=", arg):  # Use -v="1,2,3"
        vehicle_number = re.split("=", arg)[-1]
        vehicle_number = re.split(",\s*", vehicle_number)

df = pd.read_csv(data_file)
df.set_index('index', inplace=True)

sizes = []
for veh in vehicle_number:
    data = df.query('vehicle_number == {}'.format(veh))
    sizes.append(len(data.index))

v = [np.zeros(y) for y in sizes]
A = [np.zeros(y) for y in sizes]
t = [np.zeros(y) for y in sizes]
x = [np.zeros(y) for y in sizes]
y = [np.zeros(y) for y in sizes]

for i in range(len(vehicle_number)):
    data = df.query('vehicle_number == {}'.format(vehicle_number[i]))
    v[i] = data.as_matrix(columns=['v']).reshape(-1)
    A[i] = data.as_matrix(columns=['vAD']).reshape(-1)
    t[i] = data.as_matrix(columns=['message_time']).reshape(-1)
    x[i] = data.as_matrix(columns=['x']).reshape(-1).reshape(-1)
    y[i] = data.as_matrix(columns=['y']).reshape(-1).reshape(-1)

# fig = plt.figure(1)
# fig.suptitle('Figure 1', fontsize=14, fontweight='bold')
# fig.subplots_adjust(hspace=0.45)
fig,ax = plt.subplots()
for vi, ti, veh, AD in zip(v, t, vehicle_number, A):
    ax.plot(ti, vi, label="vehicle {}".format(veh))
    ax.plot(ti, AD, label="vehicle {} AD".format(veh))
ax.legend()
ax.set_title('Speed of the vehicles')
ax.set_xlabel('time (steps)')
ax.set_ylabel('speed (m/s)')

# ax1 = fig.add_subplot(211)
# for vi, ti, veh, AD in zip(v, t, vehicle_number, A):
#     ax1.plot(ti, vi, label="vehicle {}".format(veh))
#     ax1.plot(ti, AD, label="vehicle {} AD".format(veh))
# ax1.legend()
# ax1.set_title('Speed of the vehicles')
# ax1.set_xlabel('time (steps)')
# ax1.set_ylabel('speed (m/s)')

# ax2 = fig.add_subplot(212)
# ax2.axis('equal')
# ax2.axis([0, 200, 0, 200])
# for xi, yi, veh in zip(x, y, vehicle_number):
#     ax2.scatter(xi[0::skipPosition], yi[0::skipPosition],
#                 s=2, label="vehicle {}".format(veh))
# ax2.legend()
# ax2.set_title('Path of the vehicles')
# ax2.set_xlabel('x position (m)')
# ax2.set_ylabel('y position (m)')

plt.show()
