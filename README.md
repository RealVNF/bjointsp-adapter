# bjointsp-adapter
Adapter to map the inputs and outputs of the B-JointSP to the simulator interface

B-JointSP should work with the [flow-level simulator](https://github.com/RealVNF/coordination-simulation), ie, be aligned to the [interface](https://github.com/RealVNF/coordination-simulation/blob/master/src/siminterface/interface/siminterface.py). This requires mapping the simulator state into something B-JointSP understands and mapping B-JointSP's outputs/placement into something the simulator understands.

<p align="center">
    <img src="https://raw.githubusercontent.com/RealVNF/deep-rl-service-coordination/master/docs/realvnf_logo.png?token=AIDTJSQ4PTVX6A4D6HSPDDC6RNE54" height="150" hspace="30"/>
	<img src="https://raw.githubusercontent.com/RealVNF/deep-rl-service-coordination/master/docs/upb.png?token=AIDTJSXSEB2M2BEFGFU4N3S6RNFGA" width="200" hspace="30"/>
	<img src="https://raw.githubusercontent.com/RealVNF/deep-rl-service-coordination/master/docs/huawei_horizontal.png?token=AIDTJSSKOEGP7GI6K5YIWUC6RNFH2" width="250" hspace="30"/>
</p>


## Citing this work

If you are using this work in whole or in part in your project, please cite it as follows:

```
@inproceedings{schneider2020coordination,
	author = {Schneider, Stefan and Khalili, Ramin and Manzoor, Adnan and Qarawlus, Haydar and Uthe, Sven and Karl, Holger and Hecker, Artur},
	booktitle = {ACM SIGCOMM NetAI Workshop 2020 (SIGCOMM NetAI ’20)},
	pages = {1--8},
	title = {Self-Driving Coordination of Massively Scaled Services Using Deep Reinforcement Learning},
	year = {2020},
	note = {under review}
}
```

## Working Details
BjoinSP-adapter does the conversion in the following order:
1. Calls BjoinSP's `place` function with the following parameters:
    1. `network file`: path to the file
    2. `template`:path to the file created (just created once and used for every subsequent call to `place`) with the following assumptions/adjustments:
      1. Each VNF has no memory (for simplicity)
      2. An artificial VNF `vnf_source` having no `vnf_delay` is added and connected to the first VNF of the SFC
      3. For each VNF, `vnf_delay` = `processing_delay_mean` from the `config` file
      4. VNFs only have a forward link
      5. The vnf_links has a very high `max_delay` = 1000
    3. `source` : path to a first source file. Since we at the beginning don't have any traffic information  from the simulator we have to create this file statically. Each ingress node in the network is assumed to be a source having a single VNF `vnf_Source` and a single flow of `data_rate` =  `flow_dr_mean` taken from the `config` file
    4. `cpu` = `mem` = `node_capacity` from the network file
    5. dr=1000: Since the simulator in its current state does not have any link_dr , we are using a high value = 1000
2. The results of the `place` call from step `1.` above are used to create the placement and schedule for the simulator as follows:
    1. `placement`: The placements are simply obtained from the result of `place` call.
    2. `schedule`: Since BJointSP does not return any schedule we have create it from the flows information returned by `place`. We assume that there is only a single SFC for simplicity. `flows` keeps track of the number of flows forwarded by BJointSP from a source_node to a dest_node. The schedule is created for each `source node`, for each `VNF` in the SFC, for each `destination node`. If a flow exits in `flows` from source node to destination node for a requested VNF we add it to the schedule. We use the probabilities normalization function `normalize_scheduling_probabilities` such that for each SF the sum of Probabilities is 1
3. The `schedule` and `placement` from step `2.`  are used to call the `apply` function of the simulator.
4. The result (traffic info.) of the `apply` call from step `3.` are used to create the `sources` for the next call to BjoinSP's `place` function. The sources are created as follows:
    1.  For each node in the traffic_info, if the first SF (in our cases `a`) has some aggregate dr , we divide it with the `flow_dr_mean` to get the total number of flows (`number_of_flows`) on that node for the SF. Each such node becomes a source node with `vnf_source` in it and all of the `number_of_flows` each of `flow_dr_mean`.
    2. If traffic_info is empty , then the source file would be empty
5. If the `source` is created in step `4.`  we use it to call BJointSP's `place` and repeat step 2, 3, & 4.
6. If the `source` is not created in step `4.`, the previously calculated `schedule` and `placement` is used to make the next call to the simulator's `apply`.

## Setup

Install [Python 3.6](https://www.python.org/downloads/release/) and [venv](https://docs.python.org/3/library/venv.html) modules.

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
pip install .
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

## Acknowledgement

This project has received funding from German Federal Ministry of Education and Research ([BMBF](https://www.bmbf.de/)) through Software Campus grant 01IS17046 ([RealVNF](https://realvnf.github.io/)).

<p align="center">
	<img src="https://raw.githubusercontent.com/RealVNF/deep-rl-service-coordination/master/docs/software_campus.png?token=AIDTJSQS7WZNSZHFL23FNYS6RNFJK" width="200"/>
	<img src="https://raw.githubusercontent.com/RealVNF/deep-rl-service-coordination/master/docs/BMBF_sponsored_by.jpg?token=AIDTJSRMQYSKOC7K3EWIQ5S6RNFKW" width="250"/>
</p>
