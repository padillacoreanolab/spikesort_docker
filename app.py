import os
import pickle
import glob
import warnings
import git
import imp
import spikeinterface
import time
import json
import spikeinterface.core
import numpy as np
import pandas as pd
import scipy.signal
import _pickle as cPickle
import matplotlib.pyplot as plt
import spikeinterface as si  # import core only
import spikeinterface.extractors as se
import spikeinterface.sorters as ss
import spikeinterface.preprocessing as sp
import spikeinterface.comparison as sc
import spikeinterface.widgets as sw
import spikeinterface.full as si
import mountainsort5 as ms5
from collections import defaultdict
from datetime import datetime
from matplotlib.pyplot import cm
from spikeinterface.exporters import export_to_phy
from probeinterface import get_probe
from probeinterface.plotting import plot_probe, plot_probe_group
from probeinterface import write_prb, read_prb
from pathlib import Path
import gradio as gr 

def add_string(text: str, add: str) -> str:
    return text + add

iface = gr.Interface(
    fn=add_string,
    inputs=["text", "text"],
    outputs="text",
    title="Add String",
    description="Add a string to the end of your text."
)

iface.launch(server_name="0.0.0.0", server_port=7000)