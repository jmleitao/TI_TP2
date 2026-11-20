#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 28 12:13:36 2026

@author: lorenapetrella

In the terminal install wfdb: pip install wfdb 
"""

import wfdb

filename = "folder_path/record_name"   # record number without extension

record = wfdb.rdrecord(filename)

for key, value in record.__dict__.items():
    print(f"{key}: {value}")

fs = record.fs
signal = record.p_signal                 # 2D
