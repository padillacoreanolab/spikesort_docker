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
set /p SORT_PARAMS="Enter --sort-params (JSON string, e.g., {\"param\":123}) (default: {}): "
set /p FORCE_CPU="Enter --force-cpu (true/false): "
set /p MS_BEFORE="Enter --ms-before (default 1): "
set /p MS_AFTER="Enter --ms-after (default 1): "
set /p N_JOBS="Enter --n-jobs (default 8): "
set /p TOTAL_MEMORY="Enter --total-memory (default '1G'): "
set /p COMPUTE_PC_FEATURES="Enter --compute-pc-features (true/false) (default: True): "
set /p COMPUTE_AMPLITUDES="Enter --compute-amplitudes (true/false) (default: True): "

:: Convert backslashes to forward slashes if variables are not empty
if not "%HOST_DATA_FOLDER%"=="" set "HOST_DATA_FOLDER=%HOST_DATA_FOLDER:\=/%"
if not "%OUTPUT_FOLDER%"=="" set "OUTPUT_FOLDER=%OUTPUT_FOLDER:\=/%"
if not "%PRB_FILE%"=="" set "PRB_FILE=%PRB_FILE:\=/%"
if not "%RECORDING_FILE%"=="" set "RECORDING_FILE=%RECORDING_FILE:\=/%"

:: Set default values if inputs are empty
if "%OUTPUT_FOLDER%"=="" set "OUTPUT_FOLDER=."
if "%STREAM_ID%"=="" set "STREAM_ID=trodes"
if "%FREQ_MIN%"=="" set "FREQ_MIN=300"
if "%FREQ_MAX%"=="" set "FREQ_MAX=6000"
if "%WHITEN_DTYPE%"=="" set "WHITEN_DTYPE=float32"
if "%SORT_PARAMS%"=="" set "SORT_PARAMS={}"
if "%MS_BEFORE%"=="" set "MS_BEFORE=1"
if "%MS_AFTER%"=="" set "MS_AFTER=1"
if "%N_JOBS%"=="" set "N_JOBS=8"
if "%TOTAL_MEMORY%"=="" set "TOTAL_MEMORY=1G"
if "%COMPUTE_PC_FEATURES%"=="" set "COMPUTE_PC_FEATURES=True"
if "%COMPUTE_AMPLITUDES%"=="" set "COMPUTE_AMPLITUDES=True"

:: Process boolean parameters for DISABLE_BATCH and FORCE_CPU.
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

:: Process optional arguments that expect a value.
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

:: Run Docker with both data and output folders mounted.
:: Note: The added "chmod -R 777 /output &&" ensures that /output is writable.
docker run --rm -it --name spikesort_c --gpus all --log-driver=json-file -v "%HOST_DATA_FOLDER%:/spikesort" -v "%OUTPUT_FOLDER%:/output" padillacoreanolab/spikesort:latest bash -c "chmod -R 777 /output && source /root/miniconda3/etc/profile.d/conda.sh && conda activate spikesort && python app.py --data-folder /spikesort --output-folder \"/output\" %PRB_ARG% %DISABLE_ARG% %REC_ARG% --stream-id \"%STREAM_ID%\" --freq-min \"%FREQ_MIN%\" --freq-max \"%FREQ_MAX%\" --whiten-dtype \"%WHITEN_DTYPE%\" --sort-params \"%SORT_PARAMS%\" %FORCE_ARG% --ms-before \"%MS_BEFORE%\" --ms-after \"%MS_AFTER%\" --n-jobs \"%N_JOBS%\" --total-memory \"%TOTAL_MEMORY%\" --compute-pc-features \"%COMPUTE_PC_FEATURES%\" --compute-amplitudes \"%COMPUTE_AMPLITUDES%\""

echo.
echo Container finished. Press any key to exit...
pause
