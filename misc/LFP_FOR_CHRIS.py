# Bandpass Filtering, keeping all the points that are within a certain frequency range
recording_bandpass = spikeinterface.preprocessing.bandpass_filter(recording_intermediate, freq_min=0.5, freq_max=300)

# Notch Filtering, keeping all the points that are within a certain frequency range
recording_notch = spikeinterface.preprocessing.notch_filter(recording_bandpass, freq=60)

# We are not going to run the resampling step because it causes issues with saving to file
# Resampling
recording_resample = spikeinterface.preprocessing.resample(recording_notch, resample_rate=1000)

recording_intermediate.save_to_folder(name="lfp_preprocessing", folder=preprocessing_output_directory, n_jobs=8)