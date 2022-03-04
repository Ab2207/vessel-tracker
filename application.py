import imaplib

import pandas as pd
from datetime import datetime
from vesseflfinderapi import VesselFinderApi
from exceptions import ApiErrorException
from apscheduler.schedulers.background import BackgroundScheduler as scheduler
import folium
from flask import Flask, render_template
from waitress import serve

v = VesselFinderApi(userkey='WS-5B857566-76490B')


# class VesselTracking:
#
#     def __init__(self):
#         pass

def get_data():
    try:
        vessels = v.vessels(mmsi=[538002747, 477776200, 215134000, 235479000, 255806430, 636018541, 371274000, 477652300, 636021449, 636020684,
                                 351848000, 566959000, 229464000], imo=None)
        # mmsi=[376184000, 244023406, 271001031, 244554000, 567057400, 244670094,215748000, 229742000, 227704490,
        # 224176340]

        cols = vessels[0]["AIS"].keys()
        result = []
        # date_time = str(datetime.now().strftime("%Y_%m_%d-%I%M%S%p"))

        for i in range(len(vessels)):
            extracted_data = vessels[i]["AIS"].values()
            result.append(extracted_data)
        df = pd.DataFrame(result, columns=cols)
        # file_name = 'vesselLocation_{}.csv'.format(date_time)
        # output_data = df.to_csv(file_name)
        return df

    except ApiErrorException as e:
        print(e)


# def select_marker_color(row):
#     if row['DISTANCE_REMAINING'] > 0:
#         return 'blue'
#     return 'red'
#
#
# get_data()['color'] = get_data().apply(select_marker_color, axis=1)

application = Flask(__name__)


@application.route("/")
def plot_map():
    world_map = folium.Map(location=[13.133932434766733, 16.103938729508073],
                           zoom_start=2,
                           tiles="Cartodb Positron")

    for _, data in get_data().iterrows():
        url = "www.https://www.vesselfinder.com/vessels/{NAME}-MMSI-{MMSI}".format(NAME=data['NAME'],
                                                                                   MMSI=data['MMSI'])
        folium.Marker(location=[data['LATITUDE'], data['LONGITUDE']],
                      tooltip=data['NAME'],
                      popup=folium.Popup("<strong>MMSI:     </strong>{MMSI}<br>"
                                         "<strong>Location:     </strong>{LATITUDE},{LONGITUDE}<br>"
                                         "<strong>Current Speed:        </strong>{SPEED}<br>"
                                         "<strong>Destination:      </strong>{DESTINATION}<br>"
                                         "<strong>Distance Left:        </strong>{DISTANCE_REMAINING}<br>"
                                         "<strong>ETA:      </strong>{ETA}<br>"
                                         "<strong>Last Reported:        </strong>{TIMESTAMP}<br>"
                                         "<strong>Link:     </strong>{URL}<br>".
                                         format(NAME=data['NAME'], SPEED=data['SPEED'], MMSI=data['MMSI'],
                                                DESTINATION=data['DESTINATION'], ETA=data['ETA'],
                                                ETA_PREDICTED=data['ETA_PREDICTED'], URL=url,
                                                TIMESTAMP=data['TIMESTAMP'], LATITUDE=data['LATITUDE'],
                                                LONGITUDE=data['LONGITUDE'], IMO=data['IMO'],
                                                DISTANCE_REMAINING=data['DISTANCE_REMAINING']), max_width=350,
                                         min_width=350),
                      icon=folium.Icon(color='red', prefix='fa', icon='ship')
                      ).add_to(world_map)

    # return world_map.save('map.html')
    return world_map._repr_html_()


if __name__ == "__main__":
    application.run(host='0.0.0.0', port=8080)
    #serve(app, host='0.0.0.0', port=80)

get_data()
plot_map()

sch = scheduler()
sch.add_job(get_data, 'interval', seconds=3600)
sch.add_job(plot_map, 'interval', seconds=3600)
sch.start()

try:
    print('Scheduler started, ctrl-c to exit!')
    while 1:
        # pass
        input()
except KeyboardInterrupt:
    if sch.state:
        sch.shutdown()
