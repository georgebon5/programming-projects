# search.py
# ---------
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


"""
In search.py, you will implement generic search algorithms which are called by
Pacman agents (in searchAgents.py).
"""

import util
from util import Stack, Queue, PriorityQueue


class SearchProblem:
    """
    This class outlines the structure of a search problem, but doesn't implement
    any of the methods (in object-oriented terminology: an abstract class).

    You do not need to change anything in this class, ever.
    """

    def getStartState(self):
        """
        Returns the start state for the search problem.
        """
        util.raiseNotDefined()

    def isGoalState(self, state):
        """
          state: Search state

        Returns True if and only if the state is a valid goal state.
        """
        util.raiseNotDefined()

    def getSuccessors(self, state):
        """
          state: Search state

        For a given state, this should return a
        list of triples, (successor,
        action, stepCost), where 'successor' is a successor to the current
        state, 'action' is the action required to get there, and 'stepCost' is
        the incremental cost of expanding to that successor.
        """
        util.raiseNotDefined()

    def getCostOfpath(self, path):
        """
        actions: A list of actions to take

        This method returns the total cost of a particular sequence of actions.
        The sequence must be composed of legal moves.
        """
        util.raiseNotDefined()


def tinyMazeSearch(problem):
    """
    Returns a sequence of moves that solves tinyMaze.  For any other maze, the
    sequence of moves will be incorrect, so only use this for tinyMaze.
    """
    from game import Directions
    s = Directions.SOUTH
    w = Directions.WEST
    return  [s, s, w, s, w, w, s, w]


def depthFirstSearch(problem):
    """
    Search the deepest nodes in the search tree first.
    Implements DFS using a Stack and avoids revisiting nodes.
    """
    # Αρχικοποίηση
    stack = Stack()
    visited = set()

    # Ξεκινάμε από την αρχική κατάσταση χωρίς ενέργειες
    stack.push((problem.getStartState(), []))

    while not stack.isEmpty():
        state, path = stack.pop()

        # Αν έχουμε ήδη επισκεφτεί αυτό το state, το αγνοούμε
        if state in visited:
            continue

        # Μαρκάρουμε οποια εχουν επισκεφθει
        visited.add(state)

        # Αν το state είναι στόχος, επιστρέφουμε τη διαδρομή
        if problem.isGoalState(state):
            return path

       # Εξερευνούμε τους διαδόχους (successors)
        for successor, action, cost in problem.getSuccessors(state):
            if successor not in visited:
                stack.push((successor, path + [action]))

    # Αν δεν βρεθεί λύση, επιστρέφουμε κενή λίστα
    return []


def breadthFirstSearch(problem):
    """
    Search the shallowest nodes in the search tree first.
    Implements BFS using a Queue and avoids revisiting nodes.
    """
   
    visited = set()
    queue = Queue()

    # Ξεκιναμε απο την αρχικη κατασταση
    queue.push((problem.getStartState(), []))
    visited.add(problem.getStartState())

    while not queue.isEmpty():
        state, path = queue.pop()

        # Αν βρεθηκε τοτε επιστρεφω την διαδρομη
        if problem.isGoalState(state):
            return path

        # Εξερευνούμε τους γείτονες
        for successor, action, cost in problem.getSuccessors(state):
            if successor not in visited:
                visited.add(successor)
                queue.push((successor, path + [action]))

    # Αν δεν βρεθεί λύση
    return []




def uniformCostSearch(problem):
    """
    Search the node of least total cost first (Uniform Cost Search).
    """


    from util import PriorityQueue  # <- αυτό πρέπει να είναι με εσοχή




    frontier = PriorityQueue()  # ουρά προτεραιότητας με βάση το συνολικό κόστος
    explored_costs = {}         # αποθήκευση ελάχιστου κόστους για κάθε state

    start_state = problem.getStartState()
    frontier.push((start_state, [], 0), 0)
    explored_costs[start_state] = 0

    while not frontier.isEmpty():
        current_state, path_so_far, path_cost = frontier.pop()

        
        if problem.isGoalState(current_state):
            return path_so_far

        # Αν έχουμε ήδη βρει μικρότερο κόστος, το αγνοούμε
        if path_cost > explored_costs.get(current_state, float("inf")):
            continue

        # Επέκταση successors
        for next_state, action, step_cost in problem.getSuccessors(current_state):
            new_cost = path_cost + step_cost

            # Αν δεν έχει επισκεφθεί ή βρέθηκε φθηνότερη διαδρομή
            if new_cost < explored_costs.get(next_state, float("inf")):
                explored_costs[next_state] = new_cost
                new_path = path_so_far + [action]
                frontier.push((next_state, new_path, new_cost), new_cost)

    return []




def nullHeuristic(state, problem=None):
    """
    A heuristic function estimates the cost from the current state to the nearest
    goal in the provided SearchProblem.  This heuristic is trivial.
    """
    return 0

from util import PriorityQueue

def aStarSearch(problem, heuristic=nullHeuristic):
    """
    Search the node that has the lowest combined cost and heuristic first.
    f(n) = g(n) + h(n)
    """
    pq = PriorityQueue()
    visited = set()

    start_state = problem.getStartState()
    pq.push((start_state, [], 0), heuristic(start_state, problem))

    while not pq.isEmpty():
        state, path, cost_so_far = pq.pop()

        # Αν φτάσαμε στον στόχο, επιστρέφουμε τη λύση
        if problem.isGoalState(state):
            return path

        # Αν το state ειναι ηδη φιξαρισμενο τοτε το προσπερνάμε
        if state in visited:
            continue
        visited.add(state)

        # κανω διασχιση
        for successor, action, step_cost in problem.getSuccessors(state):
            if successor not in visited:
                ncost = cost_so_far + step_cost
                priority = ncost + heuristic(successor, problem)
                pq.push((successor, path + [action], ncost), priority)

    return []



# Abbreviations
bfs = breadthFirstSearch
dfs = depthFirstSearch
astar = aStarSearch
ucs = uniformCostSearch
