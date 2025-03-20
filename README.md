# spikesort_docker a SpikeSort Command Line Tool

This Python-based command line tool performs spike sorting on electrophysiological recordings using the [SpikeInterface](https://github.com/SpikeInterface) framework. It processes recording files by applying bandpass filtering, whitening, spike sorting (with Kilosort4), waveform extraction, and finally exporting the results to Phy for manual curation. Full parameter control is provided through command line arguments.

## Requirements

- **Python 3.12**
- Required Python packages:
  - spikeinterface==0.102.1
  - kilosort==4.0.30

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/padillacoreanolab/spikesort_docker.git
   cd spikesort_docker
   ```

2. **Install Dependencies:**

We reccomend using conda for version control.
   ```bash
   pip install -r requirements.txt
   ```

## How to Run

Execute the tool from the command line using the `app.py` script. The only required argument is `--data-folder`, which specifies the path to the folder containing your recording files.

### Basic Example

```bash
python app.py --data-folder "/path/to/recordings"
```

This command recursively searches for recording files (with names ending in `merged.rec`) in the specified folder and processes them in batch mode. The processed output will be saved in the current directory unless you specify another location with `--output-folder`.

## Command Line Arguments

The tool offers a range of configurable parameters:

### Input and Probe Configuration

- **`--data-folder`** (Required):  
  Path to the folder containing recording files (searches recursively).

- **`--output-folder`** (Optional):  
  Directory where processed output will be saved (default: current directory).

- **`--prb-file`** (Optional):  
  Path to a `.prb` file for probe configuration. If not provided, a default probe file is used.

- **`--disable-batch`** (Optional):  
  When set, only one recording file will be processed (batch processing disabled).

- **`--recording-file`** (Optional):  
  Specify a single recording file to process (used when batch processing is disabled).

- **`--stream-id`** (Optional):  
  Stream ID to use when reading recording files (default: `"trodes"`).

### Preprocessing Parameters

- **`--freq-min`** (Optional):  
  Minimum frequency for bandpass filtering (default: `300` Hz).

- **`--freq-max`** (Optional):  
  Maximum frequency for bandpass filtering (default: `6000` Hz).

- **`--whiten-dtype`** (Optional):  
  Data type for whitening (default: `"float32"`).

### Sorting Parameters

- **`--sort-params`** (Optional):  
  JSON string to override default sorting parameters (e.g., `'{"parameter_name": value}'`). Defaults to an empty JSON object (`{}`).

- **`--force-cpu`** (Optional):  
  Forces sorting to run on CPU even if a GPU is available.

### Waveform Extraction Parameters

- **`--ms-before`** (Optional):  
  Milliseconds before spike for waveform extraction (default: `1`).

- **`--ms-after`** (Optional):  
  Milliseconds after spike for waveform extraction (default: `1`).

- **`--n-jobs`** (Optional):  
  Number of jobs for waveform extraction (default: `8`).

- **`--total-memory`** (Optional):  
  Total memory available for waveform extraction (default: `"1G"`).

- **`--max-spikes-per-unit`** (Optional):  
  Maximum spikes per unit for waveform extraction (default: `2000`).

### Phy Export Parameters

- **`--compute-pc-features`** (Optional):  
  Compute PC features for Phy export (default: `True`).

- **`--compute-amplitudes`** (Optional):  
  Compute amplitudes for Phy export (default: `True`).

- **`--remove-if-exists`** (Optional):  
  Remove existing Phy export folder if it exists.

## Example Usages

### Batch Processing of Multiple Recordings

```bash
python app.py --data-folder "/path/to/recordings" --output-folder "/path/to/output"
```

This command searches the specified data folder recursively for files ending with `merged.rec` and processes them in batch.

### Processing a Single Recording

```bash
python app.py --data-folder "/path/to/recordings" --disable-batch --recording-file "/path/to/recordings/sample_merged.rec"
```

This command disables batch processing and explicitly processes the provided recording file.

### Advanced Configuration

```bash
python app.py --data-folder "/path/to/recordings" \
                    --prb-file "/path/to/probe.prb" \
                    --sort-params '{"parameter_name": 123, "another_param": true}' \
                    --force-cpu
```

This command uses a custom probe configuration, overrides default sorter parameters, and forces CPU processing.

## Process Overview

1. **Loading and Probe Configuration:**  
   The tool loads recording files and attaches a probe configuration from a provided `.prb` file or a default file.

2. **Preprocessing:**  
   Recordings are bandpass filtered and whitened before spike sorting.

3. **Spike Sorting:**  
   Spike sorting is performed using Kilosort4. The tool automatically detects GPU availability unless CPU processing is forced.

4. **Waveform Extraction:**  
   Extracts waveforms from the sorted data, with customizable pre- and post-spike intervals.

5. **Phy Export:**  
   Exports the sorted results and waveforms to a format compatible with Phy for further manual curation.

6. **Output Handling:**  
   Processed data is saved in organized subdirectories (e.g., `proc`, `ss_output`, `phy`), and recordings that have already been processed are automatically skipped.

## Additional Information

- **GPU/CPU Detection:**  
  The tool checks for GPU availability and uses it for spike sorting unless overridden by the `--force-cpu` flag.

- **Batch vs. Single File Processing:**  
  By default, the tool processes all recording files found in the data folder. Use `--disable-batch` and `--recording-file` to process a single file.

- **Error Handling:**  
  If a recording has already been processed (e.g., a Phy export folder exists), the tool will skip that recording to avoid duplicate work.

# What does each file do?
* `app.py` - This file contains the python script that handles the process and spike sorting.
* `Dockerfile` - This file controls the building process of building a new docker image.
* `nancyprobe_linearprobelargespace.prb or .txt` - This file represents a default example of the required .prb file that is required to run the spike sorting in the current setup.
* `spikesort.bat` - This file is a script that pulls the docker image and controls the process of spinning up a container from the image. This file also launches the actual python script/app and is what is run when clicking on the shortcut of spike sorting. Technically this is also the only file you need to run the app on a windows machine with docker installed.
* `synapse-spike.ico` - This is just an icon that can be used when creating a shortcut for the `spikesort.bat` file. 

# How to build the docker image and push it to Docker Hub.
Currently this Repo contains the necessary code to build a docker image. The docker image contains a Conda environment wherein a python script is run. The python script that is run is the `app.py` file. This is the file that controls all the processing. When this file is changed a new version of the docker image ahs to be built and pushed to docker Hub before the app works on a local PC. To create the docker image run the following commands from within the spikesort_docker folder in the terminal:
```
# Build the docker Image (--no-cache can be excluded to cache previous builds to speed up the process)
docker build --no-cache -t spikesort:latest .

# Tag the Docker Iamge as the latest version
docker tag spikesort padillacoreanolab/spikesort:latest

# Push the Docker image to DockerHub
docker push padillacoreanolab/spikesort:latest
```
When running the `spikesort.bat` file the docker image is pulled/updated from docker Hub. Thereafter a container is created running the `app.py` file inside the Conda environment from within the container. Note, that the docker image copies all the files in the root folder of this repo over into it when creating the image. When the container of the docker is spun up from the image it links a specified folder on the local computer to a path in the container named `/spikesort`. This should be kept in mind when modifying paths in the `app.py` file.

Or simply run the update_docker_image.sh script:
```bash update_docker_image.sh```

# How to run on HiperGator:
1. Make a conda env for spikesort. It is important to make the envronment and install the packages in the following way. The whole reason we use docker is because the environment is so fragile.
```bash
# Create and activate the conda environment
conda create -n spikesort python=3.12 --yes
conda activate spikesort

# Install required packages
pip install spikeinterface==0.102.1
pip install kilosort==4.0.30
```
2. Clone/Copy this repository on the Hipergator.
3. Copy data from Dropbox to HiperGator using rclone
5. Use the app.py file to run the code in the command line tool as usual.

Code was written by @ChristopherMarais so contact him for any questions
