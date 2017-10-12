# System
import re
import time
# Third party
import traci
from traci import trafficlights as tratl
from traci import vehicle as trave
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt


class TrafficLight(object):

    def __init__(self, collect_data):
        self.ID = tratl.getIDList()[0]
        self.controlledLanes = tratl.getControlledLanes(self.ID)
        self.timeInPhase = 0
        self.comfortAcceleration = 4
        self.df = pd.DataFrame()
        self.vehicleCount = 0
        self.collect_data = collect_data
        self.phases = tratl.getCompleteRedYellowGreenDefinition(self.ID)[
            0]._phases
        self.phase = 0
        self.ICData = {lane:[] for lane in self.controlledLanes}
        print (self.ICData)

    def getAdviseSpeed(self, vehID):
        distance = self.getDistance(vehID)
        notivicationDistance = self.getNotivicationDistance(vehID)
        maxSpeed = traci.lane.getMaxSpeed(trave.getLaneID(vehID))
        speed = trave.getSpeed(vehID)

        def calculateBeforeRed():
            if self.makeItBeforeRed(timeTillRed, maxSpeed, distance, vehID):
                return maxSpeed
            else:
                return distance / self.getTimeTillNextGreen(vehID)

        if distance is not None and distance > notivicationDistance:
            timeTillGreen = self.getTimeTillGreen(vehID) / 1000
            timeTillRed = self.getTimeTillRed(vehID) / 1000

            if timeTillGreen > 0:
                speed = (distance - notivicationDistance) / timeTillGreen
                if speed > maxSpeed:
                    speed = calculateBeforeRed()
            else:
                speed = calculateBeforeRed()
        else:
            speed = maxSpeed
        accelTime = np.absolute(int((speed - trave.getSpeed(vehID)) /
                                    self.comfortAcceleration * 1000))
        if self.collect_data:
            self.addToDataFrame(vehID)
        return speed, accelTime

    def getDistance(self, vehID):
        vehPosition = np.asarray(trave.getPosition(vehID))
        vehLane = trave.getLaneID(vehID)
        if vehLane in self.controlledLanes:
            tlPosition = np.asarray(traci.lane.getShape(vehLane)[1])
            delta = np.subtract(tlPosition, vehPosition)
            d = (np.sqrt(np.add(np.power(delta[0], 2), np.power(delta[1], 2))))
        else:
            d = None
        return d

    # def carDistance
    #     vehLane = trave.getLaneID(vehID)
    #     try:
    #         laneIndex = self.controlledLanes.index(vehLane)
    #     if vehLane in self.controlledLanes:


    def getTimeTillGreen(self, vehID):
        vehLane = trave.getLaneID(vehID)
        try:
            laneIndex = self.controlledLanes.index(vehLane)
        except ValueError as e:
            laneIndex = None
        if laneIndex is not None:
            currentPhase = tratl.getCompleteRedYellowGreenDefinition(self.ID)[
                0]._currentPhaseIndex
            greenCheck = re.compile("[gG]")
            phases = tratl.getCompleteRedYellowGreenDefinition(self.ID)[
                0]._phases
            phasesCicle = list(range(currentPhase, len(phases)))
            if currentPhase is not 0:
                phasesCicle.extend(list(range(0, currentPhase)))
            duration = -(self.timeInPhase)
            for i in phasesCicle:
                if greenCheck.match(phases[i]._phaseDef[laneIndex]):  # if green
                    break
                else:
                    duration += phases[i]._duration
        else:
            duration = None
        return duration

    def getTimeTillNextGreen(self, vehID):
        vehLane = trave.getLaneID(vehID)
        greens = 0
        try:
            laneIndex = self.controlledLanes.index(vehLane)
        except ValueError as e:
            laneIndex = None
        if laneIndex is not None:
            currentPhase = tratl.getCompleteRedYellowGreenDefinition(self.ID)[
                0]._currentPhaseIndex
            greenCheck = re.compile("[gG]")
            phases = tratl.getCompleteRedYellowGreenDefinition(self.ID)[
                0]._phases
            phasesCicle = list(range(currentPhase, len(phases)))
            if currentPhase is not 0:
                phasesCicle.extend(list(range(0, currentPhase)))
            duration = -(self.timeInPhase)
            for i in phasesCicle:
                if greenCheck.match(phases[i]._phaseDef[laneIndex]):
                    greens += 1
                    if greens is 2:
                        break
                else:
                    duration += phases[i]._duration
        else:
            duration = None
        return duration

    def getNotivicationDistance(self, vehID):
        speed = trave.getSpeed(vehID)
        return (speed / self.comfortAcceleration * speed)+12
        """ +12 = minimal distance to ignore traffic lights """

    def update(self):
        self.updateTime()
        self.updateVehicles()

    def updateVehicles(self):
        DepartIDs = traci.simulation.getDepartedIDList()
        for ID in DepartIDs:
            LaneID = trave.getLaneID(ID)
            if LaneID in self.controlledLanes:
                Position = trave.getPosition(ID)
                self.ICData[LaneID]+=[{"id":ID,"x":Position[0],"y":Position[1]}]
        print(self.ICData)

    def updateTime(self):
        nextSwitch = tratl.getNextSwitch(self.ID)
        time = traci.simulation.getCurrentTime()
        phaseTime = tratl.getPhaseDuration(self.ID)
        self.timeInPhase = phaseTime - (nextSwitch - time)
        # if time % 10000 == 0:
        #     self.phase = tratl.getPhase(self.ID) + 1
        #     if self.phase >= len(self.phases):
        #         self.phase = 0
        #     tratl.setPhase(self.ID, self.phase)

    def getTimeTillRed(self, vehID):
        vehLane = trave.getLaneID(vehID)
        try:
            laneIndex = self.controlledLanes.index(vehLane)
        except ValueError as e:
            laneIndex = None
        if laneIndex is not None:
            currentPhase = tratl.getCompleteRedYellowGreenDefinition(self.ID)[
                0]._currentPhaseIndex
            redCheck = re.compile("[r]")
            phases = tratl.getCompleteRedYellowGreenDefinition(self.ID)[
                0]._phases
            phasesCicle = list(range(currentPhase, len(phases)))
            if currentPhase is not 0:
                phasesCicle.extend(range(0, currentPhase))
            duration = -(self.timeInPhase)
            for i in phasesCicle:
                if redCheck.match(phases[i]._phaseDef[laneIndex]):  # if green
                    break
                else:
                    duration += phases[i]._duration
        else:
            duration = None
        return duration

    def addToDataFrame(self, vehID):
        self.df = self.df.append({"message_time": traci.simulation.getCurrentTime(),
                                  "vehicle_number": self.getVehicleNumber(vehID),
                                  "vehID": vehID,
                                  "x": trave.getPosition(vehID)[0],
                                  "y": trave.getPosition(vehID)[1],
                                  "v": trave.getSpeed(vehID),
                                  "s": trave.getDistance(vehID)}, ignore_index=True)

    def getVehicleNumber(self, vehID):
        if len(self.df.index) > 0:
            dist = self.df.query('vehID == "{}"'.format(vehID))
            if len(dist.index) > 0:
                if dist.tail(1).iloc[0]['s'] <= trave.getDistance(vehID) or dist.tail(1).iloc[0]['s'] != -1001:
                    number = dist.tail(1).iloc[0]['vehicle_number']
                else:
                    self.vehicleCount += 1
                    number = self.vehicleCount
            else:
                self.vehicleCount += 1
                number = self.vehicleCount
        else:
            self.vehicleCount += 1
            number = self.vehicleCount
        return number

    def exportDataFrame(self):
        self.df.index.name = 'index'
        self.df.to_csv('data.csv')

    def makeItBeforeRed(self, timeTillRed, maxSpeed, distance, vehID):
        return timeTillRed * maxSpeed > distance + trave.getLength(vehID)

    def getID(self):
        return self.ID

    def getControlledLanes(self):
        return self.controlledLanes
