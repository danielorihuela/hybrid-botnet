#!/bin/bash

# Activate conda environment
conda env update -f environment.yml
conda activate demo_botnet_p2p

# Execute tests
pwd
pytest ./tests/unit_tests/
