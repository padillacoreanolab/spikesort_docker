import os
import shutil
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import spikeinterface as si  # import core only
import spikeinterface.extractors as se
import spikeinterface.preprocessing as sp
import spikeinterface.widgets as sw
import spikeinterface.full as si
import mountainsort5 as ms5
from matplotlib.pyplot import cm
from spikeinterface.exporters import export_to_phy
from probeinterface import get_probe
from probeinterface.plotting import plot_probe, plot_probe_group
from probeinterface import write_prb, read_prb
from pathlib import Path


def read_camera_module_time_stamps(filename):
    # Open the file in binary mode
    with open(filename, 'rb') as f:
        # Read the header of the file to determine the clock rate
        header = f.read(200).decode('latin-1')
        end_header_loc = header.find('<End settings>')
        if end_header_loc != -1:
            headersize = end_header_loc + 14
            clock_rate_loc = header.find('Clock rate:')
            if clock_rate_loc != -1:
                clock_rate = int(header[clock_rate_loc + 12:].split()[0])
            else:
                clock_rate = 30000
        else:
            headersize = 0
            clock_rate = 30000

        # Read the timestamps from the file
        f.seek(headersize)
        timestamps = np.fromfile(f, dtype=np.uint32)

    return timestamps, clock_rate


def spikesort():
    pwd = os.getcwd() + "/spikesort"  # r"C:\Users\Padilla-Coreano\Desktop\GITHUB_REPOS\diff_fam_social_memory_ephys"
    print(pwd)
    prb_file_path = Path(f"{pwd}/data/nancyprobe_linearprobelargespace.prb")
    probe_object = read_prb(prb_file_path)
    probe_df = probe_object.to_dataframe()  # ???
    print(probe_df)
    recording_filepath_glob = str(Path(f"{pwd}/data/**/*merged.rec"))
    all_recording_files = glob.glob(recording_filepath_glob, recursive=True)

    for recording_file in all_recording_files:
        # read in files
        trodes_recording = se.read_spikegadgets(recording_file, stream_id="trodes")       
        trodes_recording = trodes_recording.set_probes(probe_object)
        
        # get paths and directories
        recording_basename = os.path.basename(recording_file)
        recording_output_directory = str(Path(f"{pwd}/proc/{recording_basename}"))
        os.makedirs(recording_output_directory, exist_ok=True)
        child_spikesorting_output_directory = os.path.join(recording_output_directory, "ss_output")
        child_recording_output_directory = os.path.join(recording_output_directory, "preprocessed_recording_output")
        child_lfp_output_directory = os.path.join(recording_output_directory, "lfp_preprocessing_output")

        print("Calculating LFP...")
        # Make sure the recording is preprocessed appropriately
        # lazy preprocessing
        recording_filtered = sp.bandpass_filter(trodes_recording, freq_min=300, freq_max=6000)
        # Do LFP
        # Notch Filtering, keeping all the points that are within a certain frequency range
        recording_notch = sp.notch_filter(recording_filtered, freq=60)
        # We are not going to run the resampling step because it causes issues with saving to file?
        # Resampling
        # recording_resample = sp.resample(recording_notch, resample_rate=1000)
        print("Saving LFP result...")
        recording_notch.save_to_folder(name="lfp_preprocessing", folder=child_lfp_output_directory, n_jobs=8)
        print("Spikesorting preprocessing...")
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
        print("Saving variables...")
        spike_sorted_object_disk = spike_sorted_object.save(folder=child_spikesorting_output_directory) # ???
        recording_preprocessed_disk = recording_preprocessed.save(folder=child_recording_output_directory) # ???

        sw.plot_rasters(spike_sorted_object)
        plt.title(recording_basename)
        plt.ylabel("Unit IDs")

        plt.savefig(os.path.join(recording_output_directory, f"{recording_basename}_raster_plot.png"))
        plt.close()

        waveform_output_directory = os.path.join(recording_output_directory, "waveforms")

        print("Extracting Waveforms...")
        we_spike_sorted = si.extract_waveforms(recording=recording_preprocessed_disk, 
                                        sorting=spike_sorted_object_disk, 
                                        folder=waveform_output_directory,
                                        ms_before=1, 
                                        ms_after=1, 
                                        progress_bar=True,
                                        n_jobs=8, 
                                        total_memory="1G", 
                                        overwrite=True,
                                        max_spikes_per_unit=2000)

        # remove temp folder
        for filename in os.listdir(child_recording_output_directory):
            file_path = os.path.join(child_recording_output_directory, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))


        phy_output_directory = os.path.join(recording_output_directory, "phy")
        print("Saving PHY2 output...")
        export_to_phy(we_spike_sorted, 
                      phy_output_directory,
                      compute_pc_features=True, 
                      compute_amplitudes=True, 
                      remove_if_exists=False)
        print("PHY2 output Saved!")

        # edit the params.py file os that it contains the correct realtive path
        params_dir = os.path.join(phy_output_directory, "params.py")
        with open(params_dir, 'r') as file:
            lines = file.readlines()
        lines[0] = "dat_path = r'./recording.dat'\n"
        with open(params_dir, 'w') as file:
            file.writelines(lines)

        # do timestamp processing
        data_folder_path = Path(f"{pwd}/data/")
        files = os.listdir(data_folder_path)
        videoTimeStamps_files = [f for f in files if f.endswith('.videoTimeStamps')]
        if len(videoTimeStamps_files) == 1:
            arr = read_camera_module_time_stamps(os.path.join(data_folder_path, videoTimeStamps_files[0]))
            dfs = pd.DataFrame(arr[0])
            dfs.to_csv(os.path.join(recording_output_directory,"timestaps.csv"))
        else:
            raise ValueError('There should be only one csv file in the folder')

    return "SPIKES ARE SORTED & LFP DONE! :)"


if __name__ == "__main__":
    spikesort()

# code used for web gui
# input_text = gr.inputs.Textbox(label="Enter folder path")
# output_text = gr.outputs.Textbox(label="Status")
# interface = gr.Interface(fn=spikesort, inputs=input_text, outputs=output_text)
# interface.launch(server_name="0.0.0.0", server_port=7000)
