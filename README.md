
# Gabrino, A Desktop Robot Assistant (WORK IN PROGRESS)



## A robot assistant, capable of communicating with its users, and connecting college students to their family back at home!


This project was built as a gift for my sister, who is leaving for college in a few months. In order to continue the legacy of the annoying little brother,
I built Gabrino. As my sister leaves for college, she can bring Gabrino with her, enabling me to hang out with her, tour UCLA, and annoy her whenever I 
want. I'm not all annoying though, so I built some functions to help her throughout college:


* An INMP441 microphone to capture audio input
* A speaker connected to the MAX98357A amplifier to relay audio back to her 
* An AI assistant to help her answer quick questions and set alarms
* A 1 inch OLED screen to show the time, weather, or any visual indicator
* A connection to a Flask API server, to connect her with me and the assistant
* A high quality camera stream, to bother her whenever I want
* A frontend website, writen with React and Vite to control the robot
* A stationary esp32 wifi gateway for her to control gabrino



## Here's a quick preview of Gabrino
<img src="cad_preview.png" alt="Isn't he adorable" width="180" height="180" border="10" />



## How to recreate Gabrino, using your own CAD design, but same circuitry and code

You will need to purchase all the parts and CAD your own model, but here's the electrical setup.

1. Copy the schematic below. <br/>
<img src="schematic.png" alt="schematic" width="1000" height="1000" border="10"/>

2. Clone this project <br/>
3. Upload the code via [Arduino IDE](https://support.arduino.cc/hc/en-us/articles/360019833020-Download-and-install-Arduino-IDE) <br/>
4. Run the Flask API server <br/>

``` bash
cd server
python3 -m venv ./venv
source venv/bin/activate
pip3 install -r requirements.txt
python3 app.py
```
5. Run the frontend
``` bash
cd frontend
npm run dev
```

## How to use for your own purposes

For all my fellow little brothers out there, cad your own robot, and give it to your sister, so you can annoy her. For fellow
developers, feel free to use my code whether you want to stream audio from the inmp441 to your server, or connect api servers
to hardware projects.








