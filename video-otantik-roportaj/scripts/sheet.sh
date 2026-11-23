#!/bin/bash
# Look before you decide, and look after you render: frames of a video as one image.
# usage: sheet.sh <video> <out.jpg> [every_s=1] [cols=10] [width=160]   |   sheet.sh <video> <out.jpg> at "0.1 1.5 3.2" [width=360]
set -eu; V=$1; O=$2; FF=${FF:-ffmpeg}
if [ "${3:-}" = "at" ]; then
  T=$(mktemp -d); i=0; for t in $4; do $FF -v error -y -ss $t -i "$V" -frames:v 1 -vf "scale=${5:-360}:-1,drawtext=text='$t':x=8:y=8:fontsize=22:fontcolor=yellow:box=1:boxcolor=black@0.5" $T/$(printf %03d $i).png 2>/dev/null || $FF -v error -y -ss $t -i "$V" -frames:v 1 -vf "scale=${5:-360}:-1" $T/$(printf %03d $i).png; i=$((i+1)); done
  $FF -v error -y -pattern_type glob -i "$T/*.png" -vf "tile=${i}x1" -frames:v 1 "$O"; rm -r $T
else
  D=$(${FP:-ffprobe} -v error -show_entries format=duration -of csv=p=0 "$V"); N=$(python3 -c "import math;print(math.ceil($D/${3:-1}))"); C=${4:-10}
  $FF -v error -y -i "$V" -vf "fps=1/${3:-1},scale=${5:-160}:-1,tile=${C}x$(( (N + C - 1) / C ))" -frames:v 1 "$O"
fi
echo "$O"
