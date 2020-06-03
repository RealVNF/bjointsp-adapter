import argparse
import logging
import os
import random
from datetime import datetime
from pathlib import Path
import yaml
from bjointsp.main import place as bjointsp_place
from common.common_functionalities import create_input_file
from siminterface.simulator import Simulator
from spinterface.spinterface import SimulatorAction
from tqdm import tqdm
from util.reader import get_placement_and_schedule
from util.writer import create_template, create_source_object, copy_input_files

log = logging.getLogger(__name__)

FIRST_SRC_PATH = "res/sources"
DATETIME = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
PROJECT_ROOT = str(Path(__file__).parent.parent.parent)


def get_ingress_nodes_and_cap(network):
    """
    Gets a NetworkX DiGraph and returns a list of ingress nodes in the network and the largest capacity of nodes
    Parameters:
        network: NetworkX Digraph
    Returns:
        ing_nodes : a list of Ingress nodes in the Network
        node_cap : the single largest capacity of all the nodes of the network
    """
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
    parser.add_argument('-s', '--seed', required=False, dest="seed", type=int)
    parser.add_argument('-n', '--network', required=True, dest='network')
    parser.add_argument('-sf', '--service_functions', required=True, dest="service_functions")
    parser.add_argument('-c', '--config', required=True, dest="config")
    return parser.parse_args()


def main():
    args = parse_args()
    if not args.seed:
        args.seed = random.randint(1, 9999)
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(filename="logs/{}_{}_{}.log".format(os.path.basename(args.network),
                                                            DATETIME, args.seed), level=logging.INFO)
    logging.getLogger("coordsim").setLevel(logging.WARNING)
    logging.getLogger("bjointsp").setLevel(logging.WARNING)

    # Creating the results directory variable where the simulator result files will be written
    network_stem = os.path.splitext(os.path.basename(args.network))[0]
    service_function_stem = os.path.splitext(os.path.basename(args.service_functions))[0]
    simulator_config_stem = os.path.splitext(os.path.basename(args.config))[0]

    results_dir = f"{PROJECT_ROOT}/results/{network_stem}/{service_function_stem}/{simulator_config_stem}" \
                  f"/{DATETIME}_seed{args.seed}"
    # creating the simulator
    # initializing the simulator with absolute paths to the network, service_functions and the config. files.
    simulator = Simulator(os.path.abspath(args.network),
                          os.path.abspath(args.service_functions),
                          os.path.abspath(args.config), test_mode=True, test_dir=results_dir)
    init_state = simulator.init(args.seed)
    # log.info("Network Stats after init(): %s", init_state.network_stats)
    # assuming for now that there is only one SFC.
    sfc_name = list(init_state.sfcs.keys())[0]
    sf_list = list(init_state.sfcs.get(sfc_name))
    sf_delays_dict = init_state.service_functions
    nodes_list = [node['id'] for node in init_state.network.get('nodes')]
    ingress_nodes, node_cap = get_ingress_nodes_and_cap(simulator.network)
    # Getting the Mean Flow Data rate from the sim_config.yaml file
    with open(args.config, "r") as f:
        conf = yaml.load(f, yaml.SafeLoader)
        flow_dr_mean = conf.get('flow_dr_mean')
    # The template dict is fixed, so it is created just once and used throughout for the 'place' fx of BJointSP
    template = create_template(sfc_name, sf_list, sf_delays_dict)

    # Since after the init() call to Simulator we don't get any traffic info back
    # we can't create the source list needed for 'place' function of BJointSP,
    # So we for just the first 'place' call to BJointSP create a source file with just ingress nodes having *
    # *vnf_source as the vnf in it and date_rate of flow_dr_mean from the config file

    source_list = []
    for i in range(len(ingress_nodes)):
        source_list.append({'node': ingress_nodes[i], 'vnf': "vnf_source", 'flows': [{"id": "f" + str(i + 1),
                                                                                      "data_rate": flow_dr_mean}
                                                                                     ]})

    # Since the simulator right now does not have any link_dr , we are using a high value = 1000 for now.
    first_result = bjointsp_place(os.path.abspath(args.network), template, source_list, source_template_object=True,
                                  cpu=node_cap, mem=node_cap, dr=1000, networkx=simulator.network, write_result=False,
                                  logging_level=None)
    # creating the schedule and placement for the simulator from the first result file that BJointSP returns.
    placement, schedule = get_placement_and_schedule(first_result, nodes_list, sfc_name, sf_list)

    # We run the simulator iterations number of times to get the Traffic info from the SimulatorAction object
    # We generate new source file for the BJointSP from the traffic info we get from the simulator for each iteration
    # Using this source file and the already generated Template file we call the 'place' fx of BJointSP
    # In-case no source exists, we use the previous placement and schedule
    for _ in tqdm(range(args.iterations)):
        action = SimulatorAction(placement, schedule)
        apply_state = simulator.apply(action)
        source, source_exists = create_source_object(apply_state.traffic, sf_list, sfc_name, flow_dr_mean)
        if source_exists:
            result = bjointsp_place(os.path.abspath(args.network), template, source, source_template_object=True,
                                    cpu=node_cap, mem=node_cap, dr=1000, networkx=simulator.network, write_result=False,
                                    logging_level=None)
            placement, schedule = get_placement_and_schedule(result, nodes_list, sfc_name, sf_list)

    copy_input_files(results_dir, os.path.abspath(args.network), os.path.abspath(args.service_functions),
                     os.path.abspath(args.config))
    create_input_file(results_dir, len(ingress_nodes), "BJointSP-Default")
    log.info(f"Saved results in {results_dir}")


if __name__ == '__main__':
    main()
