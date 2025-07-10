import os
import requests
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET
import pandas as pd
import time
from datetime import datetime

url = "https://b2b.promet-info.hr/dc/b2b.hac.trafficData"  
username = "tomislav.krljan@uniri.hr"           
password = "7iq2YaxY"              
specific_ids = ["COUNTER:A7:CAV:171049", "COUNTER:A7:CAV:171050", "COUNTER:A7:CAV:171051", "COUNTER:A7:CAV:171052"]

interval = 300 

#output_folder = "C:/Users/Neven Grubisic/Local/NPT/01/HAC"
output_folder = "C:/Users/tkrljan/Desktop/my-map-platform/pool-data-from-server"

os.makedirs(output_folder, exist_ok=True)

dataframes = {id_: pd.DataFrame(columns=['measurement_time', 'TrafficHeadway', 'TrafficFlow', 'TrafficSpeed', 'TrafficConcentration']) for id_ in specific_ids}

def sanitize_filename(filename):
    return filename.replace(':', '_').replace('/', '_').replace('\\', '_')

while True:
    response = requests.get(url, auth=HTTPBasicAuth(username, password))

    if response.status_code == 200:
        xml_data = response.content

        timestamp = datetime.now().strftime("%d%m%Y-%H%M%S")
        output_file = os.path.join(output_folder, f"data_filtered_{timestamp}.xml")

        root = ET.fromstring(xml_data)
        namespace = {'ns0': 'http://datex2.eu/schema/2/2_0'}
        
        filtered_data = []
        for site_measurement in root.findall('.//ns0:siteMeasurements', namespace):
            measurement_site_ref = site_measurement.find('ns0:measurementSiteReference', namespace)
            if measurement_site_ref is not None:
                detector_id = measurement_site_ref.attrib.get('id')
                if detector_id in specific_ids:
                    filtered_data.append(site_measurement)
                    measurement_time = site_measurement.find('ns0:measurementTimeDefault', namespace).text
                    traffic_headway = traffic_flow = traffic_speed = traffic_concentration = None

                    for measured_value in site_measurement.findall('ns0:measuredValue', namespace):
                        basic_data = measured_value.find('ns0:measuredValue/ns0:basicData', namespace)
                        if basic_data is not None:
                            data_type = basic_data.attrib.get('{http://www.w3.org/2001/XMLSchema-instance}type')
                            if data_type == 'TrafficHeadway':
                                traffic_headway = float(basic_data.find('ns0:averageTimeHeadway/ns0:duration', namespace).text)
                            elif data_type == 'TrafficFlow':
                                traffic_flow = float(basic_data.find('ns0:vehicleFlow/ns0:vehicleFlowRate', namespace).text)
                            elif data_type == 'TrafficSpeed':
                                traffic_speed = float(basic_data.find('ns0:averageVehicleSpeed/ns0:speed', namespace).text)
                            elif data_type == 'TrafficConcentration':
                                traffic_concentration = float(basic_data.find('ns0:concentration/ns0:concentrationOfVehicles', namespace).text)

                    new_data_df = pd.DataFrame([{
                        'measurement_time': measurement_time,
                        'TrafficHeadway': traffic_headway,
                        'TrafficFlow': traffic_flow,
                        'TrafficSpeed': traffic_speed,
                        'TrafficConcentration': traffic_concentration
                    }])

                    dataframes[detector_id] = pd.concat([dataframes[detector_id], new_data_df], ignore_index=True)

        if filtered_data:
            new_root = ET.Element("siteMeasurementsList")
            for data in filtered_data:
                new_root.append(data)

            new_xml_data = ET.tostring(new_root, encoding='utf-8', method='xml')

            with open(output_file, "wb") as file:
                file.write(new_xml_data)
            
            print(f"Filtered XML data successfully downloaded and saved to {output_file}")

        for detector_id, df in dataframes.items():
            sanitized_id = sanitize_filename(detector_id)
            csv_output_file = os.path.join(output_folder, f"{sanitized_id}_data.csv")
            df.to_csv(csv_output_file, index=False)
            print(f"Data for {detector_id} saved to {csv_output_file}")

    else:
        print(f"Failed to download XML data. Status code: {response.status_code}")

    time.sleep(interval)