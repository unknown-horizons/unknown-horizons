#!/bin/bash

find * -type f -iname '*.pyc' -exec rm "{}" \; 
find * -type f -iname '*.pyo' -exec rm "{}" \; 
