@echo off
:: Log into Docker
echo Logging into Docker...
docker login
if %errorlevel% neq 0 (
    echo Login failed!
    exit /b %errorlevel%
)

:: Pull the latest Docker image
echo Pulling Latest Version of Image: spikesort...
docker pull padillacoreanolab/spikesort:latest

:: Stop and remove any existing container with the same name
echo Shutting down any existing container named spikesort_c...
docker stop spikesort_c >nul 2>&1
docker rm spikesort_c >nul 2>&1

:: Prompt for all command-line parameters

echo.
set /p HOST_DATA_FOLDER="Enter the full path to the data folder (the folder that contains recording files): "
set /p OUTPUT_FOLDER="Enter --output-folder (directory for processed output): "
set /p PRB_FILE="Enter --prb-file (path to .prb file) or leave blank for default: "
set /p DISABLE_BATCH="Enter --disable-batch (true/false): "
set /p RECORDING_FILE="Enter --recording-file (path to a single recording file) or leave blank: "
set /p STREAM_ID="Enter --stream-id (default 'trodes'): "
set /p FREQ_MIN="Enter --freq-min (default 300): "
set /p FREQ_MAX="Enter --freq-max (default 6000): "
set /p WHITEN_DTYPE="Enter --whiten-dtype (default 'float32'): "
set /p SORT_PARAMS="Enter --sort-params (JSON string, e.g., {\"param\":123}): "
set /p FORCE_CPU="Enter --force-cpu (true/false): "
set /p MS_BEFORE="Enter --ms-before (default 1): "
set /p MS_AFTER="Enter --ms-after (default 1): "
set /p N_JOBS="Enter --n-jobs (default 8): "
set /p TOTAL_MEMORY="Enter --total-memory (default '1G'): "
set /p MAX_SPIKES="Enter --max-spikes-per-unit (default 2000): "
set /p COMPUTE_PC_FEATURES="Enter --compute-pc-features (true/false): "
set /p COMPUTE_AMPLITUDES="Enter --compute-amplitudes (true/false): "
set /p REMOVE_IF_EXISTS="Enter --remove-if-exists (true/false): "

echo.
echo Running Docker container with your parameters...

:: Run Docker container in interactive mode with conda auto-activation and pass the parameters.
docker run --rm -it --name spikesort_c --gpus all --log-driver=json-file -v "%HOST_DATA_FOLDER%:/spikesort" padillacoreanolab/spikesort:latest bash -c "source /opt/miniconda3/etc/profile.d/conda.sh && conda activate spikesort && python app.py --data-folder /spikesort --output-folder %OUTPUT_FOLDER% --prb-file %PRB_FILE% --disable-batch %DISABLE_BATCH% --recording-file %RECORDING_FILE% --stream-id %STREAM_ID% --freq-min %FREQ_MIN% --freq-max %FREQ_MAX% --whiten-dtype %WHITEN_DTYPE% --sort-params \"%SORT_PARAMS%\" --force-cpu %FORCE_CPU% --ms-before %MS_BEFORE% --ms-after %MS_AFTER% --n-jobs %N_JOBS% --total-memory %TOTAL_MEMORY% --max-spikes-per-unit %MAX_SPIKES% --compute-pc-features %COMPUTE_PC_FEATURES% --compute-amplitudes %COMPUTE_AMPLITUDES% --remove-if-exists %REMOVE_IF_EXISTS%"

echo.
echo Container finished. Press any key to exit...
pause
