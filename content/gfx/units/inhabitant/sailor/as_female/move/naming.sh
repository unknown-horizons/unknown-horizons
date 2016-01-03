#!/bin/sh


for file in 45/ 90/ 270/ 315/ ;
do
cd */
for i in [0-9].png; do mv $i 000${i%.png}.png; done
for i in [0-9][0-9].png; do mv $i 00${i%.png}.png; done
cd ..

done
