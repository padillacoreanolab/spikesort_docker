#!/usr/bin/env python3
import os
import glob
import argparse
import shutil
import warnings
import json
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import spikeinterface as si
import spikeinterface.extractors as se
import spikeinterface.preprocessing as sp
import spikeinterface.widgets as sw
import spikeinterface.sorters as ss
from spikeinterface.exporters import export_to_phy
from probeinterface import get_probe, read_prb

import signal
import sys

warnings.filterwarnings("ignore", category=DeprecationWarning)

def handle_sigint(signum, frame):
    print("KeyboardInterrupt (Ctrl-C) received. Exiting gracefully...")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_sigint)

def is_gpu_available():
    """
    Check if a GPU is available.
    Attempts to import cupy and torch to query GPU availability.
    """
    try:
        import cupy
        if cupy.cuda.runtime.getDeviceCount() > 0:
            return True
    except Exception:
        pass
    try:
        import torch
        if torch.cuda.is_available():
            return True
    except Exception:
        pass
    return False

def process_recording(recording_file, output_folder, probe_object, sort_params,
                      stream_id, freq_min, freq_max, whiten_dtype, force_cpu,
                      ms_before, ms_after, n_jobs, total_memory,
                      compute_pc_features, compute_amplitudes,
                      random_spikes_max, pc_n_components, pc_mode, spike_amp_peak_sign):
    """
    Process a single recording file using supplied parameters.
    Each recording's outputs will be stored in a subfolder under the user-specified
    output folder (structure: <output_folder>/proc/<recording_basename>/).
    """
    recording_basename = os.path.basename(recording_file)
    output_base = Path(output_folder) / "proc" / recording_basename

    # Define the completion marker file
    complete_marker = output_base / "complete.txt"

    # Check for existing final output: if the 'phy' folder or completion marker exists, skip processing.
    phy_output_directory = output_base / "phy"
    if phy_output_directory.exists() or complete_marker.exists():
        print(f"Skipping {recording_basename}: output already exists or processing is complete.")
        return

    print(f"\nProcessing recording: {recording_file}")
    os.makedirs(output_base, exist_ok=True)
    
    # Define directories for sorter output, preprocessed recording, and waveforms.
    ss_output_dir = output_base / "ss_output"
    preproc_rec_dir = output_base / "preprocessed_recording_output"
    waveform_output_dir = output_base / "waveforms"
    
    # Remove the existing sorter output folder if it exists.
    if ss_output_dir.exists():
        print(f"Removing existing sorter output folder: {ss_output_dir}")
        shutil.rmtree(str(ss_output_dir))

    try:
        # Load recording and attach probe using set_probe.
        recording_obj = se.read_spikegadgets(recording_file, stream_id=stream_id)
        recording_obj = recording_obj.set_probes(probe_object)

        # Preprocessing: bandpass filtering then whitening.
        recording_filtered = sp.bandpass_filter(recording_obj, freq_min=freq_min, freq_max=freq_max)
        recording_preprocessed = sp.whiten(recording_filtered, dtype=whiten_dtype)
        # Re-attach the probe after processing.
        recording_preprocessed = recording_preprocessed.set_probes(probe_object)

        # Prepare sorter parameters.
        default_sort_params = {
            "torch_device": "cuda" if is_gpu_available() and not force_cpu else "cpu"
        }
        default_sort_params.update(sort_params)

        print("Running sorting with Kilosort4 via unified interface...")
        spike_sorted = ss.run_sorter(
            'kilosort4',
            recording=recording_preprocessed,
            folder=str(ss_output_dir),
            **default_sort_params
        )

        # Save outputs.
        print("Saving spike sorted output to disk...")
        spike_sorted_disk = spike_sorted.save(folder=str(ss_output_dir), overwrite=None)
        print("Spike sorted output saved to:", ss_output_dir)

        print("Saving preprocessed recording to disk...")
        recording_preproc_disk = recording_preprocessed.save(folder=str(preproc_rec_dir), overwrite=None)
        print("Preprocessed recording saved to:", preproc_rec_dir)

        # Plot raster and save figure.
        print("Generating and saving raster plot...")
        sw.plot_rasters(spike_sorted)
        plt.title(recording_basename)
        plt.ylabel("Unit IDs")
        raster_plot_path = output_base / f"{recording_basename}_raster_plot.png"
        plt.savefig(str(raster_plot_path))
        plt.close()
        print("Raster plot saved at:", raster_plot_path)

        # --- Use the new waveform extraction API ---
        print("Extracting waveforms using si.extract_waveforms()...")
        we = si.extract_waveforms(
            recording=recording_preproc_disk,
            sorting=spike_sorted_disk,
            folder=str(waveform_output_dir),
            ms_before=ms_before,
            ms_after=ms_after,
            max_spikes_per_unit=random_spikes_max,
            n_jobs=n_jobs,
            total_memory=total_memory,
            overwrite=None
        )
        print("Waveform extraction initiated...")
        we.extract_waveforms()
        print("Waveforms extraction complete.")

        # Compute additional extensions if desired.
        print("Computing principal components (default: n_components=%d, mode='%s')..." % (pc_n_components, pc_mode))
        we.compute_principal_components(n_components=pc_n_components, mode=pc_mode)
        print("Principal components computed with n_components=%d and mode='%s'.\n" % (pc_n_components, pc_mode))

        print("Computing spike amplitudes (default: peak_sign='%s')..." % spike_amp_peak_sign)
        we.compute_spike_amplitudes(peak_sign=spike_amp_peak_sign)
        print("Spike amplitudes computed with peak_sign='%s'.\n" % spike_amp_peak_sign)

        # Export to Phy using WaveformExtractor.
        print("Exporting to Phy using WaveformExtractor...")
        we.export_to_phy()
        print("PHY export saved!")

        # Update params.py to include the correct relative path.
        params_path = phy_output_directory / "params.py"
        if params_path.exists():
            with open(params_path, "r") as f:
                lines = f.readlines()
            lines[0] = "dat_path = r'./recording.dat'\n"
            with open(params_path, "w") as f:
                f.writelines(lines)
        else:
            print(f"Warning: params.py not found in {phy_output_directory}")

        # Write the completion marker.
        with open(complete_marker, "w") as f:
            f.write(f"Processing completed on {datetime.now()}\n")

        print(f"Finished processing {recording_basename}")

    except Exception as e:
        if "No non-empty units" in str(e):
            print(f"Skipping {recording_basename}: {str(e)}")
        else:
            print(f"Error processing {recording_basename}: {str(e)}")
        return

def str2bool(v):
    """
    Convert string to boolean.
    """
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
       return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
       return False
    else:
       raise argparse.ArgumentTypeError('Boolean value expected.')

def main():
    parser = argparse.ArgumentParser(description="Spike Sorting Command Line Tool with full parameter control")
    # Input and probe configuration.
    parser.add_argument("--data-folder", type=str, required=True,
                        help="Path to the folder containing recording files (searches recursively).")
    parser.add_argument("--output-folder", type=str, default=".",
                        help="Directory where processed output will be saved (default: current directory).")
    parser.add_argument("--prb-file", type=str, default=None,
                        help="Path to a .prb file for probe configuration. Uses default probe file if not provided.")
    parser.add_argument("--disable-batch", action="store_true",
                        help="If set, only one recording file will be processed (batch processing disabled).")
    parser.add_argument("--recording-file", type=str, default=None,
                        help="Specify a single recording file to process (used when batch processing is disabled).")
    parser.add_argument("--stream-id", type=str, default="trodes",
                        help="Stream ID to use when reading recording files (default: 'trodes').")

    # Preprocessing parameters.
    parser.add_argument("--freq-min", type=float, default=300,
                        help="Minimum frequency for bandpass filtering (default: 300 Hz).")
    parser.add_argument("--freq-max", type=float, default=6000,
                        help="Maximum frequency for bandpass filtering (default: 6000 Hz).")
    parser.add_argument("--whiten-dtype", type=str, default="float32",
                        help="Data type for whitening (default: 'float32').")

    # Sorting parameters.
    parser.add_argument("--sort-params", type=str, default="{}",
                        help="JSON string to override default sorting parameters (e.g., '{\"parameter_name\": value}').")
    parser.add_argument("--force-cpu", action="store_true",
                        help="If set, forces sorting to run on CPU even if a GPU is available.")

    # Waveform extraction parameters.
    parser.add_argument("--ms-before", type=float, default=1,
                        help="Milliseconds before spike for waveform extraction (default: 1).")
    parser.add_argument("--ms-after", type=float, default=1,
                        help="Milliseconds after spike for waveform extraction (default: 1).")
    parser.add_argument("--n-jobs", type=int, default=8,
                        help="Number of jobs for waveform extraction (default: 8).")
    parser.add_argument("--total-memory", type=str, default="16G",
                        help="Total memory available for waveform extraction (default: '16G').")

    # Phy export parameters.
    parser.add_argument("--compute-pc-features", type=str2bool, default=True,
                        help="Compute PC features for Phy export (default: True).")
    parser.add_argument("--compute-amplitudes", type=str2bool, default=True,
                        help="Compute amplitudes for Phy export (default: True).")

    # New post-processing extension parameters.
    parser.add_argument("--random-spikes-max", type=int, default=200,
                        help="Max spikes per unit for random spikes computation (default: 200).")
    parser.add_argument("--pc-n-components", type=int, default=3,
                        help="Number of principal components (default: 3).")
    parser.add_argument("--pc-mode", type=str, default="by_channel_local",
                        help="PCA mode (default: 'by_channel_local').")
    parser.add_argument("--spike-amp-peak-sign", type=str, default="neg",
                        help="Peak sign for spike amplitude computation (default: 'neg').")

    args = parser.parse_args()
    
    if args.recording_file == "":
        args.recording_file = None

    if args.prb_file == "":
        args.prb_file = None

    try:
        sort_params = json.loads(args.sort_params)
    except json.JSONDecodeError as e:
        print("Error parsing sort parameters. Please provide a valid JSON string.")
        return

    # Print GPU/CPU information.
    gpu_available = is_gpu_available()
    if args.force_cpu:
        print("Forcing CPU for sorting.")
    else:
        if gpu_available:
            print("GPU is available. Using GPU for sorting.")
        else:
            print("GPU not available. Using CPU for sorting.")

    # Load probe configuration.
    if args.prb_file:
        prb_path = Path(args.prb_file)
        if not prb_path.exists():
            print(f"Provided prb file '{args.prb_file}' does not exist. Exiting.")
            return
        probe_object = read_prb(str(prb_path))
        print(f"Using probe configuration from: {args.prb_file}")
    else:
        default_probe_path = Path(__file__).parent / "nancyprobe_linearprobelargespace.prb"
        if not default_probe_path.exists():
            print(f"Default probe file not found at: {default_probe_path}. Exiting.")
            return
        print(f"No prb file provided; using default probe file at: {default_probe_path}")
        probe_object = read_prb(str(default_probe_path))
    
    # Determine which recordings to process.
    data_folder = args.data_folder
    if args.disable_batch:
        if args.recording_file:
            recording_files = [args.recording_file]
        else:
            recording_files = glob.glob(os.path.join(data_folder, "**/*merged.rec"), recursive=True)
            if recording_files:
                recording_files = [recording_files[0]]
            else:
                print("No recording files found in the provided data folder.")
                return
    else:
        recording_files = glob.glob(os.path.join(data_folder, "**/*merged.rec"), recursive=True)
        if not recording_files:
            print("No recording files found in the provided data folder.")
            return

    print(f"Found {len(recording_files)} recording file(s) to process.")

    for rec_file in recording_files:
        if os.path.isdir(rec_file):
            continue
        process_recording(
            recording_file=rec_file,
            output_folder=args.output_folder,
            probe_object=probe_object,
            sort_params=sort_params,
            stream_id=args.stream_id,
            freq_min=args.freq_min,
            freq_max=args.freq_max,
            whiten_dtype=args.whiten_dtype,
            force_cpu=args.force_cpu,
            ms_before=args.ms_before,
            ms_after=args.ms_after,
            n_jobs=args.n_jobs,
            total_memory=args.total_memory,
            compute_pc_features=args.compute_pc_features,
            compute_amplitudes=args.compute_amplitudes,
            random_spikes_max=args.random_spikes_max,
            pc_n_components=args.pc_n_components,
            pc_mode=args.pc_mode,
            spike_amp_peak_sign=args.spike_amp_peak_sign
        )

    print("\nBatch processing complete. SPIKES ARE SORTED! :)")

if __name__ == '__main__':
    import multiprocessing as mp
    mp.set_start_method('fork', force=True)
    main()
