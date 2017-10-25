import os
import sys
import traci
import time
import numpy as np
import traffic_light

DIR = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.basename(DIR)
FILE = os.path.splitext(sys.argv[0])[0]

collect_data = False
if len(sys.argv) > 1:
    if sys.argv[1] == '--data' or sys.argv[1] == '-d':
        collect_data = True
    else:
        raise Exception('Argument not available...')

sumoCmd = ["sumo-gui", "-c", FOLDER + ".sumocfg"]  # sumo-gui for simulation
traci.start(sumoCmd)
step = 0
steps = 2000

tlList = []
tlAppend = tlList.append
for tlID in traci.trafficlights.getIDList():
    tlAppend(traffic_light.TrafficLight(tlID, collect_data=collect_data))
while step < steps:
    traci.simulationStep()
    for tl in tlList:
        tl.update()
    # Gives new vehicle a color
    for newVeh in traci.simulation.getDepartedIDList():
        col = np.random.rand(3) * 255
        traci.vehicle.setColor(newVeh, (col[0], col[1], col[2], 0))

    step += 1

if collect_data:
    tl.exportDataFrame()
traci.close()
