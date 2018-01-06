# -*- coding: utf-8 -*-
# Soiling Rate Dev, at inverter level
# Author: Qi Liu
# Email: qi.liu@colorado.edu

# import pymysql.cursors
import numpy as np
import pandas as pd
import time
import math
import datetime
import multiprocessing as mp
import matplotlib.pyplot as plt
from pandas.plotting import scatter_matrix
from sklearn import linear_model
from scipy.signal import medfilt

# Parameters configuration
startDTModel = '2016-01-01'
endDTModel = '2017-03-26'

# date list
start = datetime.datetime.strptime(startDTModel, "%Y-%m-%d").date()
end = datetime.datetime.strptime(endDTModel, "%Y-%m-%d").date()
dateList = [start + datetime.timedelta(days=x) for x in range(0, (end - start).days)]

dayList = []
for day in dateList:
    dayList.append(str(day))

# date list
start = datetime.datetime.strptime(startDTModel, "%Y-%m-%d").date()
end = datetime.datetime.strptime(endDTModel, "%Y-%m-%d").date()
dateList = [start + datetime.timedelta(days=x) for x in range(0, (end - start).days)]

dayList = []
for day in dateList:
    dayList.append(str(day))

timeRg = ['05:30', '19:30'];  # use pandas to get data within this range

resPath = '/Users/mira67/Documents/concord/concord_work/inverter/'
figPath = '/Users/mira67/Documents/concord/concord_work/'
qxjl = '/Users/mira67/Documents/concord/concord_work/qxjl.csv'

"""
Data Query Module: Extract data from database, table-nbq
Input: nbq Info: nbqID, Datetime: startDT,endDT
Output: nbq parameters
"""


def queryNbqData(nbqID, startDT, endDT, timeRg):

    sql1 = """SELECT data_date, I,V FROM pingyuan2.nbq WHERE nbqno = '{}'
            AND data_date BETWEEN '{}' AND '{}'
            AND TIME(data_date) BETWEEN '{}'AND '{}'"""
    sqlSts1 = sql1.format(nbqID, startDT, endDT, timeRg[0], timeRg[1])

    sql2 = """SELECT data_date,Fs1m, Fs2m, Wv, Wd, Sd, T0,I1m, I2m, V1m FROM pingyuan2.qxz
            WHERE data_date BETWEEN '{}' AND '{}'
            AND TIME(data_date) BETWEEN '{}'AND '{}';"""
    sqlSts2 = sql2.format(startDT, endDT, timeRg[0], timeRg[1])

    # Make database connetion
    db = pymysql.connect(host='localhost',
                         user='liuqi',
                         password='1234',
                         db='pingyuan2',
                         port=3306,
                         charset='utf8mb4',
                         cursorclass=pymysql.cursors.DictCursor, local_infile=True)
    cbData = pd.DataFrame()
    try:
        '''training data'''
        cursor = db.cursor()
        cursor.execute(sqlSts1)
        db.commit()

        # collect query data
        strCurrent = pd.DataFrame(cursor.fetchall())

        cursor.execute(sqlSts2)
        db.commit()

        # collect query data
        features = pd.DataFrame(cursor.fetchall())

        # join table to avoid missing dates problem
        cbData = strCurrent.join(features.set_index('data_date'), on='data_date')

    except Exception as e:
        # Rollback in case there is any error
        db.rollback()
        print('Not able to query hlx %s' % (nbqID))

    # close connection
    db.close()
    return cbData

# Main


def main_old():
    # list of combiner boxes
    hlx_info = pd.read_csv('E:/myprojects/pv_detection/data/concord_work/hlxinfo.csv')
    nbqList = hlx_info['nbqno'].unique().tolist()
    # hlxList = map(str, hlxList)

    start = time.time()

    for idx, nbqID in enumerate(nbqList):
        print(idx, nbqID)
        nbqData = queryNbqData(nbqID, startDTModel, endDTModel, timeRg)
        # fill na with the forward valid data
        nbqData.fillna(method='ffill')
        nbqData.to_csv(resPath + nbqID + '.csv')

        # downsample for quick plot
        nbqSample = nbqData.sample(n=2000, replace='False')
        nbqSample = nbqSample.drop(['data_date'], axis=1)
        nbqSample['P'] = nbqSample['I'] * nbqSample['V']
        nbqSample['Pex'] = nbqSample['I1m'] * nbqSample['V1m']
        # plot
        nbqSample = nbqSample.astype(np.float32)  # must convert to float32 before scatter
        nbqPlot(nbqSample, nbqID)

    end = time.time()
    runtime = end - start
    msg = "Single Process Took {time} seconds to complete"
    print(msg.format(time=runtime))

    # profiling
    '''
    start = time.time()

    with mp.Pool(3) as pool:
        results = pool.map(extractSlopeFea, hlxList[121:301])
    end = time.time()
    runtime = end - start

    msg = "Feature Extraction Multi-Processing Took {time} seconds to complete"
    print(msg.format(time=runtime))
    '''
# analyse nbq data


def nbqPlot(df, title):
    # correlation matrix
    scatter_matrix(df, alpha=0.2, figsize=(6, 6), diagonal='kde')
    plt.show()
    # plt.savefig(figPath + title + '.png', dpi=300)


def nbqTemp(df, title):
    tempRg = [[-10.0, 0.0], [0.0, 10.0], [10.0, 20.0], [20.0, 30.0], [30.0, 40.0]]
    #tempRg = [[0.0, 20.0], [20.0, 40.0], [40.0, 60.0], [60.0, 100.0]]
    # tempRg.reverse()
    df = df[df.P > 500]
    for rg in tempRg:
        data = df[df.T0 >= rg[0]]
        data = data[data.T0 < rg[1]]
        print(data.shape)
        plt.plot(data.Fs2m, data.P, '.', label=rg)
        lm = linearModel(data.Fs2m.values.reshape(-1, 1), data.P.values.reshape(-1, 1), 'ransac')
        print(rg, lm.estimator_.coef_[0])  #
        p_pred = lm.predict(data.Fs2m.values.reshape(-1, 1))
        plt.plot(data.Fs2m, p_pred, linewidth=2, label=str(rg) + 'regression')
    plt.ylabel('Power (W)')
    plt.xlabel('Solar Irradiance (W/m^2)')
    plt.legend()
    plt.show()


def linearModel(Features, stringCurrent, estimator):
    '''
    multiple regression estimation methods
    simple-simple linear
    theil-theil-sen, median
    '''
    if estimator == 'simple':
        lm = linear_model.LinearRegression()
        lm.fit(Features, stringCurrent)
    elif estimator == 'theil':
        pass
    elif estimator == 'ransac':
        lm = linear_model.RANSACRegressor()
        lm.fit(Features, stringCurrent)
    else:
        print('Invalid Estimator')
    return lm


def extractSlopeFea(df_org):
    '''
    Grab daily slopes and put in dataframe and save to csv files
    '''
    # grab daily slopes -> upgrade code to spark later for multiple columns computing in parallel
    # create an array to store slopes for each strings
    numDays = len(dayList)
    slopeArray = np.zeros((numDays, 1))
    try:
        for idx, day in enumerate(dateList):
            # query data
            print(day)
            df = df_org[(df_org['data_date'] >= str(day) + ' ' + timeRg[0]) &
                        (df_org['data_date'] < str(day) + '' + timeRg[1])]
            # print('remove data date')
            df = df.drop(['data_date'], axis=1)
            # print('add columns')
            df['P'] = df['I'] * df['V']
            # print('remove outliers')
            # df = df[df.apply(lambda x: np.abs(
            #     x - x.mean()) / x.std() < 3).all(axis=1)]
            print('computing...', df.shape)
            if df.shape[0] >= 100:
                # all strings currents
                df_power = df.P
                # feature data
                df_fea = df.Fs2m
                # fft feature holder for each CB
                all_slopes = pd.DataFrame()
                # features, currents
                try:
                    lm = linearModel(df_fea.values.reshape(-1, 1),
                                     df_power.values.reshape(-1, 1), 'ransac')
                    slope = lm.estimator_.coef_[0]  # lm.coef_[0]#extract slopes
                    # put in array
                    slopeArray[idx] = slope
                except:
                    # use the prev one, or assign zeros
                    slopeArray[idx] = slopeArray[idx - 1]
                    print('regression fail')

        # obtain dataframe and record to file
        slopeDF = pd.DataFrame(data=slopeArray, columns=['Pr'])
        slopeDF['data_date'] = pd.DataFrame(data=dayList)
        filename = resPath + 'slope_ransac' + '.csv'
        slopeDF.to_csv(filename, sep=',', header=True)
        print('Completed computing slopes')

    except Exception as e:
        print('Exception: ', e)
        print('Not able to process')

    return '2018'


def removeOutliers(a, outlierConstant):
    upper_quartile = np.percentile(a, 75)
    lower_quartile = np.percentile(a, 25)
    IQR = (upper_quartile - lower_quartile) * outlierConstant
    quartileSet = (lower_quartile - IQR, upper_quartile + IQR)
    resultList = []
    for y in a.tolist():
        if y >= quartileSet[0] and y <= quartileSet[1]:
            resultList.append(y)
        else:
            resultList.append(np.median(a))
    return resultList, upper_quartile


def alignClean():
    nbq_qx = pd.read_csv(qxjl)
    df = pd.read_csv(resPath + 'slope_ransac.csv')
    print(df.head())
    # df = df[df['DeviceCode'] == '350M201M2M1']
    nbq_qx = nbq_qx[nbq_qx['nbqno'] == 'S01-NBA']  # reorganize code and make a flow

    nbq_qx['qxdate'] = pd.to_datetime(nbq_qx['qxdate'], format='%Y-%m-%d %H:%M:%S')
    nbq_qx.set_index(['qxdate'], inplace=True)

    # plot slope
    # df['data_date'] = pd.to_datetime(df['data_date'],
    #                                  format='%Y-%m-%d %H:%M:%S')
    # df.set_index(['data_date'], inplace=True)

    df['data_date'] = pd.to_datetime(df['data_date'],
                                     format='%Y-%m-%d %H:%M:%S')
    df.set_index(['data_date'], inplace=True)

    slope = df.Pr / 485  # df.InvCPR  #
    med_slope, upper = removeOutliers(slope, 1)
    plt.plot(df.index, med_slope, label='Outliers/Missing Data Fixed')
    # med filtering
    y1 = medfilt(med_slope, 3)
    plt.plot(df.index, y1, label='7-day Med Filtered')

    # add clean record
    n_clean = [1.0] * nbq_qx.index.shape[0]
    plt.plot(nbq_qx.index, n_clean, 'x', label='Clean Event')
    plt.legend()
    plt.show()


def main():
    # list of combiner boxes
    nbqData = pd.read_csv(resPath + 'S01-NBA.csv')
    # fill na with the forward valid data
    # fill in
    nbqData = nbqData.fillna(method='ffill')
    # print('start computing slopes')
    # extractSlopeFea(nbqData)

    # downsample for quick plot
    nbqSample = nbqData.sample(n=50000, replace='False')
    nbqSample = nbqSample.drop(['data_date'], axis=1)

    # data cleaning
    nbqSample = nbqSample[nbqSample.apply(lambda x: np.abs(x - x.mean()) / x.std() < 3).all(axis=1)]

    nbqSample['P'] = nbqSample['I'] * nbqSample['V']

# Optimal Slope
#     df = nbqSample
#     df_power = df.P
#     # feature data
#     df_fea = df.Fs2m
#     # fft feature holder for each CB
#     all_slopes = pd.DataFrame()
# # features, currents
#     lm = linearModel(df_fea.values.reshape(-1, 1),
#                      df_power.values.reshape(-1, 1), 'ransac')
#     slope = lm.estimator_.coef_[0]  # lm.coef_[0]#extract slopes
#     # put in array
#     print('slope', slope)

    # nbqSample['Pex'] = nbqSample['I1m'] * nbqSample['V1m']

    # plot
    nbqSample = nbqSample.astype(np.float32)  # must convert to float32 before scatter

    nbqTemp(nbqSample, 'Temp, P, Solar')
    # plt.plot(nbqSample['r'], '.')
    # plt.show()
    # nbqSample['T0'].hist()
    # plt.plot(nbqSample['R'])
    # plt.show()
    # nbqPlot(nbqSample, 'inverter')


if __name__ == "__main__":
    # lignClean()
    main()