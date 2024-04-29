import copy as cp
import collections
import json
import operator
import os

class arch_generator:
    Contract_Dir = "./contracts/"
    Contract_List = os.listdir(Contract_Dir)

    MAX_NODES     = 6 #inclusive
    MAX_EDGES     = 9 #inclusive

    # maximal depth to go
    explore_depth = 5
    
    def count_edges(self, adj_mat):
        ec = 0
        for l in adj_mat:
            ec += sum(l)
        return ec
            
    def get_potential_edges(self, adj_mat):
        candidates = []
        for i in range( 0, len(adj_mat) ):
            for j in range(0, len( adj_mat[i] ) ):
                if j > i: # only count the upper triangle
                    if adj_mat[i][j] == 0:
                        candidates.append( (i, j) )
        return candidates

    def get_actions(self, net ):
        # the actions will result in a vast number of
        network = cp.deepcopy(net)
        actions =[]
        assert type(network) is type( collections.OrderedDict() )
        adj_mat   = network["adj_mat"]
        # adding a new node
        for i in range(len(self.Contract_List)):
            actions.append("node:"+str(self.Contract_List[i]))

        # mutate to the current graph by introducing an new edge
        edge_candidates = self.get_potential_edges(adj_mat)
        for e in edge_candidates:
            actions.append("edge:" + str(e) )
        # this will be a combination problem in python
        actions.append('term') # Terminal action
        return actions

    def get_next_network(self, net, action):
        # Input: net: a list
        # Output: a list
        network = cp.deepcopy(net)
        assert type(network) is type(collections.OrderedDict() )
        node_list = network["node_list"]
        adj_mat   = network["adj_mat"]
        node_c    = len(node_list)
        edge_c    = self.count_edges(adj_mat)
        if node_c > self.MAX_NODES:
            return None
        if edge_c > self.MAX_EDGES:
            return None
        if node_c == self.MAX_NODES and "node" in action:
            return None
        if edge_c == self.MAX_EDGES and "edge" in action:
            return None

        assert node_c <= self.MAX_NODES
        assert edge_c <= self.MAX_EDGES
        if 'edge' in action:
            node_list = network["node_list"]
            adj_mat   = network["adj_mat"]
            ridx = int(action[6])
            cidx = int(action[9])
            adj_mat[ridx][cidx] = 1
            network["adj_mat"]   = adj_mat
            network["node_list"] = node_list
            assert network["node_list"][0] == "input"
            assert network["node_list"][-1] == "output"
            assert type(network) is collections.OrderedDict
            return network
        elif 'node' in action:
            new_network = collections.OrderedDict()
            #wipe out all the existing edges
            node_type = action.split(":")[1]
            assert node_type in self.Contract_List
            new_node_list = cp.deepcopy(node_list)
            new_node_list.insert(len(new_node_list) - 1, node_type)
            nodes_c = len(new_node_list)
            new_adj_mat = []
            for i in range(0, nodes_c):
                new_adj_mat.append( [0] * nodes_c )
            new_network["adj_mat"]  = new_adj_mat
            new_network["node_list"] = new_node_list
            assert new_network["node_list"][0] == "input"
            assert new_network["node_list"][-1] == "output"
            assert type(new_network) is collections.OrderedDict
            return new_network
        elif 'term' in action:
            assert network["node_list"][0] == "input"
            assert network["node_list"][-1] == "output"
            new_node_list = cp.deepcopy(network["node_list"])
            new_node_list.append("term")
            network["node_list"] = new_node_list
            assert type(network) is collections.OrderedDict
            return network
        else:
            raise "action must contains either object edge or node"
        return state

class train_net:
    best_trace      = collections.OrderedDict()
    traing_mem      = collections.OrderedDict()
    training_trace  = collections.OrderedDict()
    target_str      = None
    best_accuracy   = 0
    counter         = 0

    def train_net(self, network):
        #this state has been cleaned from term
        network_str = json.dumps( network, sort_keys = True )
        assert network_str in self.traing_mem
        is_found = False
        acc = self.traing_mem[network_str]
        if network_str not in self.training_trace:
            self.training_trace[network_str] = acc
        self.counter += 1
        if acc > self.best_accuracy:
            print("@@@update best state:", network)
            print("@@@update best acc:", acc)
            self.best_accuracy = acc
            item = [acc, self.counter]
            self.best_trace[network_str] = item
            print("target str:", self.target_str)
        if self.counter % 1000 == 0:
            sorted_best_traces = sorted(self.best_trace.items(), key=operator.itemgetter(1))
            final_results = []
            for item in sorted_best_traces:
                final_results.append( item[1] )
            final_results_str = json.dumps(final_results)
            filename = "results/result_"+str(self.counter)
            with open(filename, "a") as f:
                f.write(final_results_str + '\n')

        return acc, is_found