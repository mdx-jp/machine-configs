#!/bin/bash

export LD_LIBRARY_PATH=/usr/local/ucx-1.14.1/lib:/usr/local/openmpi-4.1.5/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
export PATH=/usr/local/ucx-1.14.1/bin:/usr/local/openmpi-4.1.5/bin:$PATH
