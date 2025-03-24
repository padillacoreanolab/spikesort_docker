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
set /p OUTPUT_FOLDER="Enter --output-folder (directory for processed output) (default: .): "
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

:: Process boolean parameters:
:: For store_true flags, only include the flag if the user enters "true" (ignoring case).
if /i "%DISABLE_BATCH%"=="true" (
    set "DISABLE_ARG=--disable-batch"
) else (
    set "DISABLE_ARG="
)
if /i "%FORCE_CPU%"=="true" (
    set "FORCE_ARG=--force-cpu"
) else (
    set "FORCE_ARG="
)
if /i "%REMOVE_IF_EXISTS%"=="true" (
    set "REMOVE_ARG=--remove-if-exists"
) else (
    set "REMOVE_ARG="
)

:: Process optional arguments that expect a value:
if "%PRB_FILE%"=="" (
    set "PRB_ARG="
) else (
    set "PRB_ARG=--prb-file \"%PRB_FILE%\""
)
if "%RECORDING_FILE%"=="" (
    set "REC_ARG="
) else (
    set "REC_ARG=--recording-file \"%RECORDING_FILE%\""
)

echo.
echo Running Docker container with your parameters...

docker run --rm -it --name spikesort_c --gpus all --log-driver=json-file -v "%HOST_DATA_FOLDER%:/spikesort" padillacoreanolab/spikesort:latest bash -c "source /root/miniconda3/etc/profile.d/conda.sh && conda activate spikesort && python app.py --data-folder /spikesort --output-folder \"%OUTPUT_FOLDER%\" %PRB_ARG% %DISABLE_ARG% %REC_ARG% --stream-id \"%STREAM_ID%\" --freq-min \"%FREQ_MIN%\" --freq-max \"%FREQ_MAX%\" --whiten-dtype \"%WHITEN_DTYPE%\" --sort-params \"%SORT_PARAMS%\" %FORCE_ARG% --ms-before \"%MS_BEFORE%\" --ms-after \"%MS_AFTER%\" --n-jobs \"%N_JOBS%\" --total-memory \"%TOTAL_MEMORY%\" --max-spikes-per-unit \"%MAX_SPIKES%\" --compute-pc-features \"%COMPUTE_PC_FEATURES%\" --compute-amplitudes \"%COMPUTE_AMPLITUDES%\" %REMOVE_ARG%"

echo.
echo Container finished. Press any key to exit...
pause
