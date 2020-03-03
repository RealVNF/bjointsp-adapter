import math
import os
from shutil import copyfile


def create_template(sfc_name, sf_list, sf_delays_dict):
    """
        Creates a template file for BJointSP based on the network file parameters.
        We assume each vnf has no memory for simplicity
        We also add an artificial source vnf 'vnf_source' that is connected with the first vnf of vnf_list
    Parameters:
        sfc_name
        sf_list
        sf_delays_dict
    Returns:
        Template object
    """

    template_dict = {}
    vnfs_list = []
    vlinks_list = []
    template_dict['name'] = sfc_name
    vnf_source = {
        "name": "vnf_source",
        "type": "source",
        "stateful": True,
        "inputs_fwd": 0,
        "inputs_bwd": 0,
        "outputs_fwd": 1,
        "outputs_bwd": 0,
        "cpu": [0],
        "mem": [0],
        "vnf_delay": 0,
        "out_fwd": [],
        "out_bwd": []
    }
    vnfs_list.append(vnf_source)
    for i in range(len(sf_list) - 1):
        vnf = {
            "name": sf_list[i],
            "type": "normal",
            "stateful": False,
            "inputs_fwd": 1,
            "inputs_bwd": 0,
            "outputs_fwd": 1,
            "outputs_bwd": 0,
            "cpu": [1, 0],
            "mem": [0, 0],
            "vnf_delay": sf_delays_dict[sf_list[i]]['processing_delay_mean'],
            "out_fwd": [[1, 0]],
            "out_bwd": []
        }
        vnfs_list.append(vnf)
    vnf_last = {
        "name": sf_list[-1],
        "type": "normal",
        "stateful": False,
        "inputs_fwd": 1,
        "inputs_bwd": 0,
        "outputs_fwd": 0,
        "outputs_bwd": 0,
        "cpu": [1, 0],
        "mem": [0, 0],
        "vnf_delay": sf_delays_dict[sf_list[-1]]['processing_delay_mean'],
        "out_fwd": [],
        "out_bwd": []
    }
    vnfs_list.append(vnf_last)
    template_dict['vnfs'] = vnfs_list

    vlink_source = {
        "direction": "forward",
        "src": "vnf_source",
        "src_output": 0,
        "dest": sf_list[0],
        "dest_input": 0,
        "max_delay": 1000
    }
    vlinks_list.append(vlink_source)

    for i in range(len(sf_list) - 1):
        vlink = {
            "direction": "forward",
            "src": sf_list[i],
            "src_output": 0,
            "dest": sf_list[i + 1],
            "dest_input": 0,
            "max_delay": 1000
        }
        vlinks_list.append(vlink)
    template_dict['vlinks'] = vlinks_list

    return template_dict


def create_source_object(traffic_info, sf_list, sfc_name, ingress_nodes, flow_dr_mean,
                         processing_delay, flow_duration, run_duration):
    """
        - creates the source object for the BJointSP based on the traffic info from the simulator
        - B-JointSP expects flows that are specified as input to run in parallel and be competing for resources
        - So, we're trying to calculate the number of overlapping flows within a given run_duration that overlap
        - A flow is competing for resources while it's being processed by a VNF
        - Processing a flow takes flow_length + vnf_processing time steps. In our case, this is always 1 + 5 = 6
        - If we have a run duration of 100, during which 50 flows arrive, then in total the 50 flows are
          processed for 50x6 = 300 time steps. Since the run duration is only 100, in average 300/100 = 3 flows
          are being processed in parallel, competing for resources.
          Thus, we should specify 3 flows, each with the specified flow size (in our case 1), as input to B-Jointsp.
        - In general, individually for each ingress, compute
              avg_num_parallel_flows = (num_flows * flow_processing_length) / run_duration.
          Then create avg_num_parallel_flows many flows, each with the specified flow size (in our case 1).
        - If traffic_info is empty , then the source would be empty
        - A boolean variable source_exists tells whether the source is empty or not
        - Incase of the empty source , we use the previous schedule and placement for the simulator
    Parameters:
        traffic_info: from simulator
        sf_list
        sfc_name
        flow_dr_mean
        ingress_nodes
        processing_delay
        flow_duration
        run_duration
    Returns:
        source_list: list of sources
        source_exits: boolean indicating whether source file is empty or not
    """

    i = 1
    source_list = []
    source_exists = False
    for node in ingress_nodes:
        flows = []
        first_vnf_dr = traffic_info[node][sfc_name][sf_list[0]]
        if first_vnf_dr:
            source_exists = True
            overlapping_flows = math.ceil((first_vnf_dr * (processing_delay + flow_duration)) / run_duration)
            for _ in range(overlapping_flows):
                flows.append({"id": "f" + str(i), "data_rate": flow_dr_mean})
                i += 1
            source_list.append({'node': node, 'vnf': "vnf_source", 'flows': flows})
    return source_list, source_exists


def copy_input_files(target_dir, network_path, service_path, sim_config_path):
    """Create the results directory and copy input files"""
    new_network_path = f"{target_dir}/{os.path.basename(network_path)}"
    new_service_path = f"{target_dir}/{os.path.basename(service_path)}"
    new_sim_config_path = f"{target_dir}/{os.path.basename(sim_config_path)}"

    os.makedirs(target_dir, exist_ok=True)
    copyfile(network_path, new_network_path)
    copyfile(service_path, new_service_path)
    copyfile(sim_config_path, new_sim_config_path)
