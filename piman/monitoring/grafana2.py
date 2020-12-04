from sys import argv
import json
from datetime import datetime
from calendar import timegm
from bottle import (Bottle, HTTPResponse, run, request, response,
                    json_dumps as dumps)

app = Bottle()

log_path = "logs/monitor.log"
DATA = {}

def parse():
    try:
        DATA.clear()
        objlist = [json.loads(line) for line in open(log_path, "r")]
        for obj in objlist:
            time = data_time_to_ms(obj["time"])
            cpu_percent = obj["cpu_percent"]
            memory_percent = obj["memory_percent"]
            disk_percent = obj["disk_percent"]
            num_pids = obj["num_pids"]
            temp = obj["temp"]
            ip = obj["ip"]

            if ip + " CPU LOAD" not in DATA:
                DATA[ip + " CPU LOAD"] = [[cpu_percent, time]]

            else:
                DATA[ip + " CPU LOAD"].append([cpu_percent, time])

            if ip + " MEM USG" not in DATA:
                DATA[ip + " MEM USG"] = [[memory_percent, time]]

            else:
                DATA[ip + " MEM USG"].append([memory_percent, time])

            if ip + " DISK USG" not in DATA:
                DATA[ip + " DISK USG"] = [[disk_percent, time]]

            else:
                DATA[ip + " DISK USG"].append([disk_percent, time])

            if ip + " NUM PIDS" not in DATA:
                DATA[ip + " NUM PIDS"] = [[num_pids, time]]

            else:
                DATA[ip + " NUM PIDS"].append([num_pids, time])
            if ip + " TEMP" not in DATA:
                DATA[ip + " TEMP"] = [[temp, time]]

            else:
                DATA[ip + " TEMP"].append([temp, time])

        return True
    except Exception as e:
        print(e)
        return False


def data_time_to_ms(timestamp):
    return 1000 * timegm(
        datetime.strptime(
            timestamp, '%a %b %d %H:%M:%S %Y').timetuple())  # Fri Oct 30 19:14:52 2020

def convert_to_time_ms(timestamp):
    return 1000 * timegm(
        datetime.strptime(
            timestamp, '%Y-%m-%dT%H:%M:%S.%fZ').timetuple())


def create_data_points(data, start, end):
    lower = convert_to_time_ms(start)
    upper = convert_to_time_ms(end)

    times = list(data.keys()) + [lower, upper]

    results = []
    to_enter = 0
    for time in sorted(times):
        if time in list(data.keys()):
            results.append([to_enter, time - 1])
            results.append([data[time], time])
            to_enter = data[time]
        else:
            results.append([to_enter, time])

    print(results)
    return results


@app.hook('after_request')
def enable_cors():
    print("after_request hook")
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = \
        'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'


@app.route("/", method=['GET', 'OPTIONS'])
def index():
    return "OK"


@app.post('/search', method=['POST', 'GET'])
def search():
    return HTTPResponse(body=dumps(sorted(list(DATA.keys()))),
                        headers={'Content-Type': 'application/json'})


@app.post('/query', method=['POST', 'GET'])
def query():
    try:
        parse()
        body = []
        start, end = request.json['range']['from'], request.json['range']['to']
        for target in request.json['targets']:
            name = target['target']
            parse()
            #datapoints = create_data_points(DATA[name], start, end)
            datapoints = sorted(DATA[name], key = lambda x : x[1])
            body.append({'target': name, 'datapoints': datapoints})

        body = dumps(body)
    except Exception as e:
        print(e)

    return HTTPResponse(body=body,
                        headers={'Content-Type': 'application/json'})


if __name__ == '__main__':
    if len(argv) > 1:
        log_path = argv[1]

    if parse():
        run(app=app, host='', port=8081)
