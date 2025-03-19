# spikesort_docker
A repo that contains all the code and guides for doing basic spike sorting in a containerized terminal app using docker. 

# How to run:
1. Install Docker desktop
2. Launch Docker. Note, that all containers and images can be deleted from docker to reset it if necessary, no need to worry about deleting docker images as everything is backed up and pulled from Docker Hub automatically. 
3. Run the `spikesort.bat` file by double clicking it or run a shortcut of this file (Only works for windows machines, but can be expanded for Unix systems in the future)
4. A command line terminal will run and show the following prompt:
```
FULL PATH TO THE PARENT FOLDER OF THE SPIKESORT DATA FOLDER:
```
Copy and paste the path into the terminal of the folder that contains the `data` folder where all the spikesort input data is located. 
e.g. `C:\Users\Padilla-Coreano\Desktop\GITHUB_REPOS\diff_fam_social_memory_ephys` is a correct example. `C:\Users\Padilla-Coreano\Desktop\GITHUB_REPOS\diff_fam_social_memory_ephys\data` is not.
5. Press `Enter` and let it run.

# Trouble Shooting
Do you keep clicking the spikesort icon and things aren't doing what you want, here are a few trouble shooting options 
- step 1: spike sorting crashed on you half way thru, move sorted data files into a new folder (labeled done or something similar) and rename your proc folder. You do not want to resort already resorted data
- step 2: Open docker app, and try click the Spikesort desk top icon again. 
- step 3: Open the docker app, click the left most icon in the upper right hand corner and restart the docker app. Click spikesort desktop icon and try again. 

  - Specifically if the terminal prints out: 
 FULL PATH TO THE PARENT FOLDER OF THE SPIKESORT DATA FOLDER: "E:\social_mem_ephys_pilot2"
Running Docker Container:  spikesort_c...
docker: Error response from daemon: error while creating mount source path '/run/desktop/mnt/host/e/social_mem_ephys_pilot2': mkdir /run/desktop/mnt/host/e: file exists.
Press any key to continue . . .


.  


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
conda create -n spikesort python=3.9 --yes
conda activate spikesort

# Install required packages
pip install spikeinterface[full,widgets]==0.97.1
pip install --upgrade mountainsort5
pip install pytest-shutil
conda install -c edeno spectral_connectivity --yes
conda install -c anaconda gitpython -y
conda install -c conda-forge gradio -y
pip install chardet
pip install cchardet
```
2. Copy data from Dropbox to HiperGator.
  1. install rclone on your local computer: https://rclone.org/downloads/
  2. run on personal computer 
  ```
  rclone.exe authorize "dropbox"
  ```
  
  crtl + click on link that terminal spits out and press agree, terminal will now spit out a token key, finish step 3 before copying and pasting it into the hipergator terminal
  
  3. open terminal in hipergator and run the following lines: 
  ```
  module load rclone
  rclone config
  ```
  
  - n) New remote
  - name your dropbox
  - Storage > 13 (type 13 (which is dropobx) and hit enter) 
  - leave client_id and client_secret blank (aka press enter) 
  - type n and click enter (No) for edit advanced config
  - type n and click enter (No) for web broswer question
  - copy and paste config token from local terminal into hipergator terminal
  - click y and hit enter for default settings to finish
  
  if authentication breaks press choose: e) Edit existing remote 
  4. find data on dropbox
  ```
  rclone ls pc-dropbox:"Padilla-Coreano Lab/path/to/data"
  ```
  5. copy data from dropdox
  source = pc-dropbox
  path ="path/to/folder"
  run dry run first to confirm path and size of download 
  
  example of destination path
  dest:path = ./data 
  ```
  rclone copy source:path dest:path --progress --dry-run
  ```
  then run it for reals
  ```
  rclone copy source:path dest:path --progress
  ```
  
  example real command:
  ```
  rclone copy pc-dropbox:"Padilla-Coreano Lab/2024/Cum_SocialMemEphys_pilot2/Habituation_Dishabituation (phase 1)/data/cagemate" ./cagemate --progress --dry-run
  ```
  
  or to upload data to dropbox: 
  
  ```
  rclone copy ./same_lfp pc-dropbox:"Padilla-Coreano Lab/2024/Cum_SocialMemEphys_pilot2/Same_Diff (phase2)/lfp_data" --progress --dry-run
  ```
3. Use the app.py file to run the code in the command line tool.

# Proposed Possible Changes:
* Use the [PHY2_Shortcut](https://github.com/padillacoreanolab/PHY2_shortcuts) as an example to run this app outside docker.
* Use a Params.py file to give more various inputs to the processing functions.
* Change it to be a command line run function with additional parameters.
* Update the `app.py` file so that it is not as dependent on the /data/ folder and needs it as a requirement.
* Add the default .prb file parameters directly into the code as a default for a .prb parameter.
* It should have a parameter to disable batch processing.
* It should not reprocess files when their results already exist in the output folder.

Code was written by @ChristopherMarais so contact him for any questions
