import psutil
import redis
import time
import uuid
from datetime import datetime
import argparse

# function to connect to Redis 
def connect_to_redis(host, port, user, password):
    r = redis.Redis(
        host=host,
        port=port,
        username=user,
        password=password
    )
    return r

# Checkpoint5: The script is run from the command line interface and should take arguments as input
parser = argparse.ArgumentParser(description='Redis Connection and Operations')
parser.add_argument('--host', type=str, default='redis-15091.c293.eu-central-1-1.ec2.cloud.redislabs.com')
parser.add_argument('--port', type=int, default=15091)
parser.add_argument('--user', type=str, default='default')
parser.add_argument('--password', type=str, default='b7ONthJGA5z0r7FvD005vsv2xmhMK9P4')
args = parser.parse_args()
# conmend line: python3 lab1-ex2.2.py --host redis-15091.c293.eu-central-1-1.ec2.cloud.redislabs.com --port 1509 --user default --password b7ONthJGA5z0r7FvD005vsv2xmhMK9P4


# Creating a Redis client object
redis_client = connect_to_redis(args.host, args.port, args.user, args.password)
#Checking if the connection to Redis is successful
is_connected = redis_client.ping()
print('Redis Connected:', is_connected)

#uuid.getnode() returns the hardware/MAC address 
#hex() converts the hardware address into its hexadecimal representation.
mac_address = hex(uuid.getnode())

# checkpoint3: Set a retention period of 1 day for mac_address:battery and mac_address:power and of 30 days for mac_address:plugged_seconds.
# Set retention period to 1 day (in ms)
retention_period_1day = 24 * 60 * 60 * 1000
# Set retention period to 30 day (in ms)
retention_period_30day = 30 * 24 * 60 * 60 * 1000

# Create a timeseries named'mac_address:battery' with a retention period to 1 day
try:
    redis_client.ts().create(f'{mac_address}:battery',retention_msecs= retention_period_1day)
    print(f'Successfully created time series {mac_address}:battery with a retention time for 1 day')
except redis.ResponseError:
    redis_client.ts().alter(f'{mac_address}:battery',retention_msecs=retention_period_1day)
    # If the time series already exists, update its retention period
    print(f'time series {mac_address}:battery already existed,updated witha retention time for 1 day')
    pass

# Create a timeseries named'mac_address:power' with a retention period to 1 day
try:
    redis_client.ts().create(f'{mac_address}:power',retention_msecs= retention_period_1day)
    print(f'Successfully created time series {mac_address}:power with a retention time for 1 day')
except redis.ResponseError:
    redis_client.ts().alter(f'{mac_address}:power',retention_msecs=retention_period_1day)
    # If the time series already exists, update its retention period
    print(f'time series {mac_address}:power already existed,updated witha retention time for 1 day')
    pass

#Checkpoint2: Create a new timeseries called mac_address:plugged_seconds
# Create a timeseries named'mac_address:plugged_seconds' with a retention period to 30 day
try:
    redis_client.ts().create(f'{mac_address}:plugged_seconds',retention_msecs= retention_period_30day)
    print(f'Successfully created time series {mac_address}:plugged_seconds with a retention time for 30 day')
except redis.ResponseError:
    redis_client.ts().alter(f'{mac_address}:plugged_seconds',retention_msecs=retention_period_30day)
    # If the time series already exists, update its retention period
    print(f'time series {mac_address}:plugged_seconds already existed,updated witha retention time for 30 day')
    pass

#This is used to store the number of the seconds the power has been plugged. Initialized to 0
plugged_seconds = 0
#Set one hour to 3600 seconds for subsequent time calculations
an_hour = 60*60
passed_seconds = int(time.time()) % an_hour #This calculates how many seconds have passed since the beginning of the current hour. For example if the current time is 14:10:03, then the passed seconds is 603 from the last hour 14:00:00.
last_hour_timestamp = int(time.time()) - passed_seconds #Calculating the last hour/ the begin of an hour
last_hour_timestamp_ms = int(last_hour_timestamp * 1000)#Redis TS requires the timestamp in ms
end_hour_timestamp = last_hour_timestamp + an_hour #Calculating the end of an hour
#print(passed_seconds,last_hour_timestamp,end_hour_timestamp)

while True:
    #time.time() returns the current time in seconds since the epoch as a floating-point number. The epoch: January 1, 1970, at 00:00:00 UTC
    current_timestamp = time.time()
    current_timestamp_ms = int(current_timestamp * 1000) #Redis TS requires the timestamp in ms

    battery_level = psutil.sensors_battery().percent
    power_plugged = int(psutil.sensors_battery().power_plugged)
    redis_client.ts().add(f'{mac_address}:battery', current_timestamp_ms, battery_level)# Store the battery level value to the timeseries
    redis_client.ts().add(f'{mac_address}:power', current_timestamp_ms, power_plugged)# Store the power plugged flag value to the timeseries
    
    #formatted_datetime = datetime.fromtimestamp(current_timestamp).strftime('%Y-%m-%d %H:%M:%S.%f')
    # Read the last added values
    b_last_timestamp_ms, b_last_value = redis_client.ts().get(f'{mac_address}:battery')
    print(f'The TiemSeries {mac_address}:battery, stored timestsmp: {b_last_timestamp_ms}, the battery level: {b_last_value} per second')
    # Read the last added values
    p_last_timestamp_ms, p_last_value = redis_client.ts().get(f'{mac_address}:power')
    print(f'The TiemSeries {mac_address}:power, stored timestsmp: {p_last_timestamp_ms}, the power plugged value: {p_last_value} per second')

    
    if power_plugged:
        
        if current_timestamp  < end_hour_timestamp:
            plugged_seconds += 1
            #print(f'curr {current_timestamp}, end {end_hour_timestamp} plugged{plugged_seconds}')
        else:
            redis_client.ts().add(f'{mac_address}:plugged_seconds', last_hour_timestamp_ms, plugged_seconds)
            last_hour_timestamp = int(time.time()) - (int(time.time()) % an_hour)
            last_hour_timestamp_ms = int(last_hour_timestamp * 1000)
            end_hour_timestamp = last_hour_timestamp + an_hour
            plugged_seconds = 0
            # Read the last added values
            s_last_timestamp_ms, seconds = redis_client.ts().get(f'{mac_address}:plugged_seconds')
            print(f'----The TiemSeries {mac_address}:plugged_seconds, stored timestsmp: {s_last_timestamp_ms}, the seconds of power plugged: {seconds} per hour')

    else:
        if current_timestamp >= end_hour_timestamp:
            redis_client.ts().add(f'{mac_address}:plugged_seconds', last_hour_timestamp_ms, plugged_seconds)
            last_hour_timestamp = int(time.time()) - (int(time.time()) % an_hour)
            last_hour_timestamp_ms = int(last_hour_timestamp * 1000)
            end_hour_timestamp = last_hour_timestamp + an_hour
            plugged_seconds = 0
           # Read the last added values
            s_last_timestamp_ms, seconds = redis_client.ts().get(f'{mac_address}:plugged_seconds')
            print(f'----The TiemSeries {mac_address}:plugged_seconds, stored timestsmp: {s_last_timestamp_ms}, the bseconds of power plugged: {seconds} per hour')
                     
    #Checkpoint1:Set the acquisition period of mac_address:battery and mac_address:power to 1 second.
    time.sleep(1)