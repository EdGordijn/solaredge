#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 12 22:34:29 2022

@author: edgordijn
"""

import itertools
import pandas as pd
import numpy as np

tuples = [t for t in itertools.product(range(1000), range(4))]
index = pd.MultiIndex.from_tuples(tuples, names=['lvl0', 'lvl1'])
data = np.random.randn(len(index),4)
df = pd.DataFrame(data, columns=list('ABCD'), index=index)
grouped = df.groupby(level='lvl1')
grouped.boxplot(rot=45, fontsize=12, figsize=(8,10)) 