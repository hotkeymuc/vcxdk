#!/bin/sh

# WARNING: CAT28C64 is 5 volt and not compatible with GLCX
#minipro -p 'CAT28C64B' -w CART_GLCX_Update_Programm-Zusatzkassette.dump.000.8KB_recombine.bin

#minipro -p 'AT28LV010@TSOP32' -r CART_GL8008CX_Update.dump.000.segs-128KB_recombine_back.bin
#minipro -p 'AT28LV64@PLCC32' -r AT28LV64_empty_read.bin

minipro -p 'AT28LV64@PLCC32' -w monitor.bin
