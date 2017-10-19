import os
import sys
import traci
import time
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

sumoCmd = ["sumo-gui", "-c", FOLDER + ".sumocfg"] #sumo-gui for simulation
traci.start(sumoCmd)
step = 0
steps = 200


tl = traffic_light.TrafficLight(collect_data)
while step < steps:
    traci.simulationStep()
    tl.update()
    step += 1

if collect_data:
    tl.exportDataFrame()
traci.close()
