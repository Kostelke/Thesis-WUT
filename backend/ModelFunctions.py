from ipaddress import summarize_address_range
from typing import List
from numpy import double
from ortools.linear_solver import pywraplp
from ortools.init import pywrapinit
from ortools.sat.python import cp_model
import math


def createNode(nodeName, demand, index):
    """
    Creates basic node element. Each node represents a node in powergrid graph.

    ----ARGUMENTS----

    nodeName -  node/ powerplant name

    demand - expressed in MW, range 0-infinity, describes energy consumption by node.
    Generation and demand in the same node is not mutually exclusive

    index - for indexing node, generated automatically when adding new nodes to grid. Allows
    access to nodes as if they were part of array

    plants - Array of plants pseudo-objects (not defined by class), allows to populate node with generation units. If no
    plants are present the node is assumed to draw energy

    ---RETURNS----
    Node structure 
    """
    node = {
        "nodeName" : nodeName,
        "demand" : demand,
        "index" : index,
        "plants" : [],
    }
    return node


def createPlants(sourceNode, plantName, blockName, Pmin, Pmax, cost =1, ramp = 20,):
    """
    Creates plant - each plant is generating unit with specific parameters. They are not defined as class.
   
    ---ARGUMENTS----

    sourceNode - Node which this block is part of. Allows to bind block to node
    
    plantName - Name of plant, used in displaying result as well to indetify plant 

    blockName - used for constraint
    and comparison purposes, identifies blocks in powerplant

    Pmin - expressed in MW, defines minimum amount of energy that block can generate while working properly
    
    Pmax - expressed in MW, defines maximum amount of energy that block can generate while working properly

    Ramp - expressed in MW/h, defines change in energy generation which block can make per each time period ( 1 hour)
    ie. ramp of 20 means that every hour, power generation in block can be changed by 20 MW max.f no ramp argument is specified, ramp
    value will be set to difference between Pmax and Pmin ( no restriction on changing power generation)

    ----RETURNS----
    plant object representing powerblock in plant.
    """
    sourceNode["plants"].append({
        "plantName" : plantName,
        "blockName" : blockName,
        "Pmin" : double(Pmin),
        "Pmax" : double(Pmax),
        "ramp" : ramp,
        "cost" : cost,
    })

def getNode(nodeList, nodeToFind):
    """
    Allows to retrieve node from list of nodes

    ----ARGUMENTS----

    nodeList - list of all nodes

    nodeToFind - name of the node that  is to be found

    ----RETURNS----
    Node if present or 0 if not found
    """
    for node in nodeList:
        if node["nodeName"] == nodeToFind:
            return node
    return 0

def loadNode(fileNodes):
    """
    Creates list of nodes from input file.
    Given list of nodes ( see file formatting for further information) uses 
    createNode() method to generate array of nodes. Created list has no plants
   
    ----ARGUMENTS----
 
    fileNodes - list of nodes

    ----RETURNS----

    Formatted list of nodes that may be populated with plants

    """
    nodeList = []
    count = 0
    file = open(fileNodes, 'r')
    for line in file:  
        _initialData = []
        for word in line.split(","):
            _initialData.append(word)
        nodeList.append(
            createNode(_initialData[0], _initialData[1] , count)
            )            
        count = count + 1
    file.close
    return nodeList



def loadPlants(nodeList, filePlants):
    """
    For given list of nodes and input file ( see file formatting for further information),
    Populates node list with powerplants. 
    method will try to read additional arguemnt from file,
    which should describe desired ramp
    
    ----ARGUMENTS----

    nodeList - list of nodes
    filePlants - file containing list of powerplants and blocks.

    ----RETURNS----

    Nothing. Used to populate node list with powerplants.
  
     """
    file = open(filePlants, 'r')

    for line in file:  
        _initialData = []
        for word in line.split(","):
            _initialData.append(word)
        if(len(_initialData) == 8):
             createPlants(getNode(nodeList, _initialData[0]), _initialData[1], _initialData[2],  _initialData[3],  _initialData[4], _initialData[6], _initialData[7])
        elif(len(_initialData) == 7):
            createPlants(getNode(nodeList, _initialData[0]), _initialData[1], _initialData[2],  _initialData[3],  _initialData[4], _initialData[6])
        else:
             createPlants(getNode(nodeList, _initialData[0]), _initialData[1], _initialData[2],  _initialData[3],  _initialData[4])


def loadPlantsJSON(nodeList, JSONfile):
    """
    For given list of nodes and JSON file ( see file formatting for further information),
    Populates node list with powerplants. 
    method will try to read additional arguemnt from JSON,
    which should describe desired ramp
    
    ----ARGUMENTS----
    
    nodeList - list of nodes

    JSONfile - JSON containing list of powerplants and blocks.

    ----RETURNS----

    Nothing. Used to populate node list with powerplants.
  
    """
    for object in JSONfile:
        _initialData = []
        _initialData.append(object["sourceNode"])
        _initialData.append(object["plantName"])
        _initialData.append(object["blockName"])
        _initialData.append(object["Pmin"])
        _initialData.append(object["Pmax"])
        _initialData.append(object["cost"])

        if "ramp" in object:
            _initialData.append(object["ramp"])
        if(len(_initialData) == 7):
            createPlants(getNode(nodeList, _initialData[0]), _initialData[1], _initialData[2],  _initialData[3],  _initialData[4], _initialData[5], _initialData[6])
        else:
            createPlants(getNode(nodeList, _initialData[0]), _initialData[1], _initialData[2],  _initialData[3],  _initialData[4], _initialData[5])


def createEdge(nodeA, nodeB,  capacity, admitance, voltageA, voltageB):
    """
    Creates edge representing power line, between two nodes.

    ----ARGUMENTS----

    nameA - node A name

    nameB - node B name
   
    capacity - expressed in MW, defines maximum load of line

    Admitance - expressed in S ( Siemens)

    VoltageA, VoltageB - Voltage at each of the nodes connected by edge.

    ----RETURNS----
    an edge with parameters provided
    """
    edge = {
        "name" : nodeA + nodeB,
        "capacity": double(capacity),
        "admitance" : double(admitance),
        "voltageA" : double(voltageA),
        "voltageB" : double(voltageB),
        "nodeA" : nodeA,
        "nodeB" : nodeB,
    }
    return edge

def loadEdges(fileEdges):
    """
    Creates list of edges from input file  ( see file formatting for further information) 

    ----ARGUMENTS----

    fileEdges - file containing edge data

    ----RETURNS----

    list of edges
    """
    edgeList = []
    file = open(fileEdges, 'r')
    for line in file:
        _initialData = []
        for word in line.split(","):
            _initialData.append(word)
        edgeList.append(createEdge(_initialData[0], _initialData[1], _initialData[2], _initialData[3], _initialData[4], _initialData[5]))
    file.close
    return edgeList

def isNeighbour(nodeA, nodeB, edges):
    """
    Checks whether two nodes are connected by any of the edges present in list of edges.

    ----ARGUMENTS----

    nodeA - node A name

    nodeB - node B name

    edges - list of all edges

    ----RETURNS----

    Returns edge which connects those nodes or -1 if there is no such edge
    """
    for edge in edges:
        if nodeA+nodeB == edge["name"] or nodeB+nodeA == edge["name"]:
            return edge
    return -1

def getSourceVoltage(nodeA,nodeB, edge):
    """
    Given two nodes and edge connecting them, returns voltage of source node 
    ie. the one for which constraint is currently being defined

    ----ARGUMENTS----

    nodeA - node A name

    nodeB - node B name

    edge - edge connecting A and B

    ----RETURNS----
    returns voltage of source node

    """
    if nodeA["nodeName"] + nodeB["nodeName"] == edge["name"]:
        return edge["voltageA"]
    else: 
        return edge["voltageB"]

def createNodeVariablesSimple(solver: pywraplp.Solver, nodes, _globalDemand, time):
    """
    Given a solver and list of nodes, creates solver variables based on input data.
    This method is simple version which assumes plants are always working in range of their Pmin and
    Pmax. When using simple variables be sure to use appropiate constraint method - otherwise 
    the solver will crash

    ----ARGUMENTS----
    
    solver - solver to which variables are added

    nodes - list of all nodes

    _globalDemand - array of demands for each node

    time - cycle number for which variables are created

    
    ----RETURNS----

    an array of solver variables for use in further methods
    """
    plantsInNodes = []
    for node in nodes:
            solverNode = {
                "nodeName" : node["nodeName"],
                "demand" : node["demand"] * _globalDemand[0],
                "plants" : [],
                "plantCost": []
            }
            if len(node["plants"]) != 0:
                for plant in node["plants"]:
                    # We set minimimum to 0 so that we can turn off the plants!! remember about it!!
                    solverNode["plants"].append(
                        solver.NumVar(0, plant["Pmax"], plant["plantName"]+"_"+plant["blockName"])
                    )
                    solverNode["plantCost"].append(plant["cost"])
            else :
                solverNode["plants"].append(
                    solver.NumVar(0, 0, node["nodeName"])
                )
                solverNode["plantCost"].append(1)

            plantsInNodes.append(solverNode)
    return plantsInNodes

def createNodeVariablesBinary(solver: pywraplp.Solver, nodes, _globalDemand, time):
    """
    Given a solver and list of nodes, creates solver variables based on input data.
    This method is binary version which includes binary variable from solver - allow for situations in which one power plant is 
    to be swithed off completly.
    In that case we assume that power plant was at minimum power capcity in one time period and then switched off
    in the next
  
    ----ARGUMENTS----
    
    solver - solver to which variables are added

    nodes - list of all nodes

    _globalDemand - array of demands for each node

    time - cycle number for which variables are created

    
    ----RETURNS----
    
    an array of solver variables for use in further methods
    """
    plantsInNodes = []
    for node in nodes:
            solverNode = {
                "nodeName" : node["nodeName"],
                "demand" : node["demand"] * _globalDemand[0],
                "plants" : [],
                "isPlantWorking" : [], # binary variable, same size as plants, defines if block is working
                "plantCost": []
            }
            if len(node["plants"]) != 0:
                for plant in node["plants"]:
                    solverNode["plants"].append(
                        solver.NumVar(0, plant["Pmax"], plant["plantName"]+"_"+plant["blockName"])
                    ) # Pmin is set to 0 because we want to allow powerplant to be shut down - if you change it it will break
                    solverNode["isPlantWorking"].append(
                        solver.BoolVar(plant["blockName"] +  " Is working: ")
                    )
                    solverNode["plantCost"].append(plant["cost"])
            else :
                solverNode["plants"].append(
                    solver.NumVar(0, 0, node["nodeName"])
                )
                solverNode["isPlantWorking"].append(
                    solver.BoolVar( node["nodeName"] + " Is not working")
                )
                solverNode["plantCost"].append(1)
            plantsInNodes.append(solverNode)
    return plantsInNodes



def createPhaseVariables(solver: pywraplp.Solver, nodes):
    """
    Given solver and list of all nodes, creates phase variables for each node and stores them in 
    phaseVariable array. Used to determine phase in each node for purpose of energy transfer through 
    power lines
    
    ----ARGUMENTS----

    solver - solver in whivh variables are created
    
    nodes - list of all nodes

    ----RETURNS----

   an array of solver variables for use in further methods
    """
    phaseVariable = []
    maxPhase = math.pi
    for node in nodes:
        phaseVariable.append(
                solver.NumVar(-maxPhase, maxPhase, node["nodeName"])
            )
    phaseVariable[0] =  solver.NumVar(0, 0, node["nodeName"])
    return phaseVariable

def createEdgeFlowVariables(solver: pywraplp.Solver, nodes, edges, edgeSolutionPeriods):
    """
    Given solver, list of all nodes and list of all edges, create
    flow variables for this edges. Method creates double the amount of edges that are given to allow easier 
    calculations and constraints creation. for nodeA and nodeB
    edgeflow variable going from A to B and from B to A will be created. They will be equal but have opposite sign.

    ----ARGUMENTS----
    
    solver - solver to which variables are added

    nodes - list of all nodes

    edges - list of all edges

    edgeSolutionPeriods - array that will store edge variables betweeen cycles

    
    ----RETURNS----

   an array of solver variables for use in further methods
    """
    edgeFlowVariables = []

    for nodeA in nodes:
            flowAB = []
            for nodeB in nodes:
                flag = isNeighbour(nodeA["nodeName"], nodeB["nodeName"], edges)
                if flag != -1:
                    edgeDataObject = {
                        "srcNodeVolt" : getSourceVoltage(nodeA, nodeB, flag),
                        "dstNodeVolt" : getSourceVoltage(nodeB, nodeA, flag),
                        "var" : solver.NumVar(-flag["capacity"], flag["capacity"], nodeA["nodeName"]+nodeB["nodeName"]),
                        "nodeA": nodeA["nodeName"],
                        "nodeB": nodeB["nodeName"],
                        "capacity": flag["capacity"],
                    }
                    flowAB.append(edgeDataObject)
                if flag == -1: 
                    flowAB.append(0)
            edgeFlowVariables.append(flowAB)
    edgeSolutionPeriods.append(edgeFlowVariables)
    return edgeFlowVariables

def createComplexConstraints(solver: pywraplp.Solver, nodes, edges, edgeFlowVariables, phaseVariable, plantsInNodes, periodOfTime, time, _globalDemand, shortage = [], strictMode = True):
    """
    Complex version of constraints, includes binary variables and ramp power generation - used with binary variables but 
    plants should have ramp specified
    Creates all constraints used in model - this is a complete method to do so but it can be implemented 
    manually. As per createNodeVariable you should provide global demand array and time period for which
    to create constraints and a set of constraint from previous period of time ( so for t-1)
    strictMode determines if constraint are strict ( ie no overflow or demand in node) or not, by 
    including additional variables defined as shortage and overflow, specific to this node. 
    This method needs model variables provided by createXXXVariable methods and 
    list of edges and nodes. Constraint are added to solver model and to the current period of time array holding all constraints


    ----ARGUMENTS----
    
    solver - solver to which variables are added

    nodes - list of all nodes

    edges - list of all edges

    edgeFlowVariables - array of solver variables for edges

    phaseVariable - array of solver variables for phase
    
    plantsInNodes - array of solver variables for individual powerpalnts

    periodOfTime - Array of cycles, that contains  all variables used for individual cycles

    time - time period for which calculations are run ( ie 1, 2, 3)

    _globalDemand - array of cycles storing demand for each node per cycle

    shortage - array to store shortages in power generation

    stricMode - specifies whether calculations are strict or relaxed ( thus allowing to not satisfy demand in nodes)
    
    ----RETURNS----

    Nothing. Adds created variables and constraints to the periodOfTime array under current cycle
    
    """
    for nodeA in nodes:
            neighbouringEdges = []
            for nodeB in nodes:
                edgeToConstrain = isNeighbour(nodeA["nodeName"], nodeB["nodeName"], edges)
                if edgeToConstrain != -1 :
                    edgeFlowDataObject = edgeFlowVariables[nodeA["index"]][nodeB["index"]]
                    neighbouringEdges.append(edgeFlowDataObject["var"])
                    solver.Add(
                        edgeFlowDataObject["var"] == edgeFlowDataObject["srcNodeVolt"] * edgeFlowDataObject["dstNodeVolt"]*edgeToConstrain["admitance"]*(
                            phaseVariable[nodeA["index"]]- phaseVariable[nodeB["index"]]
                            )
                    )
            index = 0
            for plant in plantsInNodes[nodeA["index"]]["plants"]:
                if len(nodes[nodeA["index"]]["plants"]) > 0:
                    solver.Add(
                        plant <= plantsInNodes[nodeA["index"]]["isPlantWorking"][index]*nodes[nodeA["index"]]["plants"][index]["Pmax"]
                    )
                    solver.Add(
                        plant >= plantsInNodes[nodeA["index"]]["isPlantWorking"][index]*nodes[nodeA["index"]]["plants"][index]["Pmin"]
                    )
                    if time > 0:
                        # We need to create xnor logic for determinig proper constraints on changes in power generation
                        # That is because if we have continous operation of plant ( ie isWorking[t] = 1 and isWorking[t-1] = 1)
                        # we want to apply ramp as a constraint in powercchange
                        # however when we have starting powerplant or shutting down power plant 
                        # ( ie isWorking[t] = 1 and isWorking[t-1] = 0 or   isWorking[t] = 0 and isWorking[t-1] = 1)
                        # we want to apply pmin as constraint ( simplistic view )
                        # we may want to apply some additional rules regarding powering on or off -
                        # ie isWorking[t] == 0 if only is Working[t-1] = 0 and isWorking[t-2] =0
                        zVar = solver.BoolVar("Zvar"+nodeA["nodeName"])
                        solver.Add(
                            periodOfTime[time-1][nodeA["index"]]["isPlantWorking"][index] + plantsInNodes[nodeA["index"]]["isPlantWorking"][index] >= zVar
                        )
                        solver.Add(
                              periodOfTime[time-1][nodeA["index"]]["isPlantWorking"][index] - plantsInNodes[nodeA["index"]]["isPlantWorking"][index] <= zVar
                        )
                        solver.Add(
                              -periodOfTime[time-1][nodeA["index"]]["isPlantWorking"][index] + plantsInNodes[nodeA["index"]]["isPlantWorking"][index] <= zVar
                        )
                        solver.Add(
                              2 - periodOfTime[time-1][nodeA["index"]]["isPlantWorking"][index] - plantsInNodes[nodeA["index"]]["isPlantWorking"][index] >= zVar
                        )
                        solver.Add(
                            periodOfTime[time - 1][nodeA["index"]]["plants"][index] - plant <= zVar * nodeA["plants"][index]["Pmin"] + (1-zVar)*nodeA["plants"][index]["ramp"]
                        )
                        solver.Add(
                            periodOfTime[time - 1][nodeA["index"]]["plants"][index] - plant >= -( zVar * nodeA["plants"][index]["Pmin"] + 
                           (1-zVar)*nodeA["plants"][index]["ramp"])
                        )
                    index = index + 1
            if(strictMode):
                solver.Add(
                    sum(plantsInNodes[nodeA["index"]]["plants"]) - nodeA["demand"][time]*_globalDemand[0] - sum(neighbouringEdges)==0
                )
            else: 
                short = solver.NumVar(0, 1000, "Shortage")
                solver.Add(
                    sum(plantsInNodes[nodeA["index"]]["plants"]) - nodeA["demand"][time]*_globalDemand[0] - sum(neighbouringEdges) + short ==0
                )
                shortage.append(short)
    periodOfTime.append(plantsInNodes)




def createBinaryConstraints(solver: pywraplp.Solver, nodes, edges, edgeFlowVariables, phaseVariable, plantsInNodes, periodOfTime, time, _globalDemand, shortage = [], strictMode = True,):
    """
    Binary version of constraints, includes binary variables. Used with binary variables
    Creates all constraints used in model - this is a complete method to do so but it can be implemented 
    manually. As per createNodeVariable you should provide global demand array and time period for which
    to create constraints and a set of constraint from previous period of time ( so for t-1)
    strictMode determines if constraint are strict ( ie no overflow or shortage in node) or not, by 
    including additional variables defined as shortage and overflow, specific to this node. 
    
    This method needs model variables provided by createXXXVariable methods and 
    list of edges and nodes. Constraint are added to solver model and to the current period of time array holding all constraints


    ----ARGUMENTS----
    
    solver - solver to which variables are added

    nodes - list of all nodes

    edges - list of all edges

    edgeFlowVariables - array of solver variables for edges

    phaseVariable - array of solver variables for phase
    
    plantsInNodes - array of solver variables for individual powerpalnts

    periodOfTime - Array of cycles, that contains  all variables used for individual cycles

    time - time period for which calculations are run ( ie 1, 2, 3)

    _globalDemand - array of cycles storing demand for each node per cycle

    shortage - array to store shortages in power generation

    stricMode - specifies whether calculations are strict or relaxed ( thus allowing to not satisfy demand in nodes)
    
    ----RETURNS----

    Nothing. Adds created variables and constraints to the periodOfTime array under current cycle
    
    
    """
    for nodeA in nodes:
            neighbouringEdges = []
            for nodeB in nodes:
                edgeToConstrain = isNeighbour(nodeA["nodeName"], nodeB["nodeName"], edges)
                if edgeToConstrain != -1 :
                    edgeFlowDataObject = edgeFlowVariables[nodeA["index"]][nodeB["index"]]

                    neighbouringEdges.append(edgeFlowDataObject["var"])
                
                    solver.Add(
                        edgeFlowDataObject["var"] == edgeFlowDataObject["srcNodeVolt"] * edgeFlowDataObject["dstNodeVolt"]*edgeToConstrain["admitance"]*(
                            phaseVariable[nodeA["index"]]- phaseVariable[nodeB["index"]]
                            )
                    )
            index = 0
            for plant in plantsInNodes[nodeA["index"]]["plants"]:
                if len(nodes[nodeA["index"]]["plants"]) > 0:
                    solver.Add(
                        plant <= plantsInNodes[nodeA["index"]]["isPlantWorking"][index] * nodes[nodeA["index"]]["plants"][index]["Pmax"]
                    )
                    solver.Add(
                        plant >= plantsInNodes[nodeA["index"]]["isPlantWorking"][index]  * nodes[nodeA["index"]]["plants"][index]["Pmin"]
                    )
                    index = index + 1
            if(strictMode):
                solver.Add(
                    sum(plantsInNodes[nodeA["index"]]["plants"]) - nodeA["demand"][time]*_globalDemand[0] - sum(neighbouringEdges)==0
                )
            else: 
                short = solver.NumVar(0, 1000, "Shortage")
            
                solver.Add(
                    sum(plantsInNodes[nodeA["index"]]["plants"]) - nodeA["demand"][time]*_globalDemand[0] - sum(neighbouringEdges) + short ==0
                )
                shortage.append(short)
    periodOfTime.append(plantsInNodes)



def createSimpleConstraints(solver: pywraplp.Solver, nodes, edges, edgeFlowVariables, phaseVariable, plantsInNodes, periodOfTime, time, _globalDemand, shortage = [], overflow=[], strictMode=True):
    """
    Simple version of constraints used with simple variables method
    Creates all constraints used in model - this is a complete method to do so but it can be implemented 
    manually. As per createNodeVariable you should provide global demand array and time period for which
    to create constraints and a set of constraint from previous period of time ( so for t-1)
    strictMode determines if constraint are strict ( ie no overflow or demand in node) or not, by 
    including additional variables defined as shortage and overflow, specific to this node. 
    
     This method needs model variables provided by createXXXVariable methods and 
    list of edges and nodes. Constraint are added to solver model and to the current period of time array holding all constraints


    ----ARGUMENTS----
    
    solver - solver to which variables are added

    nodes - list of all nodes

    edges - list of all edges

    edgeFlowVariables - array of solver variables for edges

    phaseVariable - array of solver variables for phase
    
    plantsInNodes - array of solver variables for individual powerpalnts

    periodOfTime - Array of cycles, that contains  all variables used for individual cycles

    time - time period for which calculations are run ( ie 1, 2, 3)

    _globalDemand - array of cycles storing demand for each node per cycle

    shortage - array to store shortages in power generation

    stricMode - specifies whether calculations are strict or relaxed ( thus allowing to not satisfy demand in nodes)
    
    ----RETURNS----

    Nothing. Adds created variables and constraints to the periodOfTime array under current cycle
    
    
    """
    for nodeA in nodes:
            neighbouringEdges = []
            for nodeB in nodes:
                edgeToConstrain = isNeighbour(nodeA["nodeName"], nodeB["nodeName"], edges)
                if edgeToConstrain != -1 :
                    edgeFlowDataObject = edgeFlowVariables[nodeA["index"]][nodeB["index"]]
                    neighbouringEdges.append(edgeFlowDataObject["var"])
                    solver.Add(
                        edgeFlowDataObject["var"] == edgeFlowDataObject["srcNodeVolt"] * edgeFlowDataObject["dstNodeVolt"]*edgeToConstrain["admitance"]*(
                            phaseVariable[nodeA["index"]]- phaseVariable[nodeB["index"]]
                            )
                    )
            index = 0
            for plant in plantsInNodes[nodeA["index"]]["plants"]:
                if len(nodes[nodeA["index"]]["plants"]) > 0:
                    solver.Add(
                        plant <= nodes[nodeA["index"]]["plants"][index]["Pmax"]
                    )
                    solver.Add(
                        plant >= nodes[nodeA["index"]]["plants"][index]["Pmin"]
                    )
                    index = index + 1
            if(strictMode):
                solver.Add(
                    sum(plantsInNodes[nodeA["index"]]["plants"]) - nodeA["demand"][time]*_globalDemand[0] - sum(neighbouringEdges)==0
                )
            else: 
                short = solver.NumVar(0, 1000, "Shortage")
                solver.Add(
                    sum(plantsInNodes[nodeA["index"]]["plants"]) - nodeA["demand"][time]*_globalDemand[0] - sum(neighbouringEdges) + short==0
                )
                shortage.append(short)
    periodOfTime.append(plantsInNodes)

def createMinimizeFunction(solver: pywraplp.Solver, periodOfTime):
    """
    Creates array of plants generation variables to minimize in solver. Should be run after all periodOfTime constraints are created

    ----ARGUMENTS----

    solver - solver which will be used

    periodOfTime - array containing all variables and constraints, grouped by cycle

    ----RETURNS----
    returns array of solver Variables to be optimized
    """
    sumOfGeneration = []
    for hour in periodOfTime:
        for node in hour :
            pindex = 0
            for plant in node["plants"]:
                sumOfGeneration.append(plant * node["plantCost"][pindex])
                pindex = pindex + 1
    return sumOfGeneration

def createMinimizeFunctionDemand(solver: pywraplp.Solver, periodOfTime, shortage):
    """
    Creates array of plants generation variables to minimize in solver with relaxed constraints when it comes to demand in nodes. Should be run after all periodOfTime constraints are created

    ----ARGUMENTS----

    solver - solver which will be used

    periodOfTime - array containing all variables and constraints, grouped by cycle
    
    shortage - array of solver variables representing shortage in each node

    ----RETURNS----
    returns array of solver Variables to be optimized
    """
    sumOfGeneration = []
    maxCost = 1
    for hour in periodOfTime:
        
        for node in hour :
            pindex = 0
            for plant in node["plants"]:
                if(int(node["plantCost"][pindex] or 1) > maxCost):
                    maxCost = node["plantCost"][pindex]
                sumOfGeneration.append(node["plantCost"][pindex]*plant)
                pindex = pindex + 1

    for short in shortage:
        sumOfGeneration.append((maxCost+1)*short)
    return sumOfGeneration

def createMinimizeFunctionBinary(solver: pywraplp.Solver, periodOfTime):
    """
    Test method for debugging purposes
    """
    sumOfGeneration = []
    for hour in periodOfTime:
        for node in hour :
            pindex = 0
         
            for plant in node["plants"]:
                cost = solver.NumVar(0, 10000, "testset")
                solver.Add(
                    cost == node["plantCost"][pindex] * plant
                )
                sumOfGeneration.append(cost)
                pindex = pindex + 1
    return sumOfGeneration


def exportNodesJSON( nodes, time, demand):
    """
    Exports  node and their data as JSON structure

    ----ARGUMENTS----

    nodes - list of all solver node variables

    time - cyclew for which data is exported

    demand - array of demand by cycle

    ----RETURNS----

    JSON structure of nodes
    """
    JSONNode = []
    index = 0
    for node in nodes:
        nodeObject = {
            "group": "nodes",
            "data": {
                "id": node["nodeName"],
                "type": "node",
                "demand": round(node["demand"][time] * demand[0],2)
            }
        }
        JSONNode.append(nodeObject)
    return JSONNode

def exportPlantsJSON(plantsInNodes, nodes, mode):
    """
    Exports  powerplants and their data as JSON structure

    ----ARGUMENTS----

    plantsInNodes - solver variables for powerplants, 
    nodes - list of all solver node variables

    mode - either binary, simple or complex

    ----RETURNS----

    JSON structure of powerplants
    """
    JSONPlants = []
    for node in nodes:
        pIndex = 0
        for plant in node["plants"]:
            plantObj = {
            "group": "nodes",
            "data": {
                "id": plant["blockName"],
                "parent": node["nodeName"],
                "type": "node",
                "value":  round(plantsInNodes[node["index"]]["plants"][pIndex].solution_value(),2),
                "isWorking": 1,
                }
            }
            if mode != "simple":
                if plantsInNodes[node["index"]]["isPlantWorking"][pIndex].solution_value() == 0:
                    plantObj["data"]["isWorking"] = 0
            pIndex +=1
            JSONPlants.append(plantObj)
    return JSONPlants



def exportEdgeJSON(edgeInNodes):
    """
    Exports edges and their data as JSON structure

    ----ARGUMENTS----

    edgeInNodes - solver variables for edges, 

    ----RETURNS----

    JSON structure of edges
    """
    validEdges = []
    JSONEdge = []
    index = 0
    for flow in edgeInNodes:
        for edge in flow:
            if edge != 0 :
                if isPresent(edgeInNodes, edge, validEdges) == False:
                    validEdges.append(edge)
    for edge in validEdges:
        edgeObject = {
            "group": "edges",
            "data": {
                "id": edge["nodeA"] + edge["nodeB"],
                "source": edge["nodeA"],
                "target": edge["nodeB"],
                "value": round(edge["var"].solution_value(),2),
                "percentage": round(abs(edge["var"].solution_value()/edge["capacity"])*100, 2)
                }
            }
        JSONEdge.append(edgeObject)
    return JSONEdge

def isPresent(edges, edgeToCheck, edgesToSearch):
    """
    checks whether specific edge is present in a group of edges

    """
    if len(edgesToSearch) == 0:
        return False
    for flow in edges:
        for edge in flow:
            if edge != 0:
                for ee in edgesToSearch:
                    name = ee["nodeA"] + ee["nodeB"]
                    targetName = edgeToCheck["nodeB"] + edgeToCheck["nodeA"]
                    if targetName == name:
                        return True          
    return False

