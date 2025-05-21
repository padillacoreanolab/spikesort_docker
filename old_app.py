import os
import pickle
import glob
import warnings
# import git # Note: 'git' import is present but not used in the provided spikesort function.
# import imp   # Note: 'imp' is deprecated, consider 'importlib'. Not used in spikesort function.
import spikeinterface
import time
import json
import spikeinterface.core
import numpy as np
import pandas as pd
import scipy.signal
# import _pickle as cPickle # Note: 'cPickle' is for Python 2. In Python 3, 'pickle' is often optimized.
import matplotlib.pyplot as plt
import spikeinterface as si  # First import: 'si' is spikeinterface (core-like)
import spikeinterface.extractors as se
import spikeinterface.sorters as ss
import spikeinterface.preprocessing as sp
import spikeinterface.comparison as sc
import spikeinterface.widgets as sw
import spikeinterface.full as si # Second import: 'si' is rebound to spikeinterface.full
                                 # All subsequent 'si.' calls will use 'spikeinterface.full'
import mountainsort5 as ms5
from collections import defaultdict
from datetime import datetime
from matplotlib.pyplot import cm
from spikeinterface.exporters import export_to_phy
# from probeinterface import get_probe # Not used directly, read_prb is used.
# from probeinterface.plotting import plot_probe, plot_probe_group # Not used in spikesort function.
from probeinterface import read_prb # write_prb removed as it's not used
from pathlib import Path
import shutil
import argparse # Added for command-line arguments
import traceback # For more detailed error reporting

# --- Main Spikesorting Function ---
def spikesort(source_dir: Path, output_dir: Path, probe_filename: str = "nancyprobe_linearprobelargespace.prb"):
    # Determine the directory of the currently running script (app.py)
    script_dir = Path(__file__).resolve().parent
    
    print(f"Script directory (where probe file is expected): {script_dir}")
    print(f"Source directory (for ephys data): {source_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Probe filename: {probe_filename}")

    # Ensure top-level output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Construct path to the probe file, now relative to the script directory
    prb_file_path = script_dir / probe_filename
    if not prb_file_path.is_file():
        print(f"ERROR: Probe file '{probe_filename}' not found in the script directory '{script_dir}'.")
        print(f"Full path checked: {prb_file_path.resolve()}")
        return f"ERROR: Probe file '{prb_file_path}' not found."

    print(f"Loading probe file from: {prb_file_path}")
    try:
        probe_object = read_prb(prb_file_path)
        probe_df = probe_object.to_dataframe()
        print("Probe Dataframe (first 5 rows):")
        print(probe_df.head())
    except Exception as e:
        print(f"ERROR: Could not read or parse probe file {prb_file_path}. Exception: {e}")
        traceback.print_exc()
        return f"ERROR: Failed to load probe file."

    # Find all .merged.rec files recursively in the source directory
    recording_filepath_glob_pattern = str(source_dir / "**" / "*merged.rec")
    all_recording_files = [Path(p) for p in glob.glob(recording_filepath_glob_pattern, recursive=True)]

    if not all_recording_files:
        print(f"WARNING: No '*.merged.rec' files found matching pattern: {recording_filepath_glob_pattern}")
        return "No .rec files found. Spikesorting cannot proceed."

    print(f"Found {len(all_recording_files)} recording file(s) to process.")

    for recording_file_path in all_recording_files:
        print(f"\n--- Processing recording file: {recording_file_path} ---")

        try:
            relative_rec_path = recording_file_path.relative_to(source_dir)
            output_subfolder_name = relative_rec_path.with_suffix('') 
            
            current_recording_output_base = output_dir / "proc" / output_subfolder_name
            current_recording_output_base.mkdir(parents=True, exist_ok=True)
            
            recording_display_name = recording_file_path.name 
            print(f"Output directory for this recording: {current_recording_output_base}")

            trodes_recording = se.read_spikegadgets(str(recording_file_path), stream_id="trodes")
            trodes_recording = trodes_recording.set_probes(probe_object)
            
            child_spikesorting_output_dir = current_recording_output_base / "ss_output"
            child_temp_preprocessed_dir = current_recording_output_base / "preprocessed_recording_output_temp"

            print("Preprocessing: Bandpass filtering and whitening...")
            recording_filtered = sp.bandpass_filter(trodes_recording, freq_min=300, freq_max=6000)
            recording_preprocessed: si.BaseRecording = sp.whiten(recording_filtered, dtype='float32')
            
            recording_preprocessed_disk = recording_preprocessed.save(folder=child_temp_preprocessed_dir, overwrite=True)
            print(f"Temporary preprocessed data saved to: {child_temp_preprocessed_dir}")

            print("Running MountainSort5 (scheme2)...")
            scheme2_params = ms5.Scheme2SortingParameters(
                detect_sign=0,
                phase1_detect_channel_radius=700,
                detect_channel_radius=700,
            )
            spike_sorted_object = ms5.sorting_scheme2(
                recording=recording_preprocessed_disk, 
                sorting_parameters=scheme2_params
            )
            
            print("Saving sorting results...")
            spike_sorted_object_disk = spike_sorted_object.save(folder=child_spikesorting_output_dir, overwrite=True)
            print(f"Spike sorting output saved to: {child_spikesorting_output_dir}")

            print(f"Plotting raster for {recording_display_name}...")
            sw.plot_rasters(spike_sorted_object_disk)
            plt.title(recording_display_name)
            plt.ylabel("Unit IDs")
            raster_plot_path = current_recording_output_base / f"{recording_display_name}_raster_plot.png"
            plt.savefig(raster_plot_path)
            plt.close() 
            print(f"Raster plot saved to: {raster_plot_path}")

            waveform_output_dir = current_recording_output_base / "waveforms"
            print(f"Extracting waveforms to: {waveform_output_dir}...")
            we_spike_sorted = si.extract_waveforms(
                recording=recording_preprocessed_disk, 
                sorting=spike_sorted_object_disk,
                folder=str(waveform_output_dir), 
                ms_before=1, ms_after=1, 
                progress_bar=True,
                n_jobs=8, 
                total_memory="1G", 
                overwrite=True,
                max_spikes_per_unit=2000
            )
            print("Waveform extraction complete.")

            print(f"Removing temporary preprocessed recording directory: {child_temp_preprocessed_dir}")
            shutil.rmtree(child_temp_preprocessed_dir)

            phy_output_dir = current_recording_output_base / "phy"
            print(f"Exporting to PHY format at: {phy_output_dir}...")
            export_to_phy(
                waveform_extractor=we_spike_sorted,
                output_folder=str(phy_output_dir), 
                compute_pc_features=True,
                compute_amplitudes=True,
                remove_if_exists=True 
            )
            print("PHY export complete.")

            params_py_path = phy_output_dir / "params.py"
            if params_py_path.is_file():
                with open(params_py_path, 'r') as file:
                    lines = file.readlines()
                lines[0] = "dat_path = r'./recording.dat'\n" 
                with open(params_py_path, 'w') as file:
                    file.writelines(lines)
                print(f"Updated params.py in {phy_output_dir}")
            else:
                print(f"WARNING: params.py not found in {phy_output_dir}. Cannot update dat_path.")
            
            print(f"--- Successfully processed: {recording_file_path} ---")

        except Exception as e:
            print(f"ERROR processing file {recording_file_path}: {e}")
            traceback.print_exc() 
            # Continue to the next file if an error occurs
            print(f"Skipping to next file due to error with {recording_file_path}.")
            continue


    return "SPIKESORTING PROCESS COMPLETED (see logs for details on individual files)."


# --- Main execution block for command-line usage ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Spike sort ephys data from .merged.rec files.")
    parser.add_argument("source_directory", type=str, 
                        help="Directory containing the .merged.rec files (can be in subfolders).")
    parser.add_argument("output_directory", type=str, 
                        help="Directory where all processing outputs will be saved.")
    parser.add_argument("--probe_filename", type=str, default="nancyprobe_linearprobelargespace.prb",
                        help="Name of the probe file (e.g., 'myprobe.prb'). Default: 'nancyprobe_linearprobelargespace.prb'. "
                             "This file must be located in the same directory as the app.py script.") # Updated help text
    
    args = parser.parse_args()

    # Resolve paths to be absolute for robustness
    source_path = Path(args.source_directory).resolve() 
    output_path = Path(args.output_directory).resolve()

    if not source_path.is_dir():
        print(f"Error: Source directory not found or is not a directory: {source_path}")
        exit(1) # Exit if source directory is invalid

    # Call the main spikesorting function
    start_time = time.time()
    status = spikesort(source_dir=source_path, output_dir=output_path, probe_filename=args.probe_filename)
    end_time = time.time()
    print(f"\n{status}")
    print(f"Total processing time: {end_time - start_time:.2f} seconds.")

    # Gradio interface code (remains commented out as per previous versions)
    # ...