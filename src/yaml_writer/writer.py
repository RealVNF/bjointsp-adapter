import yaml

TEMPLATES_DIRECTORY = "res/templates/"
BJOINTSP_SOURCE_LOCATION = "res/sources/source.yaml"
PREV_EMBEDDING_LOCATION = "res/prev_embedding/prev.yaml"


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
        file_loc: relative path of the template file
    """
    file_loc = TEMPLATES_DIRECTORY + sfc_name + ".yaml"
    with open(file_loc, "w") as f:
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
        yaml.dump(template_dict, f, default_flow_style=False)
    return file_loc


def create_source_file(traffic_info, sf_list, sfc_name, flow_dr_mean):
    """
        - creates the source file for the BJointSP based on the traffic info from the simulator
        - for each node in the traffic_info, if the first SF has some aggregate dr , we divide it with the mean flow dr
          to get the total number of flows on that node for the SF. Each such node becomes a source node with vnf_source
          in it and total flows each of mean date rate.
        - If traffic_info is empty , then the source file would be empty
        - A boolean variable source_exists tells whether the source file is empty or not
        - Incase of the empty source file, we use the previous schedule and placement for the simulator
    Parameters:
        traffic_info: from simulator
        sf_list
        sfc_name:
        flow_dr_mean:
    Returns:
        JOINTSP_SOURCE_LOCATION: source file location
        source_exits: boolean indicating whether source file is empty or not
    """
    with open(BJOINTSP_SOURCE_LOCATION, "w") as f:
        i = 1
        source_list = []
        source_exists = False
        for node in traffic_info:
            flows = []
            first_vnf_dr = traffic_info[node][sfc_name][sf_list[0]]
            if first_vnf_dr:
                source_exists = True
                number_of_flows = int(first_vnf_dr / flow_dr_mean)
                for _ in range(number_of_flows):
                    flows.append({"id": "f" + str(i), "data_rate": flow_dr_mean})
                    i += 1
                source_list.append({'node': node, 'vnf': "vnf_source", 'flows': flows})
        yaml.dump(source_list, f, default_flow_style=False)
    return BJOINTSP_SOURCE_LOCATION, source_exists
