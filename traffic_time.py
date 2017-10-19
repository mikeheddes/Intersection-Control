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


class TrafficTime():
    def setTimeTillGreen(self):
        for laneID, time in self.timeTillGreen.items():
            laneIndex = self.controlledLanes.index(laneID)
            currentPhase = tratl.getCompleteRedYellowGreenDefinition(self.ID)[
                0]._currentPhaseIndex
            phases = tratl.getCompleteRedYellowGreenDefinition(self.ID)[
                0]._phases
            phasesCicle = list(range(currentPhase, len(phases)))
            if currentPhase is not 0:
                phasesCicle.extend(list(range(0, currentPhase)))
            duration = -(self.timeInPhase)
            for i in phasesCicle:
                if self.greenCheck.match(phases[i]._phaseDef[laneIndex]):
                    break
                else:
                    duration += phases[i]._duration
            self.timeTillGreen[laneID] = duration / 1000

    def setTimeTillNextGreen(self):
        for laneID, time in self.timeTillNextGreen.items():
            greens = 0
            laneIndex = self.controlledLanes.index(laneID)
            currentPhase = tratl.getCompleteRedYellowGreenDefinition(self.ID)[
                0]._currentPhaseIndex
            phases = tratl.getCompleteRedYellowGreenDefinition(self.ID)[
                0]._phases
            phasesCicle = list(range(currentPhase, len(phases)))
            if currentPhase is not 0:
                phasesCicle.extend(list(range(0, currentPhase)))
            duration = -(self.timeInPhase)
            for i in phasesCicle:
                if self.greenCheck.match(phases[i]._phaseDef[laneIndex]):
                    greens += 1
                    if greens is 2:
                        break
                    else:
                        duration += phases[i]._duration
                else:
                    duration += phases[i]._duration
            self.timeTillNextGreen[laneID] = duration / 1000

    def setTimeTillRed(self):
        for laneID, time in self.timeTillRed.items():
            laneIndex = self.controlledLanes.index(laneID)
            currentPhase = tratl.getCompleteRedYellowGreenDefinition(self.ID)[
                0]._currentPhaseIndex
            phases = tratl.getCompleteRedYellowGreenDefinition(self.ID)[
                0]._phases
            phasesCicle = list(range(currentPhase, len(phases)))
            if currentPhase is not 0:
                phasesCicle.extend(range(0, currentPhase))
            duration = -(self.timeInPhase)
            for i in phasesCicle:
                if i is currentPhase:
                    duration += phases[i]._duration
                else:
                    if self.redCheck.match(phases[i]._phaseDef[laneIndex]):
                        break
                    else:
                        duration += phases[i]._duration
            self.timeTillRed[laneID] = duration / 1000

    def updateTime(self):
        nextSwitch = tratl.getNextSwitch(self.ID)
        time = traci.simulation.getCurrentTime()
        phaseTime = tratl.getPhaseDuration(self.ID)
        self.timeInPhase = phaseTime - (nextSwitch - time)
        ''' Switches to next phase after 10000 time is past
        if time % 10000 == 0:
            self.phase = tratl.getPhase(self.ID) + 1
            if self.phase >= len(self.phases):
                self.phase = 0
            tratl.setPhase(self.ID, self.phase)'''
