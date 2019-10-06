from collections import defaultdict

import yaml
from common.common_functionalities import normalize_scheduling_probabilities


def get_placement_and_schedule(results_file_loc, nodes_list, sfc_name, sf_list):
    """
    Reads the results file created by the BJointSP to create the placement and schedule for the simulator

    Parameters:
        results_file_loc: Results file from BJointSP
        nodes_list
        sfc_name
        sf_list
    Returns:
         placement
         schedule

    placement is a Dictionary with:
            key = nodes of the network
            value = list of all the SFs in the network

    schedule is of the following form:
            schedule : dict
                {
                    'node id' : dict
                    {
                        'SFC id' : dict
                        {
                            'SF id' : dict
                            {
                                'node id' : float (Inclusive of zero values)
                            }
                        }
                    }
                }

    """
    placement = defaultdict(list)

    # creating the placement for the simulator from the results of BJointSP
    with open(results_file_loc) as f:
        results = yaml.load(f, yaml.SafeLoader)

    for node in nodes_list:
        placement[node] = []

    # The simulator does not need the 'vnf_source', we just need it for the BJointSP.
    # In the 'apply' fx. of the simulator 'vnf_source' causes an error as it cannot find it from the network file.
    for vnf in results['placement']['vnfs']:
        if vnf['name'] != 'vnf_source':
            placement[vnf['node']].append(vnf['name'])

    # creating the schedule for the simulator from the results of BJointSP
    # we use the flows from the results file

    # 'flows' keeps track of the number of flows forwarded by BJointSP from a source_node to a dest_node with
    # dest_vnf(or requested vnf) lying in the dest_node.
    # The schedule is finally created for each vnf in the vnf_list from each node of the network to all the nodes
    # We use the probabilities normalization function 'normalize_scheduling_probabilities' such that for each SF,*
    # *the sum of Probabilities is 1
    flows = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    for flow in results['placement']['flows']:
        source_node = flow['src_node']
        dest_node = flow['dst_node']
        vnf = flow['dest_vnf']
        if flows[source_node][dest_node][vnf]:
            flows[source_node][dest_node][vnf] += 1
        else:
            flows[source_node][dest_node][vnf] = 1

    schedule = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(float))))

    for src_node in nodes_list:
        for sf in sf_list:
            prob_list = []
            for dest_node in nodes_list:
                if flows[src_node][dest_node][sf]:
                    prob_list.append(flows[src_node][dest_node][sf])
                else:
                    prob_list.append(0)
            rounded_prob_list = normalize_scheduling_probabilities(prob_list)
            for i in range(len(nodes_list)):
                schedule[src_node][sfc_name][sf][nodes_list[i]] = rounded_prob_list[i]
    return placement, schedule
