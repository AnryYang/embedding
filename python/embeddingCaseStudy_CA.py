#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Embedding case study at CA level.


Created on Sun Jan 22 16:08:27 2017

@author: hj
"""

import pickle
import numpy as np
import matplotlib.pyplot as plt
from embeddingEvaluation_tract import retrieveCrossIntervalEmbeddings, getLEHDfeatures_helper, mergeBlockCensus
from sklearn.cluster import KMeans


def tract_to_CA():
    import shapefile
    sf = shapefile.Reader("../data/Census-Tracts-2010/chicago-tract")
    
    tract2CA = {}
    for rec in sf.records():
        tid = int(rec[2])
        CAid = int(rec[6])
        tract2CA[tid] = CAid
    
    return tract2CA


def CA_poi():
    t2c = tract_to_CA()
    with open("../miscs/POI_tract.pickle") as fin:
        ordKey = pickle.load(fin)
        tract_poi = pickle.load(fin)
    ca_poi = {}
    for tid in t2c:
        if tid not in tract_poi:
            print tid
            continue
        cid = t2c[tid]
        if cid not in ca_poi:
            ca_poi[cid] = tract_poi[tid]
        else:
            for k, v in tract_poi[tid].items():
                if k in ca_poi[cid]:
                    ca_poi[cid][k] = ca_poi[cid][k] + v
                else:
                    ca_poi[cid][k] = v
    return ca_poi
    

def get_CAfeatures_from_tractFeatures(tacs, t2c):
    cacs = {}
    for tid in tacs:
        cid = t2c[tid]
        if cid not in cacs:
            cacs[cid] = tacs[tid]
        else:
            cacs[cid] = mergeBlockCensus(cacs[cid], tacs[tid])
            
    ids = []
    x = []
    for tid, vec in cacs.items():
        vec_sum = float(sum(vec))
        if vec_sum != 0:
            ids.append(tid)
            v = vec / vec_sum
            x.append(v)
            
    return np.array(ids), x



def generatePOIClusteringlabel(nclusters=3):
    t2c = tract_to_CA()
    with open("../miscs/POI_tract.pickle") as fin:
        ordKey = pickle.load(fin)
        tract_poi = pickle.load(fin)
        
    n = len(ordKey)
    header = ['Food', 'Residence', 'Travel', 'Arts & Entertainment', 
        'Outdoors & Recreation', 'College & Education', 'Nightlife', 
        'Professional', 'Shops', 'Event']
    tpois = {}
    for i, k in enumerate(ordKey):
        row = np.zeros((len(header),))
        if k in tract_poi:
            for j, h in enumerate(header):
                if h in tract_poi[k]:
                    row[j] = tract_poi[k][h]
        tpois[k] = row
    ids, x = get_CAfeatures_from_tractFeatures(tpois, t2c)
    
    cls = KMeans(n_clusters=nclusters)
    res = cls.fit(x)
    return ids, res.labels_





def generate_AC_clusteringLabel(ncluster=3, racORwac="rac"):
    t2c = tract_to_CA()
    if racORwac == "rac":
        fn = "../data/il_rac_S000_JT03_2013.csv"
    elif racORwac == "wac":
        fn = "../data/il_wac_S000_JT00_2013.csv"
        
    tacs = getLEHDfeatures_helper(fn, t2c.keys())
    
    ids, x = get_CAfeatures_from_tractFeatures(tacs, t2c)
    
    cls = KMeans(n_clusters=ncluster)
    res = cls.fit(x)
    return ids, res.labels_



def generate_od_clusteringLabel(ncluster=2):
    t2c = tract_to_CA()
    racs = getLEHDfeatures_helper("../data/il_rac_S000_JT03_2013.csv", t2c.keys())
    wacs = getLEHDfeatures_helper("../data/il_wac_S000_JT00_2013.csv", t2c.keys())
    acs = {}
    for tid in t2c:
        v1 = racs[tid] if tid in racs else np.zeros((1,))
        v2 = wacs[tid] if tid in wacs else np.zeros((1,))
        v = np.concatenate((v1, v2))
        acs[tid] = v
    ids, x = get_CAfeatures_from_tractFeatures(acs, t2c)
    labels = np.array([0 if e[0] > e[1] else 1 for e in x])
    
    return ids, labels



def visualizeEmbedding_2D_withCluster(ncluster=3):
    twoGraphEmbeds, twoGRids = retrieveCrossIntervalEmbeddings("../miscs/taxi-deepwalk-CA-usespatial.vec", skipheader=0)
    
#    gndTid, gndLabels = generate_AC_clusteringLabel(ncluster, "wac")
#    gndTid, gndLabels = generatePOIClusteringlabel(ncluster)
    gndTid, gndLabels = generate_od_clusteringLabel(ncluster)
    clrs = ["b", "r", "g", "w", "c", "b"]
    
    
    
    plt.figure(figsize=(80,60))
    plt.suptitle("OD count as ground truth {0} clusters".format(ncluster))
    for h in range(24):
        plt.subplot(4,6,h+1)
        for cluster in range(ncluster):
            groupIds = gndTid[np.argwhere(gndLabels==cluster)]
            idx = np.in1d(twoGRids[h], groupIds)
            x = twoGraphEmbeds[h][idx,0]
            y = twoGraphEmbeds[h][idx,1]
            ids = twoGRids[h][idx]
            
            plt.scatter(x, y, c=clrs[cluster], hold=True)
            for i, e in enumerate(ids):
                plt.annotate(s = str(e), xy=(x[i], y[i]), xytext=(-5, 5), textcoords="offset points")
            plt.title("2D visualization at {0}".format(h))
    plt.savefig("CA-OD-{0}cluster.png".format(ncluster))   
        
    
def visualizeEmbedding_2D():
    twoGraphEmbeds, twoGRids = retrieveCrossIntervalEmbeddings("../miscs/taxi-deepwalk-CA-usespatial.vec", skipheader=0)
    groups = [[5,6,7,21,22], [8,32,33], [26, 27, 29, 30]]
    clrs = ["b", "r", "g", "w", "c", "b"]
    
    plt.figure(figsize=(22,14))
    for h in range(24):
        plt.subplot(4,6,h+1)
        for i, group in enumerate(groups):
            idx = np.in1d(twoGRids[h], group)
            x = twoGraphEmbeds[h][idx,0]
            y = twoGraphEmbeds[h][idx,1]
            ids = twoGRids[h][idx]
            
            plt.scatter(x, y, c=clrs[i], hold=True)
            for j, e in enumerate(ids):
                plt.annotate(s = str(e), xy=(x[j], y[j]), xytext=(-5, 5), textcoords="offset points")
            plt.title("2D visualization at {0}".format(h))
    plt.savefig("CA-case-3region.png")
    
    
    
def getTaxiFlow():
    flows = {}
    for h in range(24):
        f = np.loadtxt("../miscs/taxi-CA-h{0}.matrix".format(h), delimiter=" ")
        flows[h] = f
    return flows


def visualizeFlow():
    f = getTaxiFlow()
    cas = [5,6,7,21,22] # [26, 27, 29, 30] # [8,32,33]
    plt.figure(figsize=(22,14))
    for h in range(24):
        plt.subplot(4,6,h+1)
        lg = []
        for ca in cas:
            plt.plot(f[h][ca-1,:])
            lg.append(str(ca))
        plt.legend(lg)
        plt.title(str(h))
    
    
if __name__ == "__main__":
    visualizeFlow()
#    visualizeEmbedding_2D()
#    visualizeEmbedding_2D_withCluster(2)