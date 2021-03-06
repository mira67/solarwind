# -*- coding: utf-8 -*-
"""
Created on Fri Nov 10 14:58:02 2017

@author: xiaomei
"""

import numpy as np
import pandas as pd
from sklearn import svm 
from sklearn.metrics import classification_report,confusion_matrix
from sklearn import preprocessing
from sklearn.model_selection import StratifiedKFold
from sklearn import neighbors 
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
from sklearn import tree
from sklearn.naive_bayes import GaussianNB, MultinomialNB #Bayes
from sklearn.ensemble import BaggingClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.ensemble import AdaBoostClassifier
from sklearn.ensemble import GradientBoostingClassifier
import csv



AnomalyTypeNum = 5
FaultNum = 1034

inPath = '/Users/zhaoyingying/PVData/ADIbyCen/n_interval_fft_scale/frq_features_600interval.csv'  
outPath = '/Users/zhaoyingying/PVData/ADIbyCen/temporal_frq_features/frq_plot_360interval.csv'
 
   
def frq_format():
    #get ready for plot

    
    dt = pd.read_csv(inPath, delimiter=',') 
    dt2 = dt.drop(['Unnamed: 0'],axis = 1)   
    Type = dt2.pop('Type')
    dt2.insert(0,'Type',Type)         
    dt2 =dt2.iloc[:,:]
              
    #total:
    maxresults = pd.DataFrame()
    maxresults = pd.DataFrame(data=dt2.groupby(dt2.iloc[:,0]).max())
    print(maxresults)

    
    minresults = pd.DataFrame()
    minresults = pd.DataFrame(data=dt2.groupby(dt2.iloc[:,0]).min())
    
    meanresults = pd.DataFrame()
    meanresults = pd.DataFrame(data=dt2.groupby(dt2.iloc[:,0]).mean())
   
    
    newdf = pd.concat([maxresults,minresults,meanresults])
    newresults = newdf.as_matrix()
    newresults1 = np.transpose(newresults)
    
    
   # newdf.to_csv(outPath)
    np.savetxt(outPath,newresults1,fmt='%.2f',delimiter=',')
    
#    results['Method'] = pd.DataFrame(data=method, columns=['Type1_Max'])
#    results['Precision'] = pd.DataFrame(data=precision, columns=['Precision'])
#    results['Recall'] = pd.DataFrame(data=recall, columns=['Recall'])
#    results['F1'] = pd.DataFrame(data=f1, columns=['F1'])
#    
#
#    
#    results.groupby('Method').mean().to_csv(totalreportPath)

                    
if __name__ == '__main__':
        

    frq_format()

    
    