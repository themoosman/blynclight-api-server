# BlyncLight API Server
This is an BlyncLight API Server for the [Embrava BlyncLight](https://embrava.com/collections/blynclight-series).  This is intended to make the BlyncLight a network light and have its status updated by simple Rest calls.  I wrote this server and client so my workstation (client) can monitor my headset and webcamera and update the light accordingly.

## Why
During the shelter in place here in the USA during the COVID-19 outbreak, I was forced to work from home.  This light and client / server become required to signal other family members that I was on a conference call.  I hope this can help you out as well.

## Requirements
This application uses the [BusyLight for Humans](https://pypi.org/project/busylight-for-humans/) Python package to make the device calls.


## Server
The server is a simple Flask Rest API that updates the light or status by issuing simple calls.  This allows for a client to be implemented in just about any language.

### Example Server Calls

Get the current light color
```bash
curl http://localhost:8080/api/v1/color_name
```

Set the color of the light to Red
```bash
curl http://localhost:8080/api/v1/color_name -d '{"color_name" : "red"}' -H 'Content-Type: application/json'
```

Turn the light on
```bash
curl http://localhost:8080/api/v1/on -d '{"on" : true}' -H 'Content-Type: application/json'
```

## Client

The provided client is a very simple example that does three things.

1. Check to see if the headset is turned on.  I use a Logitech g533, so I can make a call to get the battery status.  This call will fail if the headset is turned off.  If the client finds the headset is off, it will set the light to Green and sleep.
2. If a headset is found or `use_headset_ctrl` is set to `False` then it will check to see if the headset is active.  It does this by `cat /proc/asound/card3/pcm*/sub*/status | grep "RUNNING" | wc -l` if a number > 0 is found the headset is active and it goes to the next step.  If this check returns 0, the light is set to Yellow and the client sleeps.
3. Since the headset is found to be active, the final check is for a webcam.  This is done by `lsof -t /dev/video0 |  wc -l` if the number of rows is > 0 then the webcam is active.  Since the webcam is active the light is set to flash red, if not then the light is set to solid red.  The process then sleeps until the next poll.


## Install

1) Install the necessary Python packages
````bash
python3 -m pip install -r requirements.txt
````

### Services
Both Python apps can be run as services.  See the instructions in the `.service` files for instructions.

### config.ini Overview

The repo does not ship with a `config.ini` so you must copy `config-sample.ini` to `config.ini`

The following table outlines the `config.ini` variables.

#### global

These are the default values for the server and client.  These values can be overridden in the sections below.

| Variable | Description |
| --- | --- |
| `log_level` | Sets the level of logging |
| `use_journald` | Set to true to write logs to journald.  Note: only use this when running as a servcie.  |


#### app

| Variable | Description |
| --- | --- |
| `log_level` | Sets the level of logging |
| `use_journald` | Set to true to write logs to journald.  Note: only use this when running as a servcie.  |
| `client_log_file` | Path to the client log file, only used when journald is disabled and a TTY isn't found |
| `use_headset_ctrl` | Sets if the client will run a precheck to look for the existance of a headset |
| `wait_time` | Sets the poll time |
| `long_wait_time` | Sets a longer wait time that's used when a headset cann't be located |
| `webcam_device` | Location to the webcam |
| `headset_status` | Location to the headset status file |
| `headset_stream` | Location to the headset stream file |
| `api_server` | URL to the server API |


#### server

| Variable | Description |
| --- | --- |
| `log_level` | Sets the level of logging |
| `server_debug` | Sets Flask to run in debug mode |
| `use_journald` | Set to true to write logs to journald.  Note: only use this when running as a servcie.  |
| `server_log_file` | Path to the client log file, only used when journald is disabled and a TTY isn't found |

## TODO

1. Implement a server Rest call that allows all parameters to be set at one time
2. Implement a "dance party" mode
3. Improve client sample
