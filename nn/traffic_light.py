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

    def __init__(self, ID, collect_data=False, training=False):
        self.ID = ID
        self.training = training
        self.controlledLanes = tratl.getControlledLanes(self.ID)
        self.timeInPhase = 0
        self.comfortAcceleration = 4
        self.df = pd.DataFrame()
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
        self.Tl = {l: 0 for l in self.controlledLanes}
        self.light_change = traci.simulation.getCurrentTime()
        lanes_number = len(LANES)
        input_vehicle_size = 2 + lanes_number * 2
        hidden_encoder_size = 20
        hidden_vehicle_size = 4
        stdv = .1

        H_1 = np.zeros(hidden_encoder_size)
        W1_hh = np.random.randn(hidden_encoder_size, hidden_encoder_size) * stdv
        W1_vh = np.random.randn(input_vehicle_size, hidden_encoder_size) * stdv
        W1_vv = np.random.randn(input_vehicle_size, hidden_vehicle_size) * stdv
        b1_h = np.zeros(hidden_encoder_size)
        b1_v = np.zeros(hidden_vehicle_size)
        W2_h = np.random.randn(hidden_encoder_size, 1) * stdv
        W2_v = np.random.randn(hidden_vehicle_size, 1) * stdv
        b2 = np.zeros(1)

    # def light_switch(self):
    #     vehIDs = trave.getIDList()
    #     for vehID in vehIDs:
    #         lane = trave.getLaneID(vehID)
    #         if lane in self.controlledLanes:
    #             self.Tl[lane] += np.less_equal(trave.getSpeed(vehID), 2) * \
    #                 traci.simulation.getDeltaT()
    #
    #     if self.light_change + 10000 < traci.simulation.getCurrentTime():
    #         maxTl = np.amax(list(self.Tl.values()))
    #         indexMaxTl = list(self.Tl.values()).index(maxTl)
    #         tratl.setPhase(self.ID, indexMaxTl)
    #         self.Tl[list(self.Tl.keys())[indexMaxTl]] = 0
    #         self.light_change = traci.simulation.getCurrentTime()

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
        self.updateVehicles()
        if self.training:
            self.updateTime()
            self.setTimeTillGreen()
            self.setTimeTillRed()
            self.setTimeTillNextGreen()
            self.updateAdviceSpeed()

    def updateVehicles(self):
        '''Retreve and update the state of all vehicles in ICData'''
        self.removePastVehicles()
        for laneID, lane in self.ICData.items():
            for vehicle in lane:
                pos = trave.getPosition(vehicle["id"])
                vehicle["x"] = pos[0]
                vehicle["y"] = pos[1]
        self.addNewVehicles()

    def addNewVehicles(self):
        for ID in trave.getIDList():
            LaneID = trave.getLaneID(ID)
            if LaneID in self.controlledLanes:
                if ID not in [d['id'] for d in self.ICData[LaneID] if 'id' in d]:
                    pos = trave.getPosition(ID)
                    self.ICData[LaneID] += [{"id": ID,
                                             "x": pos[0], "y":pos[1]}]

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
