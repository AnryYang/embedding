#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Embedding evaluation at tract level.


Created on Mon Dec 26 17:27:45 2016

@author: hj
"""

import pickle
import numpy as np
from sklearn import tree
from sklearn.model_selection import cross_val_score
import matplotlib.pyplot as plt
from scipy.spatial.distance import cosine
from sklearn.preprocessing import scale
from sklearn.cluster import KMeans


"""
===========================================
Pairwise similarity evaluation
===========================================
"""


numLayer = 8


def generatePOIlabel_helper(ordKey, tract_poi, poi_type):
    poi_cnt = []
    cnt = 0
    for k in ordKey:
        if k in tract_poi and poi_type in tract_poi[k]:
            poi_cnt.append(tract_poi[k][poi_type])
            cnt += 1
        else:
            poi_cnt.append(0)
    median = np.median(poi_cnt)
    print "{0} #non-zeros {1}, median {2}".format(poi_type, cnt, median)
    label = np.array([1 if val >= median else 0 for val in poi_cnt])
    assert len(label) == len(ordKey)
    return label, median >= 1
    
    
def generatePOIBinarylabel(ordKey, tract_poi):
    header = ['Food', 'Residence', 'Travel', 'Arts & Entertainment', 
        'Outdoors & Recreation', 'College & Education', 'Nightlife', 
        'Professional', 'Shops', 'Event']
        
    L = {}
    for h in header:
        l, flag = generatePOIlabel_helper(ordKey, tract_poi, h)
        if flag:
            L[h] = l
    return L
    
    
def generatePairWiseGT(rids, tract_poi):
    header = ['Food', 'Residence', 'Travel', 'Arts & Entertainment', 
        'Outdoors & Recreation', 'College & Education', 'Nightlife', 
        'Professional', 'Shops', 'Event']
    gnd_vec = {}
    for k in rids:
        if k not in tract_poi:
            poi = [0] * 10
        else:
            poi = []
            for p in header:
                if p in tract_poi[k]:
                    poi.append(tract_poi[k][p])
                else:
                    poi.append(0)
        pv = np.array(poi) / float(sum(poi)) if sum(poi) != 0 else np.array(poi)
        gnd_vec[k] = pv
    
    gnd_pair = {}
    for k in rids:
        cosDist = []
        for k2 in rids:
            if k2 == k:
                continue
            c = cosine(gnd_vec[k], gnd_vec[k2])
            if np.isnan(c):
                c = 2
            cosDist.append((k2, c))
        cosDist.sort(key=lambda x: x[1])
        gnd_pair[k] = [cosDist[i][0] for i in range(3)]
            
    return gnd_pair
        
            
    

def selectSamples(labels, rids, ordKey):
    idx = np.searchsorted(ordKey, rids)
    return labels[idx]
    
    
def retrieveEmbeddingFeatures_helper(fileName):
    t = np.genfromtxt(fileName, delimiter=" ", skip_header=1)
    rid = t[:,0].astype(int)
    features = t[:, 1:]
    return features, rid
    
    
def retrieveEmbeddingFeatures():
    """
    Retrive embeddings for each region from the *.vec file.
    
    The first line of *.vec file is region count.
    Beginning from the second line, the first column is the region ID, then it is the embedding.
    """
    embedF = []
    embedRid = []
    for h in range(numLayer):
        t = np.genfromtxt("../miscs/taxi-h{0}.vec".format(h), delimiter=" ", skip_header=1)
        embedRid.append(t[:,0].astype(int))
        t = t[:, 1:]
        assert t.shape[1]==20
        embedF.append(t)
    return embedF, embedRid
    
    
    
def retrieveCrossIntervalEmbeddings(fn="../miscs/taxi-crossInterval.vec", skipheader=1):
    t = np.genfromtxt(fn, delimiter=" ", skip_header=skipheader, dtype=None)
    tid = [row[0] for row in t]
    
    t = np.genfromtxt(fn, delimiter=" ", skip_header=skipheader)
    f = t[:, 1:]
    
    embeddings = {}
    features = {}
    rids = {}
    for i, v in enumerate(tid):
        kv = v.split("-")
        k1 = int(kv[0])
        k2 = int(kv[1])
        if k1 not in embeddings:
            embeddings[k1] = {k2: f[i]}
            features[k1] = [f[i]]
            rids[k1] = [k2]
        else:
            embeddings[k1][k2] = f[i]
            features[k1].append(f[i])
            rids[k1].append(k2)
    
    for k in features.keys():
        features[k] = np.array(features[k])
        rids[k] = np.array(rids[k])
    
    return features, rids

    
def pairwiseEstimator(features, rids):
    """
    Use the feature vectors for each sample to find the k-nearest neighbors for each sample.
    
    Input:
        features - a matrix containing features of all samples.
        rids - a list containing the region IDs for previous samples. Order match
    
    Output:
        return a dicionary containing the KNN lists for each region in the rids.
        The key of dictionary is the Id of each region.
    """
    estimates = {}
    for i, k in enumerate(rids):
        pd = []
        for i2, k2 in enumerate(rids):
            if k2 == k:
                continue
            pd.append( (k2, cosine(features[i], features[i2])) )
        pd.sort(key=lambda x: x[1])
        estimates[k] = pd
    return estimates
    
    
    
    
def evalute_by_binary_classification():
    with open("../miscs/POI_tract.pickle") as fin:
        ordKey = pickle.load(fin)
        tract_poi = pickle.load(fin)
    
    with open("nmf-tract.pickle") as fin2:
        nmfeatures = pickle.load(fin2)
        nmRid = pickle.load(fin2)
        
    embedFeatures, embedRid = retrieveEmbeddingFeatures()
    
    labels = generatePOIBinarylabel(ordKey, tract_poi)
    clf = tree.DecisionTreeClassifier()
    
    plt.figure()
    for i, l in enumerate(labels):
        print "{0}\tMF\tEmbedding".format(l)
        nm = []
        embed = []
        ax = plt.subplot(3,3,i+1)
        for h in range(24):
            assert len(np.intersect1d(nmRid[h], embedRid[h])) == len(embedRid[h])
            L = selectSamples(labels[l], nmRid[h], ordKey)
            score1 = cross_val_score(clf, nmfeatures[h], L, cv=10)
            score2 = cross_val_score(clf, embedFeatures[h], L, cv=10)
            nm.append(score1.mean())
            embed.append(score2.mean())
        ax.plot(nm)
        ax.plot(embed)
        ax.set_title(l)
        ax.legend(['NM', 'Embedding'], loc='best')
    plt.show()
            
    

def topK_accuracy(k, estimator, pair_gnd):
    """
    Return the precision and recall with top k pairs.
    """
    cnt = 0
    total = len(pair_gnd)
    for rid in estimator:
        knn = [estimator[rid][i][0] for i in range(k)]
        if len(np.intersect1d(pair_gnd[rid], knn)) != 0:
            cnt += 1
    return float(cnt) / total
    


def topKcover_case(k, estimator, pair_gnd, cmp_estimator):
    """
    Print out cases where the estimator covers the ground truth in the top k answers.
    
    Input:
        k - number of top answers to give
        estimator - the embedding estimator, a dictionary with region id as key and KNN list as value
        pair_gnd - the ground truth, same format as estimator
        cmp_estimator - the method to compare (MF), same format as estimator
    """
    for rid in estimator:
        knn = [estimator[rid][i][0] for i in range(k)]
        cmp_knn = [cmp_estimator[rid][i][0] for i in range(k)]
        if len(np.intersect1d(knn, pair_gnd[rid])) == len(pair_gnd[rid]):
            print "Case", rid
            print pair_gnd[rid]
            print knn
            print len(np.intersect1d(cmp_knn, pair_gnd[rid])), cmp_knn
    
    
    
def evalute_by_pairwise_similarity():
    with open("../miscs/POI_tract.pickle") as fin:
        ordKey = pickle.load(fin)
        tract_poi = pickle.load(fin)
    
    with open("../miscs/nmf-tract.pickle") as fin2:
        nmfeatures = pickle.load(fin2)
        nmRid = pickle.load(fin2)
        
    
    pair_gnd = generatePairWiseGT(ordKey, tract_poi)
        
    embedFeatures, embedRid = retrieveEmbeddingFeatures()
    crosstimeFeatures, cteRid = retrieveCrossIntervalEmbeddings("../miscs/taxi-deepwalk-tract-nospatial.vec", skipheader=0)
    twoGraphEmbeds, twoGRids = retrieveCrossIntervalEmbeddings("../miscs/taxi-deepwalk-tract-usespatial.vec", skipheader=0)
    
    features, rid = retrieveEmbeddingFeatures_helper("../miscs/taxi-all.vec")
    pe_all_embed = pairwiseEstimator(features, rid)
    acc = topK_accuracy(20, pe_all_embed, pair_gnd)
    print "Acc of static graph", acc
    
    ACC1 = []
    ACC2 = []
    ACC3 = []
    ACC4 = []
    plt.figure()
    for h in range(numLayer):
        
        pe_embed = pairwiseEstimator(embedFeatures[h], embedRid[h])
        pe_mf = pairwiseEstimator(nmfeatures[h], nmRid[h])
        pe_cte = pairwiseEstimator(crosstimeFeatures[h], cteRid[h])
        pe_twoG = pairwiseEstimator(twoGraphEmbeds[h], twoGRids[h])
        
        cov1 = len(embedRid[h]) / float(len(ordKey))
        cov2 = len(nmRid[h]) / float(len(ordKey))
        cov3 = len(cteRid[h]) / float(len(ordKey))
        cov4 = len(twoGRids[h]) / float(len(ordKey))
        
        acc1 = topK_accuracy(20, pe_embed, pair_gnd)
        acc2 = topK_accuracy(20, pe_mf, pair_gnd)
        acc3 = topK_accuracy(20, pe_cte, pair_gnd)
        acc4 = topK_accuracy(20, pe_twoG, pair_gnd)
        
        ACC1.append(acc1)
        ACC2.append(acc2)
        ACC3.append(acc3)
        ACC4.append(acc4)
        print h, cov1, acc1, cov2, acc2, cov3, acc3, cov4, acc4
    plt.plot(ACC1)
    plt.plot(ACC2)
    plt.plot(ACC3)
    plt.plot(ACC4)
    plt.legend(["Embedding", "MF", "CrossTime", "CT+Spatial"], loc='best')
    
        
        
    

def casestudy_pairwise_similarity():
    with open("../miscs/POI_tract.pickle") as fin:
        ordKey = pickle.load(fin)
        tract_poi = pickle.load(fin)
        
    with open("nmf-tract.pickle") as fin2:
        nmfeatures = pickle.load(fin2)
        nmRid = pickle.load(fin2)

    embedFeatures, embedRid = retrieveEmbeddingFeatures()
    
    for h in range(numLayer):
        print "Hour:", h
        pe_embed = pairwiseEstimator(embedFeatures[h], embedRid[h])
        pe_mf = pairwiseEstimator(nmfeatures[h], nmRid[h])
        pair_gnd = generatePairWiseGT(embedRid[h], tract_poi)
        topKcover_case(8, pe_embed, pair_gnd, pe_mf)

        
"""
===========================================
Clustering evaluation with tweets
===========================================
"""

def generateTweetsClusteringlabel(nclusters):
    tweets = np.loadtxt("../miscs/tweetsCount.txt", delimiter=" ")
    tid = tweets[:,0]
    features = tweets[:, 1:]
#    features = scale(features)
    
    
    cls = KMeans(n_clusters=nclusters)
    res = cls.fit(features)
    return tid, res.labels_
    


def generatePOIClusteringlabel(nclusters):
    with open("../miscs/POI_tract.pickle") as fin:
        ordKey = pickle.load(fin)
        tract_poi = pickle.load(fin)
        
    n = len(ordKey)
    header = ['Food', 'Residence', 'Travel', 'Arts & Entertainment', 
        'Outdoors & Recreation', 'College & Education', 'Nightlife', 
        'Professional', 'Shops', 'Event']
    x = np.zeros((n, len(header)))
    for i, k in enumerate(ordKey):
        if k in tract_poi:
            for j, h in enumerate(header):
                if h in tract_poi[k]:
                    x[i, j] = tract_poi[k][h]
            row_sum = np.sum(x[i,:])
            if row_sum > 0:
                x[i,:] = x[i,:] / row_sum
    
    cls = KMeans(n_clusters=nclusters)
    res = cls.fit(x)
    return ordKey, res.labels_
        

def generateCrimeClusteringlabel(nclusters):
    crimes = []
    ids = []
    with open("../data/chicago-crime-tract-level-2013.csv") as fin:
        h = fin.readline()
        for l in fin:
            ls = l.strip().split(",")
            ids.append(int(ls[0][5:]))
            total = float(ls[-1])
            vec = np.array([int(e) for e in ls[1:-1]]) / total
            crimes.append(vec)
            
    cls = KMeans(n_clusters=nclusters)
    res = cls.fit(crimes)
    return ids, res.labels_
    

    
def generateLEHDClusteringlabel(ncluster, racORwac="rac"):
    keys = []
    with open("../data/chicago-crime-tract-level-2013.csv") as fin:
        h = fin.readline()
        for l in fin:
            ls = l.strip().split(",")
            keys.append(ls[0])
    assert(len(keys)==801)
    
    racs = {}
    fn = "../data/il_rac_S000_JT03_2013.csv" if racORwac == "rac" else "../data/il_wac_S000_JT00_2013.csv"
    with open(fn) as fin2:
        h = fin2.readline()
        for l in fin2:
            ls = l.strip().split(",")
            tid = ls[0][0:11]
            if tid in keys:
                tid = int(tid[5:])
                vec = np.array([int(e) for e in ls[1:-1]])
                if tid not in racs:
                    racs[tid] = vec
                else:
                    racs[tid] = mergeBlockCensus(vec, racs[tid])
    
    ids = []
    x = []
    for tid, vec in racs.items():
        vec_sum = float(sum(vec))
        if vec_sum != 0:
            ids.append(tid)
            x.append(vec / vec_sum)
            
    cls = KMeans(n_clusters=ncluster)
    res = cls.fit(x)
    return ids, res.labels_


def mergeBlockCensus( a , b ):
    if len(a) != len(b):
        print "Two list length do not match!"
        return None
        
    for idx, val in enumerate(a):
        a[idx] += b[idx]
        
    return a    
    

def clusteringAccuracy(features, tid, gndTid, gndLabels, nclusters):
    cls = KMeans(n_clusters=nclusters)
    res = cls.fit(features)
    labels = res.labels_
    
    grp_cnt = np.zeros((nclusters, nclusters))
    for i in range(nclusters):
        idx_grp = np.argwhere(labels == i)
        for t in tid[idx_grp]:
            idx = np.argwhere(gndTid == t)
            l = gndLabels[idx]
            grp_cnt[i,l] += 1
    
    cnt_pos = 0
    
    total_samples = [np.sum(r) for r in grp_cnt]
    grp_visit_order = np.argsort(total_samples)
    grp_visit_order = grp_visit_order[::-1] # visit largest group first
    
    mapped_label = []
    for grp_id in grp_visit_order:
        gnd_label = np.argsort(grp_cnt[grp_id])[::-1]
        mapto = -1
        for gnd_l in gnd_label:
            if gnd_l not in mapped_label:
                mapto = gnd_l
                mapped_label.append(gnd_l)
                break
#        print grp_id, mapto, gnd_label, grp_cnt[grp_id], grp_cnt[grp_id, mapto]
        cnt_pos += grp_cnt[grp_id, mapto]
    
    
    return cnt_pos / len(gndTid)     
            

def evaluate_by_clustering(numCluster = 4):
    
    with open("../miscs/nmf-tract.pickle") as fin2:
        nmfeatures = pickle.load(fin2)
        nmRid = pickle.load(fin2)
    
#    gndTid, gndLabels = generateTweetsClusteringlabel(numCluster)
#    gndTid, gndLabels = generatePOIClusteringlabel(numCluster)
#    gndTid, gndLabels = generateCrimeClusteringlabel(numCluster)
    gndTid, gndLabels = generateLEHDClusteringlabel(numCluster, "wac")
    
    visualizeClusteringResults(gndTid, gndLabels, numCluster)

    # test the static graph clustering    
    features, rid = retrieveEmbeddingFeatures_helper("../miscs/taxi-all.vec")
    accr = clusteringAccuracy(features, rid, gndTid, gndLabels, numCluster)
    print accr
    
    
    embedFeatures, embedRid = retrieveEmbeddingFeatures()
    crosstimeFeatures, cteRid = retrieveCrossIntervalEmbeddings("../miscs/taxi-deepwalk-nospatial.vec", skipheader=0)
    twoGraphEmbeds, twoGRids = retrieveCrossIntervalEmbeddings("../miscs/taxi-deepwalk.vec", skipheader=0)
    
    ACC1 = []
    ACC2 = []
    ACC3 = []
    ACC4 = []
    for h in range(numLayer):
        # MF
        acc1 = clusteringAccuracy(nmfeatures[h], nmRid[h], gndTid, gndLabels, numCluster)
        cov1 = len(nmRid[h]) / float(len(gndTid))
        # LINE on time-slotted graph
        acc2 = clusteringAccuracy(embedFeatures[h], embedRid[h], gndTid, gndLabels, numCluster)
        cov2 = len(embedRid[h]) / float(len(gndTid))
        # word2vec on crosstime graph only
        acc3 = clusteringAccuracy(crosstimeFeatures[h], cteRid[h], gndTid, gndLabels, numCluster)
        cov3 = len(cteRid[h]) / float(len(gndTid))
        # word2vec on crosstime graph + spatial graph jointly
        acc4 = clusteringAccuracy(twoGraphEmbeds[h], twoGRids[h], gndTid, gndLabels, numCluster)
        cov4 = len(twoGRids[h]) / float(len(gndTid))
        
        print h, cov1, acc1, cov2, acc2, cov3, acc3, cov4, acc4
        ACC1.append(acc1)
        ACC2.append(acc2)
        ACC3.append(acc3)
        ACC4.append(acc4)
    
    plt.figure()
    plt.plot(ACC1)
    plt.plot(ACC2)
    plt.plot(ACC3)
    plt.plot(ACC4)
    plt.legend(["MF", "LINE", "CrossTime", "CT+Spatial"], loc='best')
    plt.title("POI clustering evaluation")
    plt.xlabel("Time slot")
    plt.ylabel("Accuracy")
       
 
    
def visualizeClusteringResults(gndTid, gndLabels, numCluster):
    import shapefile
    from shapely.geometry import Polygon
    from descartes import PolygonPatch
    import matplotlib.patches as mpatches
    
    sf = shapefile.Reader("../data/Census-Tracts-2010/chicago-tract")
    shps = sf.shapes()
    tracts = {}
    for idx, shp in enumerate(shps):
        tid = int(sf.record(idx)[2])
        tracts[tid] = Polygon(shp.points)
        
    clrs = ["b", "r", "g", "c", "w", "b"]
    
    f = plt.figure()
    ax = f.gca()
    for i, tid in enumerate(gndTid):
        ax.add_patch(PolygonPatch(tracts[tid], alpha=0.5, fc=clrs[gndLabels[i]]))
    
    legend_handles = []
    for i in range(numCluster):
        cnt = np.argwhere(gndLabels==i).shape[0]
        lh = mpatches.Patch(color=clrs[i], label="{0} with #{1} samples".format(i, cnt))
        legend_handles.append(lh)
    plt.legend(handles=legend_handles)
    plt.title("Clustering ground truth visualization")
        
    ax.axis("scaled")
    plt.show()
    
    
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "binary":
            evalute_by_binary_classification()
        elif sys.argv[1] == "pairwise-eval":
            evalute_by_pairwise_similarity()
        elif sys.argv[1] == "pairwise-case":
            casestudy_pairwise_similarity()
        elif sys.argv[1] == "cluster-eval":
            evaluate_by_clustering(4)
        else:
            print "wrong parameter"
    else:
        print "missing parameter"
        i, l = generateLEHDClusteringlabel(4, "rac")
        visualizeClusteringResults(i, l, 4)