#!/bin/sh
ffmpeg -f image2 -r 6 -i ${1}%5d.png -vcodec mpeg4 -y ${1}.mp4
echo ${1}
