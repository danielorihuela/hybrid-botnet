#!/bin/bash

# Activate conda environment
conda env update -f environment.yml
conda activate demo_botnet_hybrid

# Execute tests
pytest
