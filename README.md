# bjointsp-adapter
Adapter to map the inputs and outputs of the B-JointSP to the simulator interface

B-JointSP should work with the [flow-level simulator](https://github.com/RealVNF/coordination-simulation), ie, be aligned to the [interface](https://github.com/RealVNF/coordination-simulation/blob/master/src/siminterface/interface/siminterface.py). This requires mapping the simulator state into something B-JointSP understands and mapping B-JointSP's outputs/placement into something the simulator understands.

B-JointSP input:

* Network, service templates, and previous embeddings should be easy to map
* Sources: Need to map traffic info coming from the simulator to well-defined flows for B-JointSP
  * Idea: Treat all traffic of one SFC at one node as a single flow in B-JointSP
  * Only consider traffic for first SF of SFC?

B-JointSP output:

* B-JointSP also only places max 1 VNF instance per node and uses shortest path routing (check - nothing needed)
* But: Have to map edges (and flows on edges) in the placement, which connect different VNF instances, into scheduling rules for the simulator
