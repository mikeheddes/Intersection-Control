import numpy as np
import traci as tr
from traci import vehicle as trv
import time

import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.basename(DIR)
FILE = os.path.splitext(sys.argv[0])[0]

sumoCmd = ["sumo-gui", "-c", FOLDER + ".sumocfg"]  # sumo-gui for simulation
tr.start(sumoCmd)
step = 0
steps = 8000


class sigmd(object):
    @staticmethod
    def func(z):
        return 1.0 / (1.0 + np.exp(-z))

    @staticmethod
    def funcP(z):
        return np.exp(-z) / np.power(1 + np.exp(-z), 2)


def getDistance(laneID, pos):
    tlPosition = np.asarray(tr.lane.getShape(laneID)[1])
    delta = np.subtract(tlPosition, pos)
    return np.sqrt(np.power(delta[0], 2) + np.power(delta[1], 2))


LANES = tr.trafficlights.getControlledLanes(tr.trafficlights.getIDList()[0])
lanes_number = len(LANES)
all_lanes = tr.lane.getIDList()
input_vehicle_size = 2 + lanes_number + 1
hidden_encoder_size = 200
hidden_vehicle_size = 40
stdv = .1
routeID = tr.route.getIDList()[0]
learning_rate = 0.008

H_1 = np.zeros((1, hidden_encoder_size))
# W1_hh = np.random.randn(hidden_encoder_size, hidden_encoder_size) * stdv
# W1_vh = np.random.randn(input_vehicle_size, hidden_encoder_size) * stdv
# W1_vv = np.random.randn(input_vehicle_size, hidden_vehicle_size) * stdv
# b1_h = np.zeros((1, hidden_encoder_size))
# b1_v = np.zeros((1, hidden_vehicle_size))
# W2_h = np.random.randn(hidden_encoder_size, 1) * stdv
# W2_v = np.random.randn(hidden_vehicle_size, 1) * stdv
# b2 = np.zeros(1)


with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models', '2017-11-09_15-18_biases_weights.npz'), 'rb') as f2:
    nps = np.load(f2)
    W1_hh = nps['W1_hh']
    W1_vh = nps['W1_vh']
    W1_vv = nps['W1_vv']
    b1_h = nps['b1_h']
    b1_v = nps['b1_v']
    W2_h = nps['W2_h']
    W2_v = nps['W2_v']
    b2 = nps['b2']
    f2.close()

while step < steps:
    tr.simulationStep()
    # Gives new vehicle a color
    for newVeh in tr.simulation.getDepartedIDList():
        col = np.random.rand(3) * 255
        trv.setColor(newVeh, (col[0], col[1], col[2], 0))

    # make input
    vehIDs = trv.getIDList()
    vehIDs = list(filter(lambda x: trv.getLaneID(x) in LANES, vehIDs))
    X = np.zeros((len(vehIDs), 2 + lanes_number + 1))
    for i in range(len(vehIDs)):
        ID = vehIDs[i]
        laneID = trv.getLaneID(ID)
        X[i][0] = getDistance(laneID, trv.getPosition(ID)) / 300  # dist
        X[i][1] = trv.getSpeed(ID) / tr.lane.getMaxSpeed(laneID)  # speed
        X[i][2 + LANES.index(laneID)] = 1  # lane
        # X[i][2 + lanes_number + LANES.index(laneID)] = 1  # dist lane
        X[i][-1] = 1  # exit lane

    # forward
    hhz = np.dot(H_1, W1_hh) + np.sum(np.dot(X, W1_vh), axis=0) + b1_h
    hha = sigmd.func(hhz)
    hvz = np.dot(X, W1_vv) + b1_v
    hva = sigmd.func(hvz)
    outH = np.dot(hha, W2_h) + b2
    outV = np.dot(hva, W2_v)
    output = sigmd.func(outH + outV)

    # get traci calculated speed
    # Y = np.zeros((len(vehIDs), 1))
    # for i in range(len(vehIDs)):
    #     Y[i][0] = tr.vehicle.getSpeed(vehIDs[i])
    # loss = np.sum(np.power(Y - output, 2)) / 2
    # if (step % 500 == 0):
    #     print('\n\n', loss)
    #
    # # back prop
    # EL = (output - Y) * sigmd.funcP(outH + outV)  # QUADRATIC LOSS PRIME
    # b2 -= learning_rate * np.sum(EL, axis=0)
    #
    # # h update
    # EH = np.dot(EL, W2_h.T)
    # dWh = np.dot(hha.T, np.mean(EL, axis=0).reshape(1, -1))
    # W2_h -= learning_rate * dWh
    # b1_h -= learning_rate * np.sum(EH, axis=0)
    # dWhh = np.dot(H_1.T, np.mean(EH, axis=0).reshape(1, -1))
    # dWvh = np.dot(X.T, EH)
    # W1_hh -= learning_rate * dWhh
    # W1_vh -= learning_rate * dWvh
    #
    # # v update
    # EV = np.dot(EL, W2_v.T)
    # dVh = np.dot(hva.T, EL)
    # W2_v -= learning_rate * dVh
    # b1_v -= learning_rate * np.sum(EV, axis=0)
    # dVh = np.dot(X.T, EV)
    # W1_vv -= learning_rate * dVh

    H_1 = hha

    for ID, v in zip(vehIDs, output):
        trv.slowDown(ID, v, 0)

    step += 1
tr.close()

# fileName = time.strftime("%Y-%m-%d_%H-%M")
# filePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models', fileName + '_biases_weights.npz')
# f1 = open(filePath, 'wb')
# np.savez(f1, b1_h=b1_h,
#          b1_v=b1_v,
#          b2=b2,
#          W1_hh=W1_hh,
#          W1_vh=W1_vh,
#          W1_vv=W1_vv,
#          W2_h=W2_h,
#          W2_v=W2_v)
# f1.close()
