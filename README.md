# spikesort_docker: A SpikeSort Command Line Tool in Docker

**spikesort_docker** is a Python‐based command line tool that performs spike sorting on electrophysiological recordings using the [SpikeInterface](https://github.com/SpikeInterface) framework. The tool processes recording files by applying bandpass filtering, whitening, spike sorting (via Kilosort4), waveform extraction, and finally exporting the results to Phy for manual curation. It provides full parameter control through command line arguments.

> **Note:** This tool is designed to be run within a Docker container. A Windows batch file (`spikesort.bat`) is provided to launch the container interactively so that you can input all the command line parameters.

---

## Requirements

- **Python 3.12**
- **Conda** (recommended for environment/version management)
- Required Python packages:
  - `spikeinterface==0.102.1`
  - `kilosort==4.0.30`

---

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/padillacoreanolab/spikesort_docker.git
   cd spikesort_docker
   ```

2. **Install Dependencies:**

   It is recommended to use Conda for reproducibility. For example:

   ```bash
   conda create -n spikesort python=3.12 --yes
   conda activate spikesort
   pip install -r requirements.txt
   ```

---

## How to Run

### Running via Docker Using the Batch File

The provided **spikesort.bat** file pulls the latest Docker image, stops any running container with the same name, and then launches a new container in interactive mode. Inside the container, the Conda environment is automatically activated and your custom parameters are passed to the `app.py` script.

**Example of the Batch File (`spikesort.bat`):**

**Key Points:**

- The batch file prompts you for every command line parameter available.
- For the `--output-folder`, if you press Enter without typing anything, it defaults to the current directory (`.`).
- The host data folder is mounted to `/spikesort` in the container.
- Inside the container, the script automatically sources the Conda initialization script, activates the `spikesort` environment, and runs `app.py` with the provided parameters.

### Running Without the Batch File

If you prefer to run the tool manually, you can run the Docker container interactively:

1. **Run the Container:**

   ```bash
   docker run -it --rm --name spikesort_c --gpus all -v "/path/to/your/data:/spikesort" padillacoreanolab/spikesort:latest bash
   ```

2. **Inside the Container:**

   The container drops you into a shell. Activate the Conda environment and run the tool with your parameters:

   ```bash
   source /opt/miniconda3/etc/profile.d/conda.sh
   conda activate spikesort
   python app.py --data-folder /spikesort --output-folder . [other parameters...]
   ```

---

## Command Line Arguments

The tool offers a wide range of configurable parameters. Below is a summary of the available arguments:

### Input and Probe Configuration

- **`--data-folder`** (Required):  
  Path to the folder containing recording files (searched recursively).

- **`--output-folder`** (Optional):  
  Directory where processed output will be saved (default: current directory `.`).

- **`--prb-file`** (Optional):  
  Path to a `.prb` file for probe configuration. If not provided, a default probe file is used.

- **`--disable-batch`** (Optional):  
  When set (true/false), only one recording file will be processed (batch processing disabled).

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
  JSON string to override default sorting parameters (e.g., `{"parameter_name": value}`).  
  Defaults to an empty JSON object (`{}`).

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

---

## Process Overview

1. **Loading & Probe Configuration:**  
   The tool loads recording files and attaches a probe configuration from a provided `.prb` file or a default file.

2. **Preprocessing:**  
   Recordings are bandpass filtered and whitened before spike sorting.

3. **Spike Sorting:**  
   Spike sorting is performed using Kilosort4. GPU availability is automatically detected (unless overridden with `--force-cpu`).

4. **Waveform Extraction:**  
   Extracts waveforms from the sorted data using pre- and post-spike intervals defined by `--ms-before` and `--ms-after`.

5. **Phy Export:**  
   Exports the sorted results and extracted waveforms to a format compatible with Phy for manual curation.

6. **Output Handling:**  
   Processed data is saved into organized subdirectories (e.g., `proc`, `ss_output`, `phy`), and recordings that have already been processed are skipped to avoid duplication.

---

## File Structure Overview

- **`app.py`**  
  Contains the Python code that manages the spike sorting process.

- **`Dockerfile`**  
  Defines the steps to build the Docker image, including setting up the Conda environment and installing required packages.

- **`nancyprobe_linearprobelargespace.prb` (or `.txt`)**  
  A default example probe configuration file required for spike sorting.

- **`spikesort.bat`**  
  A Windows batch file that logs into Docker, pulls the latest image, prompts for all command line parameters, and then launches a Docker container that runs `app.py`. This is the primary file for running the tool on Windows with Docker installed.

- **`synapse-spike.ico`**  
  An icon file that can be used when creating a desktop shortcut for `spikesort.bat`.

---

## Building and Pushing the Docker Image

Whenever changes are made to the code (especially in `app.py`), you must rebuild and push the Docker image so that local runs (via `spikesort.bat`) use the updated version.

1. **Build the Docker Image:**

   ```bash
   docker build --no-cache -t spikesort:latest .
   ```

2. **Tag the Docker Image:**

   ```bash
   docker tag spikesort padillacoreanolab/spikesort:latest
   ```

3. **Push the Docker Image to Docker Hub:**

   ```bash
   docker push padillacoreanolab/spikesort:latest
   ```

Alternatively, you can run the provided update script:

```bash
bash update_docker_image.sh
```

When running the `spikesort.bat` file, the Docker image is pulled/updated from Docker Hub and a container is spun up with your local data folder mounted at `/spikesort`.

---

## Running on HiperGator

To run the tool on HiperGator:

1. **Create the Conda Environment:**

   ```bash
   conda create -n spikesort python=3.12 --yes
   conda activate spikesort
   pip install spikeinterface==0.102.1
   pip install kilosort==4.0.30
   ```

2. **Clone or Copy the Repository to HiperGator.**

3. **Copy Data from Dropbox Using rclone.**

4. **Run the Tool:**

   Use the `app.py` file from the command line as usual, supplying your parameters.

### Running the old version on HiperGator

1. **Create the Conda Environment:**

   ```bash
   conda create -n spikesort python=3.9 --yes
   conda activate spikesort
   pip install spikeinterface[full,widgets]==0.97.1
   pip install --upgrade mountainsort5
   pip install pytest-shutil
   conda install -c edeno spectral_connectivity --yes
   conda install -c anaconda gitpython -y
   conda install -c conda-forge gradio -y
   pip install chardet
   pip install cchardet
   ```
2. **Clone or Copy the Repository to HiperGator.**
  OR you could only copy the old_app.py file and the appropriate .prb file. These two are all that is required to run.

4. **Copy Data from Dropbox Using rclone.**

5. **Run the Tool:**

   Use the `old_app.py` file from the command line as follows.
```bash
conda activate spikesort
python old_app.py <source folder coantaining all .rec files> <output directory where the spikesortedo outputs should be saved>
```

   
---

## Credits

Code was written by [@ChristopherMarais](https://github.com/ChristopherMarais). For any questions or support, please contact him.

```

---
