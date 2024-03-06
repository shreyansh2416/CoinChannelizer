###### setting up api
from __future__ import print_function
import gate_api
from gate_api.exceptions import ApiException, GateApiException

from datetime import datetime
import pandas as pd
import numpy as np
import mplfinance as mpf
import os
import shutil
import parameters as pmts

configuration = gate_api.Configuration(
    host = "https://api.gateio.ws/api/v4"
)

api_client = gate_api.ApiClient(configuration)
api = gate_api.SpotApi(api_client)



def main(threshold_channel, coin, interval, start_date, end_date):

    ###### function to check if a channel can be considered valid
    ###### takes in coordinates of channel parallelogram and number of times sma crosses mid-channel
    ###### returns boolean value
    def is_valid_channel(i, j, yi0, yi1, yj0, yj1, crossings):
        if (crossings < pmts.crossings):
            return False

        touch_requirement = pmts.touch_requirement_factor * (i - j + 1)
        touch_band_size = (yi1 - yi0) * pmts.touch_tolerance
        
        ceil_count = 0
        floor_count = 0
        out_count = 0
        
        slope = (yi0 - yj0) / (i - j)
        ceiling = yi1
        floor = yi0
        
        for k in range(i, j-1, -1):
            if max(Open[k], Close[k]) > ceiling:
                out_count = out_count + 1
            elif High[k] >= ceiling - touch_band_size:
                ceil_count = ceil_count + 1
            
            if min(Open[k], Close[k]) < floor:
                out_count = out_count + 1
            elif Low[k] <= floor + touch_band_size:
                floor_count = floor_count + 1
            
            ceiling = ceiling - slope
            floor = floor - slope
       
        if out_count > pmts.breakout_tolerance * (i - j + 1):
            return False
        
        if ceil_count < touch_requirement or floor_count < touch_requirement:
            return False
        
        return True


    ###### function to join two candles by 'low' value
    def join_bottom_tip(i, j):
        yi0 = Low[i]
        yj0 = Low[j]

        slope = (yi0 - yj0) / (i - j)
        floor = yi0
        mx_diff = 0
        for k in range(i, j-1, -1):
            mx_diff = max(mx_diff, High[k] - floor)
            floor = floor - slope

        yi1 = yi0 + mx_diff
        yj1 = yj0 + mx_diff
        
        return yi0, yi1, yj0, yj1

    ###### function to join two candles by 'high' value
    def join_top_tip(i, j):
        yi1 = High[i]
        yj1 = High[j]

        slope = (yi1 - yj1) / (i - j)
        ceiling = yi1
        mx_diff = 0
        for k in range(i, j-1, -1):
            mx_diff = max(mx_diff, ceiling - Low[k])
            ceiling = ceiling - slope

        yi0 = yi1 - mx_diff
        yj0 = yj1 - mx_diff
        
        return yi0, yi1, yj0, yj1 


    ###### function to take in list of channels and plot them
    def plot_channels(list_of_channels):
        points_for_channel = []
        points_for_breakout = []
        for i, j, yi0, yi1, yj0, yj1 in list_of_channels:
            points_for_channel.append([(str(df.index[i]), yi0), (str(df.index[j]), yj0)])
            points_for_channel.append([(str(df.index[i]), yi1), (str(df.index[j]), yj1)])

            ### uncomment to get mid line in channels
            # points_for_channel.append([(str(df.index[i]), (yi0 + yi1)/2), (str(df.index[j]), (yj0 + yj1)/2)])

            if (pmts.mark_false_breakouts):
                slope = (yi1 - yj1) / (i - j)
                floor = yi0
                ceiling = yi1
                
                for k in range(i, j-1, -1):
                    if floor <= Open[k] and Open[k] <= ceiling and (Close[k] < floor or ceiling < Close[k]):
                        points_for_breakout.append(str(df.index[k]))
                    
                    floor = floor - slope
                    ceiling = ceiling - slope

        filename = path + '/' + coin + '_' + str(start_date)[ : 10] + '_' + str(end_date)[ : 10]
        if (pmts.mark_false_breakouts):
            mpf.plot(df,
                alines = dict(alines = points_for_channel, linewidths = 0.1, alpha = 1),
                vlines = dict(vlines = points_for_breakout, colors = 'm', linewidths = 0.005, alpha = 0.2),
                type = 'candle', style = 'yahoo', figsize = (16, 9), savefig = filename)
        else:
            mpf.plot(df,
                alines = dict(alines = points_for_channel, linewidths = 0.1, alpha = 1),
                type = 'candle', style = 'yahoo', figsize = (16, 9), savefig = filename)


    ###### function to return number of times sma crosses the mid of a channel
    def get_crossings(i, j, yi0, yi1, yj0, yj1):
        crossings = 0
        
        slope = (yi0 - yj0) / (i - j)
        midi = (yi0 + yi1) / 2
        midj = (yj0 + yj1) / 2
        
        mid = np.linspace(midj, midi, i-j+1)
        ma = sma5[j : i+1]
        res = ma > mid
        
        for k in range(1, len(res), 1):
            if res[k] != res[k-1]:
                crossings = crossings + 1
        
        return crossings


    ###### taking input, formatting and querying the api
    currency_pair = coin + '_' + 'USDT'
    start_date = datetime.strptime(start_date, '%m/%d/%Y')
    end_date = datetime.strptime(end_date, '%m/%d/%Y')
    # print(currency_pair, start_date, end_date)

    from_timestamp = int(start_date.timestamp())
    to_timestamp = int(end_date.timestamp())

    try:
        api_response = api.list_candlesticks(currency_pair, _from=from_timestamp, to=to_timestamp, interval=interval)
    except GateApiException as ex:
        print("Gate api exception, label: %s, message: %s\n" % (ex.label, ex.message))
    except ApiException as e:
        print("Exception when calling SpotApi->list_candlesticks: %s\n" % e)


    ###### storing fetched data in dataframe, cleaning and finding sma
    df = pd.DataFrame(api_response)
    df.columns = ['Time', 'Volume', 'Close', 'High', 'Low', 'Open']
    df['Time'] = [datetime.fromtimestamp(int(df.iloc[i]['Time'])) for i in df.index]
    df = df.set_index('Time')
    df[['Volume', 'Close', 'High', 'Low', 'Open']] = df[['Volume', 'Close', 'High', 'Low', 'Open']].astype(float)
    df['sma5'] = df['Close'].rolling(int(threshold_channel / 5)).mean()


    ###### creating numpy arrays of chlo data for faster execution
    Close = df['Close'].to_numpy()
    High = df['High'].to_numpy()
    Low = df['Low'].to_numpy()
    Open = df['Open'].to_numpy()
    sma5 = df['sma5'].to_numpy()


    ###### going through the candles to get list of channels
    list_of_channels = []
    i = len(df.index)-1
    while (i >= 0):
        for j in range(max(i - 2*threshold_channel + 1, 0), i - threshold_channel + 2, 1):
            yi0, yi1, yj0, yj1 = join_bottom_tip(i, j)
            crossings = get_crossings(i, j, yi0, yi1, yj0, yj1)
            if (is_valid_channel(i, j, yi0, yi1, yj0, yj1, crossings)):
                list_of_channels.append((i, j, yi0, yi1, yj0, yj1))
                i = j-1
                break
            
            yi0, yi1, yj0, yj1 = join_top_tip(i, j)
            crossings = get_crossings(i, j, yi0, yi1, yj0, yj1)
            if (is_valid_channel(i, j, yi0, yi1, yj0, yj1, crossings)):
                list_of_channels.append((i, j, yi0, yi1, yj0, yj1))
                i = j-1
                break
            
        i = i - 1


    ###### printing the channels
    print(coin, ':', len(list_of_channels))
    for channel in list_of_channels:
        print(df.index[channel[1]], '\t', df.index[channel[0]])


    ###### plotting the channels
    plot_channels(list_of_channels)





###### creating new 'plots' folder for writing plots
path = 'Plots'
if os.path.exists(path):
    shutil.rmtree(path)
try:
    os.makedirs(path)
except:
    print('could not create directory for plots, check line no. 206')


###### cleaning 'output.txt'
# print('', end = '', file = open('output.txt', 'w'))


###### reading input and processing test cases
input_lines = open('inputfile').read().split('\n')
test_cases = int(input_lines[0])
thold = int(input_lines[1])
for i in range(2, len(input_lines)):
    if len(input_lines[i]) == 0:
        continue
    tmp = input_lines[i].split(', ')
    coin = tmp[0]
    interval = tmp[1]
    start_date = tmp[2]
    end_date = tmp[3]

    main(thold, coin, interval, start_date, end_date)

    test_cases = test_cases - 1
    if test_cases == 0:
        break

print('press enter to stop main program')
input()