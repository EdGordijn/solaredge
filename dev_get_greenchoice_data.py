#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 27 21:48:26 2022

@author: edgordijn
"""

from get_greenchoice_data import GreenchoiceApi


meterstanden = GreenchoiceApi(username='ed.gordijn@gmail.com',
                              password='m1jnGreenchoice')

df = meterstanden.get_meterstanden(year=2022, product=1)
