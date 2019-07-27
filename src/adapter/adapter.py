import argparse
import os
import yaml
import logging

from yaml_writer.writer import create_template, create_source_file
from yaml_reader.results_reader import get_placement_and_schedule
from siminterface.simulator import Simulator
from bjointsp.main import place as bjointsp_place
from spinterface.spinterface import SimulatorAction

log = logging.getLogger(__name__)

BJOINTSP_FIRST_SRC_LOCATION = "res/sources/first_source.yaml"


def get_ingress_nodes_and_cap(network):
    ing_nodes = []
    node_cap = 0
    for node in network.nodes(data=True):
        if node[1]["type"] == "Ingress":
            ing_nodes.append(node[0])
        if node[1]['cap'] > node_cap:
            node_cap = node[1]['cap']

    return ing_nodes, node_cap


def parse_args():
    parser = argparse.ArgumentParser(description="BJointSP Adapter")
    parser.add_argument('-i', '--iterations', required=False, default=10, dest="iterations", type=int)
    parser.add_argument('-s', '--seed', required=False, default=9999, dest="seed", type=int)
    parser.add_argument('-n', '--network', required=True, dest='network')
    parser.add_argument('-sf', '--service_functions', required=True, dest="service_functions")
    parser.add_argument('-c', '--config', required=True, dest="config")
    return parser.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("coordsim").setLevel(logging.WARNING)
    logging.getLogger("bjointsp").setLevel(logging.WARNING)
    # creating the simulator
    simulator = Simulator()
    # initializing the simulator with absolute paths to the network, service_functions and the config. files.
    init_state = simulator.init(os.path.abspath(args.network),
                                os.path.abspath(args.service_functions),
                                os.path.abspath(args.config), args.seed)
    log.info("Network Stats after init(): %s", init_state.network_stats)
    # assuming for now that there is only one SFC.
    sfc_name = list(init_state.sfcs.keys())[0]
    sf_list = list(init_state.sfcs.get(sfc_name))
    sf_delays_dict = init_state.service_functions
    nodes_list = [node['id'] for node in init_state.network.get('nodes')]
    ingress_nodes, node_cap = get_ingress_nodes_and_cap(simulator.network)
    # The template file is fixed, so it is created just once and used throughout for the 'place' fx of BJointSP
    template = create_template(sfc_name, sf_list, sf_delays_dict)

    # Since after the init() call to Simulator we don't get any traffic info back
    # we can't create the source file needed for 'place' function of BJointSP,
    # So we for just the first 'place' call to BJointSP create a source file with just one ingress node having *
    # *vnf_source as the vnf in it and date_rate of 1 for just one flow f1
    with open(BJOINTSP_FIRST_SRC_LOCATION, "w") as f:
        source_list = []
        for i in range(len(ingress_nodes)):
            source_list.append({'node': ingress_nodes[i], 'vnf': "vnf_source", 'flows': [{"id": "f" + str(i+1),
                                                                                          "data_rate": 1},
                                                                                         {"id": "f" + str(i + 2),
                                                                                          "data_rate": 3},
                                                                                         {"id": "f" + str(i + 3),
                                                                                          "data_rate": 10}
                                                                                         ]})
        yaml.safe_dump(source_list, f, default_flow_style=False)

    # Since the simulator right now does ot have any link_dr , we are using a high value = 1000 for now.

    first_result = bjointsp_place(os.path.abspath(args.network),
                                  os.path.abspath(template),
                                  os.path.abspath(BJOINTSP_FIRST_SRC_LOCATION), cpu=node_cap, mem=node_cap, dr=1000)

    # creating the schedule and placement for the simulator from the result file that BJointSP returns.
    placement, schedule = get_placement_and_schedule(os.path.abspath(first_result), nodes_list, sfc_name, sf_list)
    with open(args.config, "r") as f:
        conf = yaml.load(f, yaml.SafeLoader)
        flow_dr_mean = conf.get('flow_dr_mean')
    # We run the simulator iterations number of times to get the Traffic info from the SimulatorAction object
    # We generate new source file for the BJointSP from the traffic info we get from the simulator for each iteration
    # Using this source file and the already generated Tempelate file we call the 'place' fx of BJointSP
    for i in range(args.iterations):
        action = SimulatorAction(placement, schedule)
        apply_state = simulator.apply(action)
        log.info("Network Stats after apply() # %s: %s", i + 1, apply_state.network_stats)
        source = create_source_file(apply_state.traffic, sf_list, sfc_name, flow_dr_mean)
        result = bjointsp_place(os.path.abspath(args.network, ),
                                os.path.abspath(template),
                                os.path.abspath(source), cpu=node_cap, mem=node_cap, dr=1000)
        placement, schedule = get_placement_and_schedule(os.path.abspath(result), nodes_list, sfc_name, sf_list)


if __name__ == '__main__':
    main()
