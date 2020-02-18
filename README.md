# KML Tour Generator
## Overview
Generate camera tours KML files from a target and route (manual/circle).  
This is an proof-of-concept version with minimal capabilities.  

KML supports look-at but we want to calculate the camera.  
This is useful for simulation of data such as KLV (MISB 601).  
The KML is used with Google Earth Pro to generate video.  
Multiplexing of video and KLV is currently beyond the scope of the project. 

## Getting started
The code is written in python and tested with version 3.6.  

Clone the repository:
```bash
git clone https://github.com/Webiks/kml-tour-generator.git
cd kml-tour-generator
```

Setup virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the dependencies:
```bash
pip install -r requirements.txt
```

Run the code:
```bash
python main.py
```

**test2.kml** file should be generated.  
Open the file in Google Earth Pro, see the data and play the tour.
