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

def spikesort(data_dir):
    pwd = os.getcwd()
    parent_spikesorting_output_directory = pwd #################### fix to be actual directory like in the og code
    prb_file_path = Path(pwd +"/nancyprobe_linearprobelargespace.prb")
    probe_object = read_prb(prb_file_path)
    probe_df = probe_object.to_dataframe()
    
    recording_filepath_glob = str(Path(data_dir + "/**/*merged.rec"))
    all_recording_files = glob.glob(recording_filepath_glob, recursive=True)
    
    for recording_file in all_recording_files:
        trodes_recording = se.read_spikegadgets(recording_file, stream_id="trodes")       
        trodes_recording = trodes_recording.set_probes(probe_object)
        recording_basename = os.path.basename(recording_file)
        recording_output_directory = f"./proc1/{recording_basename}"
        os.makedirs(recording_output_directory, exist_ok=True)
        child_spikesorting_output_directory = os.path.join(recording_output_directory,"ss_output")

        # Make sure the recording is preprocessed appropriately
        # lazy preprocessing
        recording_filtered = sp.bandpass_filter(trodes_recording, freq_min=300, freq_max=6000)
        recording_preprocessed: si.BaseRecording = sp.whiten(recording_filtered, dtype='float32')
        spike_sorted_object = ms5.sorting_scheme2(
        recording=recording_preprocessed,
        sorting_parameters=ms5.Scheme2SortingParameters(
            detect_sign=0,
            phase1_detect_channel_radius=700,
            detect_channel_radius=700,
            # other parameters...
            )
                )
        spike_sorted_object.save(folder=child_spikesorting_output_directory)

        sw.plot_rasters(spike_sorted_object)
        plt.title(recording_basename)
        plt.ylabel("Unit IDs")

        plt.savefig(os.path.join(recording_output_directory, f"{recording_basename}_raster_plot.png"))
        plt.close()

        waveform_output_directory = os.path.join(parent_spikesorting_output_directory, "waveforms")

        we_spike_sorted = si.extract_waveforms(recording=recording_preprocessed, 
                                       sorting=spike_sorted_object, folder=waveform_output_directory,
                                      ms_before=1, ms_after=1, progress_bar=True,
                                      n_jobs=8, total_memory="1G", overwrite=True,
                                       max_spikes_per_unit=2000)

        phy_output_directory = os.path.join(parent_spikesorting_output_directory, "phy")

        export_to_phy(we_spike_sorted, phy_output_directory,
              compute_pc_features=True, compute_amplitudes=True, remove_if_exists=False)


    # Make sure the recording is preprocessed appropriately
    # lazy preprocessing
    recording_filtered = sp.bandpass_filter(trodes_recording, freq_min=300, freq_max=6000)
    recording_preprocessed: si.BaseRecording = sp.whiten(recording_filtered, dtype='float32')
    spike_sorted_object = ms5.sorting_scheme2(
    recording=recording_preprocessed,
    sorting_parameters=ms5.Scheme2SortingParameters(
        detect_sign=0,
        phase1_detect_channel_radius=700,
        detect_channel_radius=700,
        # other parameters...
        )
            )
    spike_sorted_object.save(folder=child_spikesorting_output_directory)

    sw.plot_rasters(spike_sorted_object)
    plt.title('plot_title')
    plt.ylabel("Unit IDs")

    plt.savefig(os.path.join(recording_output_directory, f"{recording_basename}_raster_plot.png"))
    plt.close()

    waveform_output_directory = os.path.join(parent_spikesorting_output_directory, "waveforms")

    we_spike_sorted = si.extract_waveforms(recording=recording_preprocessed, 
                                   sorting=spike_sorted_object, folder=waveform_output_directory,
                                  ms_before=1, ms_after=1, progress_bar=True,
                                  n_jobs=8, total_memory="1G", overwrite=True,
                                   max_spikes_per_unit=2000)

    phy_output_directory = os.path.join(parent_spikesorting_output_directory, "phy")

    export_to_phy(we_spike_sorted, phy_output_directory,
          compute_pc_features=True, compute_amplitudes=True, remove_if_exists=False)
    return "SPIKES ARE SORTED! :)"

input_text = gr.inputs.Textbox(label="Enter folder path")
output_text = gr.outputs.Textbox(label="Status")
interface = gr.Interface(fn=spikesort, inputs=input_text, outputs=output_text)

interface.launch(server_name="0.0.0.0", server_port=7000)