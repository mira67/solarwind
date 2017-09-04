#PV Estimator Based Fault Detection
#Author: Qi Liu
#Email: qi.liu@colorado.edu

"""Test 1: real-time online detection with raw 1min data without filtering"""

import pymysql.cursors
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import time
import multiprocessing as mp
import matplotlib.pyplot as plt
import statsmodels.api as sm

#Parameters configuration
startDTModel = '2016-04-01'
endDTModel = '2016-04-31'

startDTTest = '2016-06-01'
endDTTest = '2016-06-30'

timeRg = ['10:00','16:00'];#use pandas to get data within this range

resPath = 'E:/myprojects/pv_detection/data/model_fault_0826/'

"""
Step 1: Extract data from database, table-hlx
Input: String Info: hlxID, strID, Datetime: startDT,endDT
Output: String current
"""
def queryStrData(hlxID, strID, startDT,endDT):
    # AND TIME(data_date) BETWEEN '08:00'AND '17:00'
    # AND TIME(data_date) BETWEEN '08:00'AND '17:00'
    sql1 = """SELECT data_date,{} FROM pingyuan.hlx WHERE combinerbox = '{}' 
            AND data_date BETWEEN '{}' AND '{}';"""
    sqlSts1 = sql1.format(strID, hlxID, startDT,endDT)
    
    sql2 = """SELECT data_date,FS1,Fs2,Fs1m,Fs2m,Sd,T0 FROM pingyuan.qxz WHERE data_date BETWEEN '{}' AND '{}';"""
    sqlSts2 = sql2.format(startDT,endDT)
    
    sql3 = """SELECT data_date,{} FROM pingyuan.hlx WHERE combinerbox = '{}' 
            AND data_date BETWEEN '{}' AND '{}';"""
    sqlSts3 = sql3.format(strID, hlxID, startDTTest,endDTTest)
    
    sql4 = """SELECT data_date,FS1,Fs2,Fs1m,Fs2m,Sd,T0 FROM pingyuan.qxz WHERE data_date BETWEEN '{}' AND '{}';"""
    sqlSts4 = sql4.format(startDTTest,endDTTest)
    
    #Make database connetion
    db = pymysql.connect(host='localhost',
                                user='liuqi',
                                password='1234',
                                db='pingyuan',
                                port=3306,
                                charset='utf8mb4',
                                cursorclass=pymysql.cursors.DictCursor,local_infile=True)

    try:
        '''training data'''
        cursor = db.cursor()
        cursor.execute(sqlSts1)
        db.commit()
        
        #collect query data
        strCurrent = pd.DataFrame(cursor.fetchall())
        
        cursor.execute(sqlSts2)
        db.commit()
        
        #collect query data
        features = pd.DataFrame(cursor.fetchall())
        
        #join table to avoid missing data problem
        trainData = strCurrent.join(features.set_index('data_date'),on='data_date')
        
        '''test data'''
        cursor = db.cursor()
        cursor.execute(sqlSts3)
        db.commit()
        
        #collect query data
        strCurrent = pd.DataFrame(cursor.fetchall())
        
        cursor.execute(sqlSts4)
        db.commit()
        
        #collect query data
        features = pd.DataFrame(cursor.fetchall())
        
        #join table to avoid missing data problem
        testData = strCurrent.join(features.set_index('data_date'),on='data_date')
        
    except:
        # Rollback in case there is any error
        db.rollback()
        print('Not able to query string %s' % (strID))
        
    #close connection
    #cursor.close()
    db.close()
    return trainData,testData

#Step 3: Build model for individual string
def strPowerModel(Features,stringCurrent):
    #Build libear model
    lm = LinearRegression()
    lm.fit(Features,stringCurrent)
    return lm
    
#Step 4: Fault detection for individual string
def strFaultDetection(hlxID, strID, FeatureList, startDT,endDT):
    #Get data
    fullData,testData = queryStrData(hlxID, strID, startDT,endDT)
    fullData = fullData.dropna(axis=0, how='any')
    fullData = fullData.drop('data_date',axis=1)
    testData = testData.dropna(axis=0, how='any')
    testData = testData.drop('data_date',axis=1)
    
    #initialize varScore
    varScore = 0
    
    try:
    
        # Smoothing, rolling(center=False,window=60).mean()
        smLen = 60
        fullData = pd.rolling_mean(fullData, smLen)
        testData = pd.rolling_mean(testData, smLen)
        
        #Build Model
        stringCurrent = fullData.iloc[smLen:,0].as_matrix().astype(np.float32)
        Features = fullData.iloc[smLen:,1:7].as_matrix().astype(np.float32)
        
        Features = sm.add_constant(Features)
        
        lm = strPowerModel(Features,stringCurrent)
        # The coefficients
        print('Coefficients: \n', lm.coef_)
        print('Variance score: %.4f' % lm.score(Features,stringCurrent))
    
        """using model to check new data for faults
            grab test data from database, using last 10 days in June
            Method 1: directly compare difference error > 10%
        """
        
        #Get test data for this string [2016-06-01, 2016-06-30] data
        testX = testData.iloc[smLen:,1:7].as_matrix().astype(np.float64)
        testX = sm.add_constant(testX)
        
        testY = testData.iloc[smLen:,0].as_matrix().astype(np.float64)
        predY = lm.predict(testX)
        resErr = (testY-predY)/testY*100
        
        # variance score
        varScore = lm.score(testX, testY)
    
        # Plot outputs
    #     f1 = plt.figure(1)
    #     #plt.plot(stringCurrent, label='Actual Power from String')
    #     #plt.plot(predY, label='Predicted Power from String')
    #     plt.plot(testY, label='Actual Power from String')
    #     plt.plot(predY, label='Predicted Power from String')
    #     
    #     plt.xlabel('Time (min)')
    #     plt.ylabel('Power')
    #     plt.title('Linear Regression')
    #     plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.07),
    #           fancybox=True, shadow=True, ncol=5)
    # 
    #     f1.show()
    
        # Plot error
        # f2 = plt.figure(2)
        # plt.plot(resErr)
        # f2.show()
        
        # record results for each string: original current, estimated current, and error
        print(testY.shape)
        
        results = np.append(testY,predY)
        results = np.append(results,resErr)
        nRes = len(results)
        nData = len(testY)
        with open(resPath+hlxID+'_'+strID+'.csv','wb+') as f_handle:
            np.savetxt(f_handle, results.reshape((nData,3),order='F'), delimiter=',',fmt='%s')
    
    except:
        print('Not able to process string %s-%s' % (hlxID,strID))
    
    return varScore

    #set resErr > 10 to Fault label in restult file
    
    
#Step 5: Summarize fault detection results for ground truth comparison
def rankFaultString():
    pass
    
def test(lists):
    print(lists)
    
#Main
def main():
    dataPath = 'E:/myprojects/pv_detection/code/code/python/testData.xlsx'
    strInfo = pd.read_excel(dataPath).values.tolist(); 
    #strings = map(str, strInfo)#seems only string list works for pool map
    #print(strInfo)
    
    varScores = []
    
    #profiling
    start = time.time()
    for idx,item in enumerate(strInfo):
        testData = strInfo[idx]
        hlxID = testData[0]
        strID = 'I'+str(testData[1])
        FeatureList = ['FS1','Fs2','Fs1m','Fs2m','Wv','Wd','Sd','T0']
        varScore = strFaultDetection(hlxID, strID, FeatureList, startDTModel,endDTModel)
        varScores.append(varScore)
    
    #Record all var scores
    with open(resPath+hlxID+'_'+strID+'_varScores.csv','wb+') as f_handle:
        np.savetxt(f_handle, varScores, delimiter=',',fmt='%s')
    
    end = time.time()
    runtime = end - start
    msg = "Fault Detection Single-Processing Took {time} seconds to complete"
    print(msg.format(time=runtime))
    
    '''
    start = time.time()
    #patternDetection('1191278995')
    with mp.Pool(3) as pool:
        results = pool.map(test, strings)
    end = time.time()
    runtime = end - start
    msg = "Fault Detection Multi-Processing Took {time} seconds to complete"
    print(msg.format(time=runtime))
    '''
    

if __name__ == "__main__":
    main()

#Alert! Thinking programming in multi-processing ways and easier to configure with
#new alsogithms and data pre-processing methods
