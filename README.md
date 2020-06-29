# BJointSP-adapter Advanced

Adapter to map the inputs and outputs of the B-JointSP to the simulator interface

B-JointSP should work with the [flow-level simulator](https://github.com/RealVNF/coordination-simulation), ie, be aligned to the [interface](https://github.com/RealVNF/coordination-simulation/blob/master/src/siminterface/interface/siminterface.py). This requires mapping the simulator state into something B-JointSP understands and mapping B-JointSP's outputs/placement into something the simulator understands.

<p align="center">
  <img src="docs/realvnf_logo.png" height="150" hspace="30"/>
	<img src="docs/upb.png" width="200" hspace="30"/>
	<img src="docs/huawei_horizontal.png" width="250" hspace="30"/>
</p>

## Working Details

BjoinSP-adapter does the conversion in the following order:

1. Calls BjoinSP's `place` function with the following parameters:
   1. `network file`: path to the file
   2. `template`:path to the file created (just created once and used for every subsequent call to `place`) with the following assumptions/adjustments:
   3. Each VNF has no memory (for simplicity)
   4. An artificial VNF `vnf_source` having no `vnf_delay` is added and connected to the first VNF of the SFC
   5. For each VNF, `vnf_delay` = `processing_delay_mean` from the `config` file
   6. VNFs only have a forward link
   7. The vnf_links has a very high `max_delay` = 1000
   8. `source` : path to a first source file. Since we at the beginning don't have any traffic information from the simulator we have to create this file statically. Each ingress node in the network is assumed to be a source having a single VNF `vnf_source` and the number of flows is calculated by calculating the number of `overlapping` flows as follows:
      overlapping_flows = math.ceil((num_flows \* (processing_delay + flow_duration))/run_duration)
      - number of flows: is given by the simulator in the `traffic_info`
      - processing_delay: taken from the service_function file
      - flow_duration: (flow_size / flow_dr_mean) \* 1000
      - run_duration: taken from the config file
   9. `cpu` = `mem` = `node_capacity` from the network file
   10. dr=1000: Since the simulator in its current state does not have any link_dr , we are using a high value = 1000
2. The results of the `place` call from step `1.` above are used to create the placement and schedule for the simulator as follows:
   1. `placement`: The placements are simply obtained from the result of `place` call.
   2. `schedule`: Since BJointSP does not return any schedule we have create it from the flows information returned by `place`. We assume that there is only a single SFC for simplicity. `flows` keeps track of the number of flows forwarded by BJointSP from a source_node to a dest_node. The schedule is created for each `source node`, for each `VNF` in the SFC, for each `destination node`. If a flow exits in `flows` from source node to destination node for a requested VNF we add it to the schedule. We use the probabilities normalization function `normalize_scheduling_probabilities` such that for each SF the sum of Probabilities is 1
3. The `schedule` and `placement` from step `2.` are used to call the `apply` function of the simulator.
4. The result (traffic info.) of the `apply` call from step `3.` are used to create the `sources` for the next call to BjoinSP's `place` function. The sources are created as follows:

   1. For each ingress node, if the first SF (in our cases `a`) has some aggregate dr , we calculate the number of overlapping flows as follows:

      `overlapping_flows = math.ceil((num_flows * (processing_delay + flow_duration))/run_duration)`

   We then place `overlapping_flows` number of flows, each of `dr` = `flow_dr_mean` on that ingress node with a single VNF `vnf_source`

   2. If traffic_info has no `dr` for `a` on any ingress node, then the source file would be empty

5. If the `source` is created in step `4.` we use it to call BJointSP's `place` and repeat step 2, 3, & 4.
6. If the `source` is not created in step `4.`, the previously calculated `schedule` and `placement` is used to make the next call to the simulator's `apply`.

#### Note: By calculating the overlapping_flows we can run the adapter with any `run_duration`. B-JointSP expects flows that are specified as sources to run in parallel and be competing for resources. A flow is competing for resources while it's being processed by a VNF. So by calculating the number of overlapping_flows we know how many parallel flows that BJointSP needs to cater to.

## Setup

Install [Python 3.6](https://www.python.org/downloads/release/) and [venv](https://docs.python.org/3/library/venv.html) modules.

_Recommended for development_: Clone and install `coord-sim` and `common-utils` locally first in the same venv before running the installation of the adapter in the `editable` mode: `pip install -e bjointsp-adapter`

```bash
# clone this repo and enter dir
git clone git@github.com:RealVNF/bjointsp-adapter.git
cd bjointsp-adapter

# create and activate virtual environment
## On Windows
python -m venv venv
.\venv\Scripts\activate

## On Linux and macOS
python3 -m venv venv
source venv/bin/activate

# install package
pip install -r requirements.txt
```

## Usage

```
usage: bjointsp-adapter [-h] [-i ITERATIONS] [-s SEED] -n NETWORK -sf
                        SERVICE_FUNCTIONS -c CONFIG

BJointSP Adapter

optional arguments:
  -h, --help            show this help message and exit
  -i ITERATIONS, --iterations ITERATIONS
  -s SEED, --seed SEED
  -n NETWORK, --network NETWORK
  -sf SERVICE_FUNCTIONS, --service_functions SERVICE_FUNCTIONS
  -c CONFIG, --config CONFIG
```

Use the following command as an example (from within bjointsp-adapter project folder):

```bash
bjointsp-adapter -n "res/networks/triangle.graphml" \
            -sf "res/service_functions/abc.yaml" \
            -c "res/config/sim_config.yaml" \
            -i 50
```

This will run the bjointsp-adapter and call the `apply()` of the sim-interface and the `place()` of BJointSP 50 times.

### Using the parallel script to run multiple experiments:

There is script provided in the `scripts` folder that utilizes the [GNU Parallel](https://www.gnu.org/software/parallel/) utility to run multiple experiments at the same time to speed up the process. It can run one algorithm at a time, so you need to choose the algo you wanna run at the beginning of the file.

From [scripts directory](scripts) configure the following files:

- [network_files](scripts/network_files.txt): 1 network file location per line
- [config_files](scripts/config_files.txt): 1 simulator config. file location per line
- [service_files](scripts/service_files.txt): 1 SFC file location per line
- [30seeds](scripts/30seeds.txt): 1 seed per run of the simulator. By default using 30 seeds. Add/Remove as per requirement

From the main directory (where the README.md file is) using a Terminal run:

```bash
bash scripts/run_parallel
```

## Acknowledgement

This project has received funding from German Federal Ministry of Education and Research ([BMBF](https://www.bmbf.de/)) through Software Campus grant 01IS17046 ([RealVNF](https://realvnf.github.io/)).

<p align="center">
	<img src="docs/software_campus.png" width="200"/>
	<img src="docs/BMBF_sponsored_by.jpg" width="250"/>
</p>
