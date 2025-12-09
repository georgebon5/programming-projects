# multiAgents.py
# --
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


from util import manhattanDistance
from game import Directions
import random, util

from game import Agent
from pacman import GameState

class ReflexAgent(Agent):
    """
    A reflex agent chooses an action at each choice point by examining
    its alternatives via a state evaluation function.

    The code below is provided as a guide.  You are welcome to change
    it in any way you see fit, so long as you don't touch our method
    headers.
    """


    def getAction(self, gameState: GameState):
        """
        You do not need to change this method, but you're welcome to.

        getAction chooses among the best options according to the evaluation function.

        Just like in the previous project, getAction takes a GameState and returns
        some Directions.X for some X in the set {NORTH, SOUTH, WEST, EAST, STOP}
        """
        # Collect legal moves and successor states
        legalMoves = gameState.getLegalActions()

        # Choose one of the best actions
        scores = [self.evaluationFunction(gameState, action) for action in legalMoves]
        bestScore = max(scores)
        bestIndices = [index for index in range(len(scores)) if scores[index] == bestScore]
        chosenIndex = random.choice(bestIndices) # Pick randomly among the best

        "Add more of your code here if you want to"

        return legalMoves[chosenIndex]

    def evaluationFunction(self, currentGameState: GameState, action):
        """
        Design a better evaluation function here.

        The evaluation function takes in the current and proposed successor
        GameStates (pacman.py) and returns a number, where higher numbers are better.

        The code below extracts some useful information from the state, like the
        remaining food (newFood) and Pacman position after moving (newPos).
        newScaredTimes holds the number of moves that each ghost will remain
        scared because of Pacman having eaten a power pellet.

        Print out these variables to see what you're getting, then combine them
        to create a masterful evaluation function.
        """

        # Δημιουργία επόμενης κατάστασης
        successor = currentGameState.generatePacmanSuccessor(action)
        pacmanPos = successor.getPacmanPosition()
        foodGrid = successor.getFood()
        ghostStates = successor.getGhostStates()
        scaredTimers = [g.scaredTimer for g in ghostStates]
        capsules = successor.getCapsules()

        # Ξεκινάμε από τη βασική βαθμολογία του παιχνιδιού
        totalScore = successor.getScore()


        # Κοντινό φαγητό — μικρότερη απόσταση σημαίνει καλύτερη επιλογή
        foodList = foodGrid.asList()
        if foodList:
            closestFood = min(manhattanDistance(pacmanPos, f) for f in foodList)
            # Χρησιμοποιούμε 1/(1+d) σύμφωνα με τις ευρετικές των διαφανειών
            totalScore += 2.0 / (1 + closestFood)
        # Αν έφαγε φαγητό, δώσε έξτρα ανταμοιβή
        if successor.getNumFood() < currentGameState.getNumFood():
            totalScore += 12

        # (2) Φαντάσματα — αποφυγή ενεργών, κυνηγητό scared
        for ghost, scaredTime in zip(ghostStates, scaredTimers):
            gPos = ghost.getPosition()
            dist = manhattanDistance(pacmanPos, gPos)

            if scaredTime > 0:
                # Αν είναι scared, πλησίασέ το ελεγχόμενα
                totalScore += 3 / (1 + dist)
                if dist == 0:  # Πιάστηκε
                    totalScore += 30
            else:
                # Ενεργό φάντασμα => μείνε μακριά
                if dist <= 1:
                    totalScore -= 8
                else:
                    totalScore -= 1 / dist

        #Capsules — επιδίωξέ τις αν υπάρχουν κοντά φαντάσματα
        if capsules:
            closestCap = min(manhattanDistance(pacmanPos, c) for c in capsules)
            ghostTooClose = any(
                s == 0 and manhattanDistance(pacmanPos, g.getPosition()) <= 2
                for g, s in zip(ghostStates, scaredTimers)
            )
            # Αν υπάρχουν φαντάσματα κοντά, αύξησε το βάρος της κάψουλας
            weight = 2.5 if ghostTooClose else 1.2
            totalScore += weight / (1 + closestCap)


        # (4) Αποφυγή ακινησίας — δεν κερδίζεις μένοντας στάσιμος
        from game import Directions
        if action == Directions.STOP:
            totalScore -= 6

        # Επιστρέφει το τελικό σκορ για αυτήν την ενέργεια
        return totalScore

def scoreEvaluationFunction(currentGameState: GameState):
    """
    This default evaluation function just returns the score of the state.
    The score is the same one displayed in the Pacman GUI.

    This evaluation function is meant for use with adversarial search agents
    (not reflex agents).
    """
    return currentGameState.getScore()

class MultiAgentSearchAgent(Agent):
    """
    This class provides some common elements to all of your
    multi-agent searchers.  Any methods defined here will be available
    to the MinimaxPacmanAgent, AlphaBetaPacmanAgent & ExpectimaxPacmanAgent.

    You *do not* need to make any changes here, but you can if you want to
    add functionality to all your adversarial search agents.  Please do not
    remove anything, however.

    Note: this is an abstract class: one that should not be instantiated.  It's
    only partially specified, and designed to be extended.  Agent (game.py)
    is another abstract class.
    """

    def __init__(self, evalFn = 'scoreEvaluationFunction', depth = '2'):
        self.index = 0 # Pacman is always agent index 0
        self.evaluationFunction = util.lookup(evalFn, globals())
        self.depth = int(depth)

class MinimaxAgent(MultiAgentSearchAgent):
    """
    Your minimax agent (question 2)
    """

    def getAction(self, gameState: GameState):
        """
        Returns the minimax action from the current gameState using self.depth
        and self.evaluationFunction.

        Here are some method calls that might be useful when implementing minimax.

        gameState.getLegalActions(agentIndex):
        Returns a list of legal actions for an agent
        agentIndex=0 means Pacman, ghosts are >= 1

        gameState.generateSuccessor(agentIndex, action):
        Returns the successor game state after an agent takes an action

        gameState.getNumAgents():
        Returns the total number of agents in the game

        gameState.isWin():
        Returns whether or not the game state is a winning state

        gameState.isLose():
        Returns whether or not the game state is a losing state
        """
        # Βοηθητική συνάρτηση για αναδρομικό υπολογισμό Minimax
        def minimax(state, depth, agentIndex):
            # Έλεγχοι τερματισμού: νίκη, ήττα ή βάθος μηδέν
            if depth == 0 or state.isWin() or state.isLose():
                return self.evaluationFunction(state)

            numAgents = state.getNumAgents()

            # Εναλλαγή Pacman (MAX) / Ghosts (MIN)
            if agentIndex == 0:
                #MAX (Pacman)
                bestValue = float("-inf")
                for action in state.getLegalActions(agentIndex):
                    successor = state.generateSuccessor(agentIndex, action)
                    value = minimax(successor, depth, 1)  # Πάμε στον πρώτο ghost
                    bestValue = max(bestValue, value)
                return bestValue

            else:
                #MIN (Ghosts)
                nextAgent = agentIndex + 1
                # Αν έχουμε περάσει όλους τους agents, αυξάνουμε βάθος και επιστρέφουμε σε Pacman
                if nextAgent == numAgents:
                    nextAgent = 0
                    depth -= 1

                bestValue = float("inf")
                for action in state.getLegalActions(agentIndex):
                    successor = state.generateSuccessor(agentIndex, action)
                    value = minimax(successor, depth, nextAgent)
                    bestValue = min(bestValue, value)
                return bestValue

        # Επιλογή βέλτιστης ενέργειας για Pacman (MAX root)
        bestScore = float("-inf")
        chosenAction = None

        for action in gameState.getLegalActions(0):
            successor = gameState.generateSuccessor(0, action)
            value = minimax(successor, self.depth, 1)
            if value > bestScore:
                bestScore = value
                chosenAction = action

        return chosenAction

class AlphaBetaAgent(MultiAgentSearchAgent):
    """
    Your minimax agent with alpha-beta pruning (question 3)
    """

    def getAction(self, gameState: GameState):
        """
        Returns the minimax action using self.depth and self.evaluationFunction
        """
        # Αναδρομική συνάρτηση Minimax με Alpha–Beta περιορισμό
         
        def alphabeta(state, depth, agentIndex, alpha, beta):
    #  Terminal state check 
            if depth == 0 or state.isWin() or state.isLose():
                return self.evaluationFunction(state)

            numAgents = state.getNumAgents()

            # Pacman (MAX)
            if agentIndex == 0:
                value = float("-inf")
                for action in state.getLegalActions(agentIndex):
                    successor = state.generateSuccessor(agentIndex, action)
                    value = max(value, alphabeta(successor, depth, 1, alpha, beta))
                    alpha = max(alpha, value)
                    if alpha > beta:
                        break
                return value

            # Ghosts (MIN)
            else:
                value = float("inf")
                nextAgent = agentIndex + 1
                # Μείωσε το βάθος ΜΟΝΟ όταν τελειώσουν όλοι οι agents
                if nextAgent == numAgents:
                    nextAgent = 0
                    depth -= 1

                for action in state.getLegalActions(agentIndex):
                    successor = state.generateSuccessor(agentIndex, action)
                    value = min(value, alphabeta(successor, depth, nextAgent, alpha, beta))
                    beta = min(beta, value)
                    if alpha > beta:
                        break
                return value

        
        # Root call: Pacman
        alpha, beta = float("-inf"), float("inf")
        bestAction = None
        bestValue = float("-inf")

        for action in gameState.getLegalActions(0):
            successor = gameState.generateSuccessor(0, action)
            value = alphabeta(successor, self.depth, 1, alpha, beta)
            if value > bestValue:
                bestValue = value
                bestAction = action
            alpha = max(alpha, bestValue)

        return bestAction

class ExpectimaxAgent(MultiAgentSearchAgent):
    """
      Your expectimax agent (question 4)
    """

    def getAction(self, gameState: GameState):
        """
        Returns the expectimax action using self.depth and self.evaluationFunction

        All ghosts should be modeled as choosing uniformly at random from their
        legal moves.
        """
        def expectimax(state, depth, agentIndex):
            #Τερματισμός αναδρομής 
            if depth == 0 or state.isWin() or state.isLose():
                return self.evaluationFunction(state)

            numAgents = state.getNumAgents()

            #Pacman – MAX layer
            if agentIndex == 0:
                bestValue = float("-inf")
                for action in state.getLegalActions(agentIndex):
                    successor = state.generateSuccessor(agentIndex, action)
                    val = expectimax(successor, depth, 1)
                    bestValue = max(bestValue, val)
                return bestValue

            #Ghosts – EXPECTATION layer
           
            else:
                actions = state.getLegalActions(agentIndex)
                if not actions:
                    return self.evaluationFunction(state)

                # Επόμενος agent και βάθος
                nextAgent = agentIndex + 1
                nextDepth = depth
                if nextAgent == numAgents:
                    nextAgent = 0
                    nextDepth -= 1

                # Ομοιόμορφη πιθανότητα επιλογής κάθε ενέργειας
                prob = 1.0 / len(actions)
                expectedValue = 0.0

                for action in actions:
                    successor = state.generateSuccessor(agentIndex, action)
                    val = expectimax(successor, nextDepth, nextAgent)
                    expectedValue += prob * val

                return expectedValue

        bestAction = None
        bestValue = float("-inf")

        for action in gameState.getLegalActions(0):
            successor = gameState.generateSuccessor(0, action)
            val = expectimax(successor, self.depth, 1)
            if val > bestValue:
                bestValue = val
                bestAction = action

        return bestAction

def betterEvaluationFunction(currentGameState: GameState):
    """
    Your extreme ghost-hunting, pellet-nabbing, food-gobbling, unstoppable
    evaluation function (question 5).

    DESCRIPTION: <write something here so we know what you did>
    """
    #Πληροφορίες από το state 
    pos = currentGameState.getPacmanPosition()
    food = currentGameState.getFood()
    ghostStates = currentGameState.getGhostStates()
    scaredTimes = [g.scaredTimer for g in ghostStates]
    capsules = currentGameState.getCapsules()
    score = currentGameState.getScore()

    # Αν ο Pacman έχει χάσει
    if currentGameState.isLose():
        return float("-inf")

    # Αν έχει κερδίσει
    if currentGameState.isWin():
        return float("inf")

    #Απόσταση από το φαγητό
    foodList = food.asList()
    if foodList:
        closestFood = min(manhattanDistance(pos, f) for f in foodList)
    else:
        closestFood = 0

    # Θέλουμε να πλησιάζουμε το φαγητό μικρότερη απόσταση = μεγαλύτερη τιμή
    foodScore = 20.0 / (1 + closestFood)

    #Απόσταση από φαντάσματα 
    ghostPenalty = 0.0
    scaredBonus = 0.0

    for ghost, t in zip(ghostStates, scaredTimes):
        d = manhattanDistance(pos, ghost.getPosition())

        # Αν το φάντασμα είναι φοβισμένο μπορεί να το κυνηγήσει
        if t > 0:
            scaredBonus += 10.0 / (1 + d)
        else:
            # Αν είναι πολύ κοντά
            if d <= 1:
                ghostPenalty -= 200
            else:
                ghostPenalty -= 1.0 / (1 + d)

    #Απόσταση από κάψουλες (Power Pellets) 
    capsuleScore = 0.0
    if capsules:
        minCapDist = min(manhattanDistance(pos, c) for c in capsules)
        capsuleScore = 10.0 / (1 + minCapDist)

    foodLeft = len(foodList)
    foodLeftBonus = -3.0 * foodLeft

    #Συνδυασμός όλων των παραγόντων 
    # Σκορ = βασικό + μπόνους τροφής + μπόνους κάψουλας + bonus/fear από φαντάσματα
    finalScore = (
        score
        + foodScore
        + scaredBonus
        + capsuleScore
        + ghostPenalty
    )

    return finalScore

# Abbreviation
better = betterEvaluationFunction
