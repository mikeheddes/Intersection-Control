import numpy as np
import traci as tr
from traci import traci.vehicle as trv

lanes_number = 3
input_vehicle_size = 3 + lanes_number * 2
hidden_encoder_size = 20
hidden_vehicle_size = 4


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


FOLDER = os.path.basename(DIR)
sumoCmd = ["sumo-gui", "-c", FOLDER + ".sumocfg"]  # sumo-gui for simulation
traci.start(sumoCmd)
step = 0
steps = 2000

H_1 = np.zeros(hidden_encoder_size)
W1_hh = np.random.randn((hidden_encoder_size, hidden_encoder_size))
W1_vh = np.random.randn((input_vehicle_size, hidden_encoder_size))
W1_vv = np.random.randn((input_vehicle_size, hidden_vehicle_size))
b1_h = np.zeros(hidden_encoder_size)
b1_v = np.zeros(hidden_vehicle_size)
W2_h = np.random.randn((hidden_encoder_size, 1))
W2_v = np.random.randn((hidden_vehicle_size, 1))
b2 = np.zeros(1)

LANES = tr.trafficlights.getControlledLanes(tr.trafficlights.getIDList()[0])

while step < steps:
    tr.simulationStep()
    # Gives new vehicle a color
    for newVeh in tr.simulation.getDepartedIDList():
        col = np.random.rand(3) * 255
        trv.setColor(newVeh, (col[0], col[1], col[2], 0))

    vehIDs = trv.getIDList()
    X = np.zeros((len(vehIDs), 2 + len(LANES) * 2))
    for i in range(len(vehIDs)):
        ID = vehIDs[i]
        laneID = trv.getLaneID(ID)
        X[i][0] = getDistance(laneID, trv.getPosition(ID))
        X[i][1] = trv.getSpeed(ID) / tr.lane.getMaxSpeed(laneID)
        X[i][2 + LANES.index(laneID)] = 1
        X[i][2 + len(LANES) + LANES.index(laneID)] = 1

    hh = np.dot(H_1, W1_hh) + np.sum(np.dot(vehInput, W1_vh), axis=0) + b1_h
    hh = sigmd.func(hh)
    hv = np.dot(vehInput, W1_vv) + b1_v
    hv = sigmd.func(hv)
    outH = np.dot(hh, W2_h) + b2
    output = sigmd.func(outH + np.dot(hv, W2_v))
    H_1 = hh

    for ID, v in zip(vehIDs, output):
        trv.slowDown(ID, v, 1)

    step += 1
