#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Taxi flow feature genration at CA level.

Goal:
    1. Generate the Matrix factorization features for taxi flow
    2. Generate the LINE embeddings features for taxi flow
    3. Generate the deepwalk embedding features for taxi flow and spatial flow.

Dependency:
    1. The taxi-CA-h{0}.matrix files, on which the MF is applied to learn representations.
    2. The taxi-CA-h{0}.vec files, which are the LINE embeddings learnt from each hour.
    3. The taxi-deepwalk-CA-usespatial.vec, which is the deepwalk embedding learnt from heterogenous graphs.
    
Created on Sun Jan 15 20:25:37 2017

@author: hj
"""

import numpy as np
import nimfa
from embeddingEvaluation_tract import retrieveEmbeddingFeatures_helper, retrieveCrossIntervalEmbeddings
import pickle
import sys


def NMFfeatures_helper(h):    
    f = np.loadtxt("../miscs/taxi-CA-h{0}.matrix".format(h), delimiter=" ")
    d1, d2 = f.shape
    assert d1 == d2 and d1 == 77
    
    nmf = nimfa.Nmf(f, rank=4, max_iter=100) #, update="divergence", objective="conn", conn_change=50)
    nmf_fit = nmf()
    src = nmf_fit.basis()
    dst = nmf_fit.coef()
    res = np.concatenate( (src, dst.T), axis=1 )
    assert res.shape == (77, 8)
    return res
  

def getNMFfeatures():
    """
    Return a dictionary, where key is the hour index, and value is the feature representations
    """
    res = {}
    for h in range(24):
        res[h] = NMFfeatures_helper(h)
    return res
    

def getLINEembeddingFeatures():
    res = {}
    for h in range(24):
        f, ids = retrieveEmbeddingFeatures_helper("../miscs/taxi-CA-h{0}.vec".format(h))
        assert len(ids) == 77
        sids = np.argsort(ids)
        features = f[sids, :]
        res[h] = features
    return res
    
    
def getDeepwalkEmbeddingFeatures(Spatial):
    res = {}
    emptyEmbedding = np.zeros((8,))
    features, ids = retrieveCrossIntervalEmbeddings("../miscs/taxi-deepwalk-CA-{0}.vec".format(Spatial), skipheader=0)
    for h in range(24):
        sids = np.argsort(ids[h])
        res[h] = features[h][sids, :]
        
        if len(sids) != 77:
            print len(sids), h
            for i in range(1, 78):
                if i not in ids[h]:
                    res[h] = np.insert(res[h], i-1, emptyEmbedding, axis=0)
        assert res[h].shape == (77, 8)
    return res


if __name__ == "__main__":
    mf = getNMFfeatures()
    line = getLINEembeddingFeatures()
    dw = getDeepwalkEmbeddingFeatures(sys.argv[1])
    with open("../miscs/CAflowFeatures.pickle", "w") as fout:
        pickle.dump(mf, fout)
        pickle.dump(line, fout)
        pickle.dump(dw, fout)
        