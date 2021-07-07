lsl-openvr-acceleration-extraction
=================================
This project was created to function asa stremi outlet for LabStreamingLayers to send head mounted device accelerations to a LabStreamingLayer Stream Inlet.

***
Dependencies
---------------------------------
Dependencies:
* Python3 [Go to download page for python](https://www.python.org/downloads/)
* SteamVR [Go to download page for SteamVR](https://store.steampowered.com/app/250820/SteamVR/)
* LabRecorder [Go to LabRecorder github page to download](https://github.com/labstreaminglayer/App-LabRecorder/releases)

To install dependencies `pip install pylsl openvr psutil numpy`

***
How to use
---------------------------------
Start by aquiring the repository. For example: `git clone https://github.com/6Kwecky6/lsl-openvr-acceleration-extraction.git`, then in terminal move into the project folder: `cd <project folder>/lsl-openvr-acceleration-extraction/`.

To start the script with default parameters, use `py main.py <-f/--frame_rate _number_> <-b/--batch_size _number_>`. Once the stream outlet is running, use LabRecorder and add the outlet to the stream inlet.
### Parameters
If no parameter is given, will use default instead
* __-f__/__--frame_rate__ --> Followed by a number (float or int) this will be the sample rate that the script uses. _Default: 60_
* __-b__/__--batch_size__ --> Should be followed by an integer that will represent the bulk size of each LabStreamingLayer package. If set to 1, will use sample-wise package sending. _Default: 1_  __Warning:__ Bulk-wise package sending is untested
