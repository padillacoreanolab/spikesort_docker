import os
import pickle
import glob
import warnings
# import git
# import imp
import spikeinterface
import time
import json
import spikeinterface.core
import numpy as np
import pandas as pd
import scipy.signal
# import _pickle as cPickle
import matplotlib.pyplot as plt
import spikeinterface as si # This is fine, but later spikeinterface.full is also imported as si
import spikeinterface.extractors as se
import spikeinterface.sorters as ss
import spikeinterface.preprocessing as sp
import spikeinterface.comparison as sc
import spikeinterface.widgets as sw
import spikeinterface.full as si_full # Changed to si_full to avoid rebind if 'si' from spikeinterface is intended elsewhere
import mountainsort5 as ms5
from collections import defaultdict
from datetime import datetime
from matplotlib.pyplot import cm
from spikeinterface.exporters import export_to_phy
from probeinterface import read_prb
from pathlib import Path
import shutil
import argparse
import traceback
# import signal # Not strictly needed for basic Ctrl+C, but can be used for more complex handling

# --- Main Spikesorting Function ---
def spikesort(source_dir: Path, output_dir: Path, probe_filename: str = "nancyprobe_linearprobelargespace.prb"):
    script_dir = Path(__file__).resolve().parent

    print(f"Script directory (where probe file is expected): {script_dir}")
    print(f"Source directory (for ephys data): {source_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Probe filename: {probe_filename}")

    output_dir.mkdir(parents=True, exist_ok=True)

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

    recording_filepath_glob_pattern = str(source_dir / "**" / "*merged.rec")
    all_recording_files = [Path(p) for p in glob.glob(recording_filepath_glob_pattern, recursive=True)]

    if not all_recording_files:
        print(f"WARNING: No '*.merged.rec' files found matching pattern: {recording_filepath_glob_pattern}")
        return "No .rec files found. Spikesorting cannot proceed."

    print(f"Found {len(all_recording_files)} recording file(s) to process.")

    for recording_file_path in all_recording_files:
        print(f"\n--- Processing recording file: {recording_file_path} ---")

        relative_rec_path = recording_file_path.relative_to(source_dir)
        # Ensure output_subfolder_name doesn't start with a separator if relative_rec_path is just a filename
        if relative_rec_path.parent == Path("."):
            output_subfolder_name = Path(relative_rec_path.stem)
        else:
            output_subfolder_name = relative_rec_path.with_suffix('')

        current_recording_output_base = output_dir / "proc" / output_subfolder_name
        child_spikesorting_output_dir = current_recording_output_base / "ss_output"
        child_temp_preprocessed_dir = current_recording_output_base / "preprocessed_recording_output_temp"
        waveform_output_dir = current_recording_output_base / "waveforms"
        phy_output_dir = current_recording_output_base / "phy"

        # Declare child_temp_preprocessed_dir here so it's defined for finally
        # even if an error occurs before it's normally assigned in the try block.
        # However, its existence is checked in `finally`, so this is mostly for clarity.

        try:
            current_recording_output_base.mkdir(parents=True, exist_ok=True)
            recording_display_name = recording_file_path.name
            print(f"Output directory for this recording: {current_recording_output_base}")

            trodes_recording = se.read_spikegadgets(str(recording_file_path), stream_id="trodes")
            trodes_recording = trodes_recording.set_probes(probe_object)

            print("Preprocessing: Bandpass filtering and whitening...")
            recording_filtered = sp.bandpass_filter(trodes_recording, freq_min=300, freq_max=6000)
            recording_preprocessed: si_full.BaseRecording = sp.whiten(recording_filtered, dtype='float32') # Using si_full

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

            if waveform_output_dir.exists() and waveform_output_dir.is_dir():
                print(f"Manually removing existing waveform directory before extraction: {waveform_output_dir}")
                shutil.rmtree(waveform_output_dir)

            print(f"Extracting waveforms to: {waveform_output_dir}...")
            we_spike_sorted = si_full.extract_waveforms( # Using si_full
                recording=recording_preprocessed_disk,
                sorting=spike_sorted_object_disk,
                folder=str(waveform_output_dir),
                ms_before=1, ms_after=1,
                progress_bar=True,
                n_jobs=1,
                total_memory="2G",
                overwrite=True,
                max_spikes_per_unit=2000
            )
            print("Waveform extraction complete.")

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
                # Ensure dat_path uses forward slashes for better cross-platform compatibility in Phy
                # and is relative to the phy_output_dir where params.py resides.
                lines[0] = "dat_path = 'recording.dat'\n" # Phy expects it relative to params.py
                with open(params_py_path, 'w') as file:
                    file.writelines(lines)
                print(f"Updated params.py in {phy_output_dir}")
            else:
                print(f"WARNING: params.py not found in {phy_output_dir}. Cannot update dat_path.")

            print(f"--- Successfully processed: {recording_file_path} ---")

        except Exception as e: # This will NOT catch KeyboardInterrupt by default
            print(f"ERROR processing file {recording_file_path}: {e}")
            traceback.print_exc()
            print(f"Skipping to next file due to error with {recording_file_path}.")
            # The 'finally' block below will still execute for cleanup

        finally:
            # This block executes for normal completion of try, if an Exception
            # (but not KeyboardInterrupt) is caught by the 'except Exception as e:' block,
            # or if a BaseException (like KeyboardInterrupt) occurs within the 'try' block.
            if child_temp_preprocessed_dir.exists() and child_temp_preprocessed_dir.is_dir():
                try:
                    print(f"Cleaning up temporary preprocessed data at: {child_temp_preprocessed_dir}")
                    shutil.rmtree(child_temp_preprocessed_dir)
                    print(f"Successfully removed: {child_temp_preprocessed_dir}")
                except OSError as e_rm:
                    print(f"ERROR: Could not remove temporary directory {child_temp_preprocessed_dir}. Reason: {e_rm}")
            else:
                # This can happen if interrupt occurred before dir creation or if already cleaned
                print(f"Temporary directory {child_temp_preprocessed_dir} for {recording_file_path.name} not found or already cleaned during this attempt.")
            print(f"--- Finished processing/cleanup attempt for: {recording_file_path} ---")

    return "SPIKESORTING PROCESS COMPLETED (or all files attempted)."


# --- Main execution block for command-line usage ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Spike sort ephys data from .merged.rec files.")
    parser.add_argument("source_directory", type=str,
                        help="Directory containing the .merged.rec files (can be in subfolders).")
    parser.add_argument("output_directory", type=str,
                        help="Directory where all processing outputs will be saved.")
    parser.add_argument("--probe_filename", type=str, default="nancyprobe_linearprobelargespace.prb",
                        help="Name of the probe file (e.g., 'myprobe.prb'). Default: 'nancyprobe_linearprobelargespace.prb'. "
                             "This file must be located in the same directory as this script.")

    args = parser.parse_args()

    source_path = Path(args.source_directory).resolve()
    output_path = Path(args.output_directory).resolve()

    if not source_path.is_dir():
        print(f"Error: Source directory not found or is not a directory: {source_path}")
        exit(1)

    start_time = time.time() # Initialize start_time here
    status_message = "" # Initialize status_message

    try:
        status_message = spikesort(source_dir=source_path, output_dir=output_path, probe_filename=args.probe_filename)
        end_time = time.time()
        print(f"\n{status_message}")
        if status_message.startswith("ERROR"): # Check if spikesort itself returned an initial error
            print("Script terminated early due to a critical error before or during initial setup.")
        else:
            print(f"Total processing time: {end_time - start_time:.2f} seconds.")

    except KeyboardInterrupt:
        print("\n\n>>> Execution interrupted by user (Ctrl+C). <<<")
        # The per-file 'finally' clause in the spikesort function should have
        # attempted to clean up temporary data for the file being processed at the moment of interruption.
        print("Cleanup for the currently processed file should have been attempted. Exiting script.")
        status_message = "Execution interrupted by user."

    except Exception as e_global: # Catch any other unexpected global errors
        print(f"\n!!! An unexpected global error occurred: {e_global} !!!")
        traceback.print_exc()
        status_message = f"Global error: {e_global}"

    finally:
        # This message will print for normal completion, KeyboardInterrupt, or other unhandled exceptions.
        print("Script execution finished or was terminated.")
        # If start_time was defined (i.e., try block was entered)
        if 'start_time' in locals() and 'end_time' not in locals(): # If interrupted before normal finish
            interrupted_time = time.time()
            print(f"Script ran for {interrupted_time - start_time:.2f} seconds before termination.")
