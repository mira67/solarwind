#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec  1 11:50:30 2017

@author: zhaoyingying
"""


import pandas as pd
#import matplotlib.pyplot as plt
from ggplot import ggplot,aes,geom_point,ggtitle
from ggplot import *

from sklearn.manifold import TSNE

n_sne = 1034



#inPath = '/Users/zhaoyingying/PVData/ADIbyCen/ADIALLTimeSeriesrenameType_rawsignal.csv'

#aggregation feature set
#inPath = '/Users/zhaoyingying/PVData/ADIbyCen/agg_features.csv'
#outPath = '/Users/zhaoyingying/PVData/ADIbyCen/agg_tsne_gnuplot.csv'

#spectrum feature set
#inPath = '/Users/zhaoyingying/PVData/ADIbyCen/trends_features.csv'
#outPath = '/Users/zhaoyingying/PVData/ADIbyCen/trends_tsne_gnuplot.csv'

#similarity feature set
inPath = '/Users/zhaoyingying/PVData/ADIbyCen/n_interval_fft_scale/frq_features_600interval.csv'
outPath = '/Users/zhaoyingying/PVData/ADIbyCen/temporal_frq_features/frq_features_plot.csv'
#3dplot 
outPath3d = '/Users/zhaoyingying/PVData/ADIbyCen/temporal_frq_features/frq_features_3dplot.csv'
def tsne():
    tsne = TSNE(n_components=2, verbose=1, perplexity=40, n_iter=300)
    df = pd.read_csv(inPath)
    tsne_results = tsne.fit_transform(df.iloc[:n_sne,1:-1].values)
 
    #concert to the fomat for gnuplot
    df_tsne = pd.DataFrame()
    df_tsne['Type']= df.iloc[:,0]
    df_tsne['#x-tsne'] = tsne_results[:,0]
    df_tsne['#y-tsne'] = tsne_results[:,1]
    #df_tsne['z-tsne'] = tsne_results[:,2]
    #df_tsne.to_csv(outPath3d,index = False)
 
    print(df_tsne.iloc[0:475,1:3])
    df_tsne_t1 =df_tsne.iloc[0:475,1:3].copy()
    df_tsne_t2 =df_tsne.iloc[475:704,1:3].copy()
    
    df_tsne_t2.index = range(len(df_tsne_t2))
    
    df_tsne_t3 =df_tsne.iloc[704:900,1:3].copy()
    df_tsne_t3.index = range(len(df_tsne_t3))
    df_tsne_t4 =df_tsne.iloc[904:,1:3].copy()
    df_tsne_t4.index = range(len(df_tsne_t4))
    df_tsne_t5 =df_tsne.iloc[900:904,1:3].copy()
    df_tsne_t5.index = range(len(df_tsne_t5))
    res = pd.concat([df_tsne_t1, df_tsne_t2, df_tsne_t3,df_tsne_t4,df_tsne_t5],axis=1)
    res.to_csv(outPath)

if __name__ == '__main__':
    tsne()