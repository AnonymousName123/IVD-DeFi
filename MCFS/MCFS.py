import os
import json
import jsonlines
import math
import collections
import copy as cp
import shutil

import jsonpickle
import numpy as np
from MCFS.arch_generator import arch_generator
from MCFS.arch_generator import train_net
from collections import OrderedDict
from MCFS.pre_processing import Generate
from MCFS.post_processing import Output
from match import FindSim

seqs = []

class Node:
    def __init__(self, state=None, x_bar=0, n=0, parent_str=None):
        assert state is not None
        assert parent_str is not None
        assert type(parent_str) is str
        assert type(state) is collections.OrderedDict

        self.x_bar = x_bar
        self.n = n
        self.parent_str = parent_str
        self.state = state

    def get_state(self):
        return self.state

    def get_xbar(self):
        return self.x_bar

    def get_n(self):
        return self.n

    def set_xbar(self, xb):
        self.x_bar = xb

    def set_n(self, n):
        self.n = n

    def get_json(self):
        return json.dumps(self.state, sort_keys=True)

    def get_parent(self):
        return self.parent_str

class MCTS:
    nodes = collections.OrderedDict()  # actual MCTS tree
    dangling_nodes = collections.OrderedDict()  # this is to track the actually trained tree in random rollouts

    S = None
    Cp = 2
    arch_gen = None
    net_trainer = None

    def __init__(self):
        self.arch_gen = arch_generator()
        self.net_trainer = train_net()
        self.trained_networks = {}
        self.simulated_networks = {}

        self.reset_to_root()

    def loads_all_states(self, truth_table_path):
        """
        node_path = 'nodes'
        if os.path.isfile(node_path) == True:
            with open(node_path, 'r') as json_data:
                self.nodes = jsonpickle.decode(json.load(json_data, object_pairs_hook=OrderedDict))
        print("=>LOAD", len(self.nodes), " MCTS nodes")

        dangling_nodes_path = 'dangling_nodes'
        if os.path.isfile(dangling_nodes_path) == True:
            with open(dangling_nodes_path, 'r') as json_data:
                self.dangling_nodes = jsonpickle.decode(json.load(json_data, object_pairs_hook=OrderedDict))
        print("=>LOAD", len(self.dangling_nodes), " dangling nodes")
        """

        # LOAD TRUTH TABLE
        with open('./MCFS/Input/' + truth_table_path, 'r') as json_data:
            self.net_trainer.traing_mem = json.load(json_data, object_pairs_hook=OrderedDict)
        print("=>LOAD", len(self.net_trainer.traing_mem), " truth table entries")


    def create_new_node(self, new_state=None, parent=None):
        # Expansion function
        # creating a regular node in a tree,
        # parent cannot be None, also the new node
        assert parent is not None
        assert new_state is not None

        new_state_str = json.dumps(new_state, sort_keys=True)

        parent_str = ""
        if parent != "ROOT":
            parent_str = json.dumps(parent, sort_keys=True)
            assert parent_str in self.nodes
        else:
            parent_str = "ROOT"

        # there are two possibilities:
        # the new node is a previous dangling node
        # the node is brand new
        xbar = 0
        # TODO once finish the actions
        xbar = self.evaluate(new_state, 2)
        assert xbar >= 0
        n = 1
        new_node = Node(new_state, xbar, n, parent_str)
        self.nodes[new_node.get_json()] = new_node

        if new_state_str in self.dangling_nodes:
            del self.dangling_nodes[new_state_str]

        return xbar

    def reset_to_root(self):
        # input->output is the ROOT
        network = collections.OrderedDict({"adj_mat": [[0, 0], [0, 0]], "node_list": ["input", "output"]})
        self.S = network
        state_str = self.get_state_str()
        if state_str not in list(self.nodes.keys()):
            self.create_new_node(self.S, "ROOT")  # state as a list is given

        assert state_str in list(self.nodes.keys())

    def get_state_str(self):
        return json.dumps(self.S, sort_keys=True)

    def get_state(self):
        return cp.deepcopy(self.S)

    def is_in_tree(self, state_str):
        assert type(state_str) is str
        if state_str not in self.nodes:
            return False
        return True

    def UCT(self, next_state):
        next_state_str = json.dumps(next_state, sort_keys=True)
        if next_state == None:
            # discourage the None nodes
            return 0
        else:
            if next_state_str not in self.nodes:
                # next state is a new node
                return float("inf")
            else:
                # next state is an existing node
                state_str = self.get_state_str()
                return self.nodes[next_state_str].get_xbar() + 2 * self.Cp * math.sqrt(
                    2 * math.log(self.nodes[state_str].get_n()) / self.nodes[next_state_str].get_n())

    def get_actions(self):
        # get legal actions
        return self.arch_gen.get_actions(self.get_state())

    def simulation(self, starting_net):
        # Input:  state (as a list)
        # Output: state (as a list). If the NN failed the model checking, return None.
        current_state = cp.deepcopy(starting_net)
        if current_state["node_list"][-1] == 'term':
            # If the current state is a terminal then return itself.
            return current_state
        counter = 0
        while True:
            rand_action = np.random.choice(self.arch_gen.get_actions(current_state))
            next_rand_net = self.arch_gen.get_next_network(current_state, rand_action)
            if next_rand_net == None:  # next_rand_net is None if it failed the model.
                current_state = starting_net
                continue

            if rand_action == 'term':
                trainable_str = json.dumps(self.clean_term_network(next_rand_net), sort_keys=True)
                
                if trainable_str in self.net_trainer.traing_mem:
                    return next_rand_net
                else:
                    # reset
                    current_state = starting_net
                    counter += 1
                    if counter > 1000:
                        return None
                    else:
                        continue

            current_state = next_rand_net

    def evaluate_terminal(self, terminal_node, rollout_from_str=None):
        # Input: state (as a list)
        # Output: accuracy
        # TODO: in net_training, we will implement a trainning memory to track every trained networks, and their accuracies.
        term_state_str = json.dumps(terminal_node, sort_keys=True)
        assert terminal_node is not None
        assert terminal_node["node_list"][-1] is 'term'

        if rollout_from_str is None:
            # this is a regular terminal node in MCTS,
            # no need to put it into dangling nodes
            nn = self.clean_term_network(terminal_node)
            nn_str = json.dumps(nn, sort_keys=True)
            if nn_str in self.net_trainer.traing_mem:
                acc, is_found = self.net_trainer.train_net(nn)
                self.trained_networks[json.dumps(nn, sort_keys=True)] = acc
                return acc
            else:
                return 0
        else:
            assert type(rollout_from_str) is str
            # this is a dangling node in MCTS rollout, at least, for that particular moment
            nn = self.clean_term_network(terminal_node)
            acc, is_found = self.net_trainer.train_net(nn)
            self.trained_networks[json.dumps(nn, sort_keys=True)] = acc
            if term_state_str not in self.dangling_nodes:
                self.dangling_nodes[term_state_str] = Node(terminal_node, acc, 0, rollout_from_str)
            return acc

    def clean_term_network(self, network):
        adj_mat = cp.deepcopy(network["adj_mat"])
        node_list = cp.deepcopy(network["node_list"])
        node_list.pop()
        new_network = collections.OrderedDict()
        new_network["adj_mat"] = adj_mat
        new_network["node_list"] = node_list
        return new_network

    def evaluate(self, starting_net, num_dyna_sim=0):
        assert starting_net is not None

        ############################
        # condition1: evaluating the terminal node
        if starting_net["node_list"][-1] == 'term':
            # If the starting_net is a terminal node, then we evaluate the terminal.
            return self.evaluate_terminal(starting_net, None)

        ############################
        # condition2: conducting random rollouts
        terminal_node = self.simulation(starting_net)

        ############################
        ### using true accuracy  ###
        ############################
        if terminal_node == None:
            return 0.1
        else:
            acc = self.evaluate_terminal(terminal_node, json.dumps(starting_net, sort_keys=True))
        return acc


    def set_state(self, state):
        self.S = cp.deepcopy(state)

    def backpropagate(self, state, sim_result):
        cur_state = cp.deepcopy(state)
        curt_state_str = json.dumps(cur_state, sort_keys=True)
        i = 0
        while True:
            i = i + 1
            assert curt_state_str in self.nodes
            parent_str = self.nodes[curt_state_str].get_parent()  # 0: parent, 1: accuracy
            assert curt_state_str is not parent_str
            if parent_str == "ROOT":
                break
            assert parent_str in self.nodes
            self.nodes[parent_str].set_n(self.nodes[parent_str].get_n() + 1)  # self.N[ parent_str ] += 1
            new_xbar = float(1 / self.nodes[parent_str].get_n()) * float(sim_result) + float(
                self.nodes[parent_str].get_n() - 1) / float(self.nodes[parent_str].get_n()) * self.nodes[parent_str].get_xbar()
            self.nodes[parent_str].set_xbar(new_xbar)
            curt_state_str = parent_str

    def search(self):
        episode = 0
        step = 0
        epoch = 20
        for i in range(0, epoch):

            print("episode:", episode, " step:", step)
            actions = self.get_actions()
            UCT = [0] * len(actions)
            for idx in range(0, len(actions)):
                act = actions[idx]
                next_net = self.arch_gen.get_next_network(self.get_state(), act)
                UCT[idx] = self.UCT(next_net)
            # the UCT = 0 if next_net is None, which is the case when the depth of network exceed the predefined explorable depth.
            best_action = actions[np.random.choice(np.argwhere(UCT == np.amax(UCT)).reshape(-1), 1)[0]]
            next_net = self.arch_gen.get_next_network(self.get_state(), best_action)
            next_net_str = json.dumps(next_net, sort_keys=True)
            curt_state_str = self.get_state_str()
            if 'node' in best_action:
                print("Next Call:", best_action[5:])
            _, val = next_net.values()
            print("Sequence:", val[1:-1])
            if val[-1] == 'term':
                val = val[:-1]
            val = val[1:-1]
            # if len(val) >= 2 and val not in seqs and i > epoch - 1:
            if len(val) >= 2 and val not in seqs:
                seqs.append(val)

            # back-propagate on 3 conditions:
            # 1. exceed the max exploratory depth---back-propogate 0
            # 2. terminal---train the network
            # 3. new node---evaluate the node
            # the tree exceed the explorable depth
            if next_net is None:
                assert curt_state_str in self.nodes
                self.backpropagate(self.get_state(), 0.0)
                self.reset_to_root()
                episode += 1
                step = 0
            else:
                # create a new node
                if not self.is_in_tree(next_net_str):
                    new_node_xbar = self.create_new_node(next_net, self.get_state())
                    if new_node_xbar > 0:
                        self.backpropagate(next_net, new_node_xbar)
                    self.reset_to_root()
                    episode += 1
                    step = 0
                else:
                    # an existing node in tree
                    # double check the network length is within the range
                    if best_action == 'term':
                        # If the agent reaches the terminal state go back to the root.
                        # we shall only back-propogate on legitimate nodes
                        assert next_net_str in self.nodes
                        acc = self.nodes[next_net_str].get_xbar()
                        self.nodes[next_net_str].set_n(self.nodes[next_net_str].get_n() + 1)
                        self.backpropagate(next_net, acc)
                        self.reset_to_root()
                        episode += 1
                        step = 0
                    else:
                        if len(next_net) > self.arch_gen.explore_depth:
                            assert len(next_net) <= self.arch_gen.explore_depth
                        # step into the next state
                        self.set_state(next_net)
                        step += 1
            if step > 1000:
                self.reset_to_root()


def MCFS():

    # tree = open('./data/Tree.txt')
    # data = tree.readlines()
    # tree.close()

    flag = False
    if flag:
        Generate()
        Input_List = os.listdir('./MCFS/Input/')
        for file in Input_List:
            agent = MCTS()
            agent.loads_all_states(file)
            if len(agent.net_trainer.traing_mem) > 20:
                agent.search()
        Output(seqs)
    else:
        shutil.copy2('./data/aggre-info.json', './data/aggre-info-opt.json')
        print("All sequences retained")

        # with jsonlines.open('../data/aggre-info.json', 'r') as source_file:
        #     for seq in source_file:
        #         print(seq)
        #     data = json.load(source_file)

        # with open('../data/aggre-info-opt.json', 'w') as destination_file:
        #     json.dump(data, destination_file)