import yaml
from collections import defaultdict
from common.common_functionalities import normalize_scheduling_probabilities


def get_placement_and_schedule(results_file_loc, nodes_list, sfc_name, sf_list):
    placement = defaultdict(list)

    # creating the placement for the simulator from the results of BJointSP
    with open(results_file_loc) as f:
        results = yaml.load(f, yaml.SafeLoader)

    for node in nodes_list:
        placement[node] = []

    for vnf in results['placement']['vnfs']:
        placement[vnf['node']].append(vnf['name'])

    # creating the schedule for the simulator from the results of BJointSP
    # we use the flows from the results

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
