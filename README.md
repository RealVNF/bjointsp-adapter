# bjointsp-adapter
Adapter to map the inputs and outputs of the B-JointSP to the simulator interface

B-JointSP should work with the [flow-level simulator](https://github.com/RealVNF/coordination-simulation), ie, be aligned to the [interface](https://github.com/RealVNF/coordination-simulation/blob/master/src/siminterface/interface/siminterface.py). This requires mapping the simulator state into something B-JointSP understands and mapping B-JointSP's outputs/placement into something the simulator understands.

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
