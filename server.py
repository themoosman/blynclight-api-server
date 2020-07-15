#!/usr/bin/python

import logging
import sys
import os
import configparser
from blynclightrunner import BlyncLightRunner
from flask import Flask, jsonify, request, json
from flask_restful import abort
from functools import wraps


#from systemd.journal import JournaldLogHandler

app = Flask(__name__)
logger = logging.getLogger(__name__)
light = BlyncLightRunner(logger)

# color_name
# curl http://localhost:8080/api/v1/color_name -d '{"color_name" : "red"}' -H 'Content-Type: application/json'
# curl http://localhost:8080/api/v1/color_name


# flash
# curl http://localhost:8080/api/v1/flash -d '{"flash" : false}' -H 'Content-Type: application/json'
# curl http://localhost:8080/api/v1/flash

# dim
# curl http://localhost:8080/api/v1/dim -d '{"dim" : false}' -H 'Content-Type: application/json'
# curl http://localhost:8080/api/v1/dim

# on
# curl http://localhost:8080/api/v1/on -d '{"on" : true}' -H 'Content-Type: application/json'
# curl http://localhost:8080/api/v1/on -d '{"on" : true}' -H 'Content-Type: application/json'
# curl http://localhost:8080/api/v1/on

# speed
# curl http://localhost:8080/api/v1/speed -d '{"speed" : 0}' -H 'Content-Type: application/json'
# curl http://localhost:8080/api/v1/speed


# curl http://localhost:8080/api/v1/color -d '{"color_name":"blue"}' -H 'Content-Type: application/json'

@app.route('/api/v1/healthz', methods=['GET'])
def healthz():
    response = jsonify({'status': 'okay'})
    response.status_code = 200
    return response


@app.route('/api/v1/dim', methods=['GET', 'POST'])
def dim():
    key = "dim"
    if request.method == 'GET':
        pass
    if request.method == 'POST':
        handle_post_request(request)

        light.dim = request.json.get('dim', False)

    j = {key: json.dumps(light.dim)}
    response = jsonify(j)
    response.status_code = 200
    return response


@app.route('/api/v1/speed', methods=['GET', 'POST'])
def speed():
    key = "speed"
    if request.method == 'GET':
        pass
    if request.method == 'POST':
        handle_post_request(request)

        speed = request.json.get('speed', 4)
        if speed > 4 or speed < 0:
            abort(400, msg='Invalid parameter value')

        light.flashspeed = speed

    j = "{'" + key + "': " + str(light.flashspeed) + "}"
    response = jsonify(j)
    response.status_code = 200
    return response


@app.route('/api/v1/flash', methods=['GET', 'POST'])
def flash():
    key = "flash"
    if request.method == 'GET':
        pass
    if request.method == 'POST':
        handle_post_request(request)

        b = request.json.get('flash', False)
        logger.debug("flash: " + str(b))
        light.flash = int(b == True)

    j = "{'" + key + "': " + json.dumps(bool(light.flash)) + "}"
    response = jsonify(j)
    response.status_code = 200
    return response


@app.route('/api/v1/color_name', methods=['GET', 'POST'])
def color():
    key = "color_name"
    if request.method == 'GET':
        pass
    if request.method == 'POST':
        handle_post_request(request)

        color_name = request.json.get('color_name', None)
        if not color_name:
            abort(400, error='Missing color_name')

        light.colorname = color_name

    j = {key: str(light.colorname)}
    response = jsonify(j)
    response.status_code = 200
    return response


@app.route('/api/v1/on', methods=['GET', 'POST'])
def on():
    key = "on"
    if request.method == 'GET':
        pass
    if request.method == 'POST':
        handle_post_request(request)

        on = request.json.get('on', False)
        force = request.json.get('force', False)

        if(light.on == on and not force):
            logger.debug("Light status matches, run status.  Nothing will be done.")
        else:
            light.on = on

    j = "{'" + key + "': " + json.dumps(light.on) + "}"
    response = jsonify(j)
    response.status_code = 200
    return response


def handle_post_request(request):
    if not request.is_json:
        logger.error("Request is no in JSON format.")
        abort(400, msg='Missing JSON in request')


def get_http_exception_handler(app):
    """Overrides the default http exception handler to return JSON."""
    handle_http_exception = app.handle_http_exception

    @wraps(handle_http_exception)
    def ret_val(exception):
        exc = handle_http_exception(exception)
        return jsonify({'code': exc.code, 'msg': exc.description}), exc.code
    return ret_val


# App entry point.
if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('config.ini')
    serverconfig = config['server']
    globalconfig = config['global']

    # setup logging
    log_datefmt = '%m-%d-%Y %H:%M:%S'
    log_fmt = '%(asctime)-15s %(levelname)-8s %(message)s'
    log_level = logging.getLevelName(serverconfig.get('log_level', globalconfig.get('log_level', 'INFO')))
    log_file = serverconfig.get('server_log_file')

    if "TTY" in os.environ:
        logging.basicConfig(format=log_fmt, datefmt=log_datefmt, level=log_level)
    else:
        if sys.stdout.isatty():
            # Connected to a real terminal - log to stdout
            logging.basicConfig(format=log_fmt, datefmt=log_datefmt, level=log_level)
        else:
            # Background mode - log to file
            logging.basicConfig(format=log_fmt, datefmt=log_datefmt, level=log_level, filename=log_file)

    logger.info("==========================================================")
    logger.info("Starting Blync Light Server")
    # Server Properties
    app.debug = serverconfig.getboolean('server_debug', False)
    app.handle_http_exception = get_http_exception_handler(app)
    # Finally start the web process and list on 8080 all IP addresses
    app.run(host='0.0.0.0', port=8080)
