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
# Own
from traffic_time import *


class TrafficLight(TrafficTime):

    def __init__(self, ID, collect_data=False):
        self.ID = ID
        self.controlledLanes = tratl.getControlledLanes(self.ID)
        self.timeInPhase = 0
        self.comfortAcceleration = 4
        self.df = pd.DataFrame()
        self.prScore = pd.DataFrame()
        self.vehicleCount = 0
        self.collect_data = collect_data
        self.phases = tratl.getCompleteRedYellowGreenDefinition(self.ID)[
            0]._phases
        self.phase = 0
        self.greenCheck = re.compile("[gG]")
        self.redCheck = re.compile("[r]")
        self.ICData = {lane: [] for lane in self.controlledLanes}
        self.timeTillGreen = {lane: None for lane in self.controlledLanes}
        self.timeTillNextGreen = {lane: None for lane in self.controlledLanes}
        self.timeTillRed = {lane: None for lane in self.controlledLanes}
        self.Tl = np.zeros(len(self.ICData))
        self.light_change = traci.simulation.getCurrentTime()

    def light_switch(self):
        for laneID, lane in self.ICData.items():
            if(len(lane) > 0):
                self.Tl[list(self.ICData.keys()).index(laneID)] = self.calcDistW(lane, laneID) + self.calcStopW(lane)
                # print(self.calcDistW(lane, laneID), self.calcStopW(lane))
            else:
                self.Tl[list(self.ICData.keys()).index(laneID)] = 0
        self.Tl = self.softmax(self.Tl)
        # print(self.Tl)
        # print(self.ICData)
        if self.light_change + 10000 < traci.simulation.getCurrentTime():
            maxTl = np.argmax(self.Tl)
            # Change phase duration instead of the phase itself
            tratl.setPhase(self.ID, maxTl)
            # self.Tl[maxTl] = 0
            self.light_change = traci.simulation.getCurrentTime()
        # self.addScoreToFrame()

    def addScoreToFrame(self):
        self.prScore = self.prScore.append({"1": self.Tl[0],
                                  "2": self.Tl[1],
                                  "3": self.Tl[2],
                                  "4": self.Tl[3]}, ignore_index=True)

    def exportScoreFrame(self):
        self.prScore.index.name = 'index'
        self.prScore.to_csv('score.csv')

    @staticmethod
    def calcStopW(lane):
        stopW = 0.01
        return np.sum(list(map(lambda x: x["<<"], lane))) * stopW

    def calcDistW(self, lane, laneID):
        distW = 0.5
        imgDist = 300
        imgDistW = 0
        return np.sum(list(map(lambda x: -np.power(1 / imgDist, 3) * np.power(self.getDistance(laneID, x["x"], x["y"]) - imgDist, 3), lane))) * distW
        #np.sum(list(map(lambda x: ((imgDistW - 1) / imgDist * self.getDistance(laneID, x["x"], x["y"]) + 1), lane))) * distW

    @staticmethod
    def softmax(z):
        z -= np.amax(z, keepdims=True)
        return np.exp(z) / np.sum(np.exp(z), keepdims=True)

    def updateAdviceSpeed(self):
        for laneID, lane in self.ICData.items():
            for vehNumber in range(len(lane)):
                veh = lane[vehNumber]
                distance = self.getDistance(laneID, veh["x"], veh["y"])
                notifyDistance = self.getNotifydDistance(veh["id"], vehNumber)
                speed, time = self.getAdviseSpeed(
                    veh["id"], distance, notifyDistance, laneID)
                traci.vehicle.slowDown(veh["id"], speed, int(time))

    def getAdviseSpeed(self, vehID, distance, notifyDistance, laneID):
        maxSpeed = traci.lane.getMaxSpeed(laneID)
        speed = trave.getSpeed(vehID)

        def calculateBeforeRed():
            if self.makeItBeforeRed(self.timeTillRed[laneID], maxSpeed, distance, vehID):
                return maxSpeed
            else:
                return self.calcSpeed(distance - notifyDistance, self.timeTillNextGreen[laneID])

        if distance > notifyDistance:
            if self.timeTillGreen[laneID] > 0:
                speed = self.calcSpeed(distance - notifyDistance,
                                       self.timeTillGreen[laneID])
                if speed > maxSpeed:
                    speed = calculateBeforeRed()
            else:
                speed = calculateBeforeRed()
        else:
            speed = maxSpeed
        accelTime = np.absolute(
            (speed - trave.getSpeed(vehID)) / self.comfortAcceleration * 1000)
        if self.collect_data:
            self.addToDataFrame(vehID, speed)
        return speed, max(min(accelTime, 1e6), -1e6)

    @staticmethod
    def calcSpeed(s, t):
        return s / (t + 1e-5)

    @staticmethod
    def getDistance(laneID, x, y):
        tlPosition = np.asarray(traci.lane.getShape(laneID)[1])
        delta = np.subtract(tlPosition, [x, y])
        return np.sqrt(np.add(np.power(delta[0], 2), np.power(delta[1], 2)))

    # def carDistance
    #     vehLane = trave.getLaneID(vehID)
    #     try:
    #         laneIndex = self.controlledLanes.index(vehLane)
    #     if vehLane in self.controlledLanes:

    def getNotifydDistance(self, vehID, vehNumber):
        speed = trave.getSpeed(vehID)
        return (speed / self.comfortAcceleration * speed) + 13 + 10 * vehNumber
        """ +13 = minimal distance to ignore traffic lights
        add vehicles in front * length"""

    def update(self):
        self.updateTime()
        self.setTimeTillGreen()
        self.setTimeTillRed()
        self.setTimeTillNextGreen()
        self.updateVehicles()
        self.updateAdviceSpeed()

    def updateVehicles(self):
        '''Retreve and update the state of all vehicles in ICData'''
        self.removePastVehicles()
        for laneID, lane in self.ICData.items():
            for vehicle in lane:
                pos = trave.getPosition(vehicle["id"])
                vehicle["x"] = pos[0]
                vehicle["y"] = pos[1]
                vehicle["<<"] += np.less_equal(trave.getSpeed(vehicle["id"]), .5)
        self.addNewVehicles()

    def addNewVehicles(self):
        for ID in trave.getIDList():
            LaneID = trave.getLaneID(ID)
            if LaneID in self.controlledLanes:
                if ID not in [d['id'] for d in self.ICData[LaneID] if 'id' in d]:
                    pos = trave.getPosition(ID)
                    self.ICData[LaneID] += [{"id": ID,
                                             "x": pos[0], "y":pos[1], "<<": 0}]

    def removePastVehicles(self):
        '''Removes the first car if the laneID is not in controlledLanes
        then check next car till laneID is in controlledLanes'''
        for laneID, lane in self.ICData.items():
            while len(lane) > 0:
                if trave.getLaneID(lane[0]["id"]) not in self.controlledLanes:
                    lane.pop(0)
                else:
                    break

    def addToDataFrame(self, vehID, adviceSpeed):
        self.df = self.df.append({"message_time": traci.simulation.getCurrentTime(),
                                  "vehicle_number": self.getVehicleNumber(vehID),
                                  "vehID": vehID,
                                  "x": trave.getPosition(vehID)[0],
                                  "y": trave.getPosition(vehID)[1],
                                  "v": trave.getSpeed(vehID),
                                  "s": trave.getDistance(vehID),
                                  "vAD": adviceSpeed}, ignore_index=True)

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
        self.df.to_csv('data_%s.csv' % (self.ID))

    def makeItBeforeRed(self, timeTillRed, maxSpeed, distance, vehID):
        return timeTillRed * maxSpeed > distance + trave.getLength(vehID)
