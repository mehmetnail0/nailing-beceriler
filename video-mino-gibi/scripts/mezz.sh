#!/bin/bash
# Step 1 of the plain path: source clip -> 1440x2560 30 fps SDR Rec.709 mezzanine (mezz.mp4) + 48 kHz wav (a48.wav).
# Runs on a laptop with plain ffmpeg (zscale + tonemap filters; the Homebrew / apt / gyan builds have them).
# usage: mezz.sh <source.mov|mp4> <workdir> [W H]      env: FF=ffmpeg  ENC=libx264  (ENC=hevc_nvenc on an NVIDIA box)
# - A phone clip in HLG / HDR10 (iPhone "HDR video", 10-bit bt2020 + arib-std-b67 / smpte2084) is tone-mapped to SDR here.
#   A plain SDR clip (bt709) skips the tone-map and is only scaled.
# - A landscape clip is centre-cropped to 9:16 (cover). Move the crop yourself in edit.json later if the speaker is off-centre.
set -eu
SRC=${1:?source file}; WD=${2:?workdir}; MW=${3:-1440}; MH=${4:-2560}
FF=${FF:-ffmpeg}; FP=${FP:-ffprobe}; ENC=${ENC:-libx264}
mkdir -p "$WD"
TRC=$($FP -v error -select_streams v:0 -show_entries stream=color_transfer -of csv=p=0 "$SRC" | head -1 | tr -d " ,\r")
echo "source transfer: ${TRC:-unknown}"
FIT="scale=${MW}:${MH}:force_original_aspect_ratio=increase:flags=lanczos,crop=${MW}:${MH}"
case "$TRC" in
  arib-std-b67)  # HLG (iPhone). npl=100 + hable measured as the closest to what the phone shows.
    VF="fps=30,${FIT},zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:rin=tv:t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p" ;;
  smpte2084)     # HDR10 / PQ
    VF="fps=30,${FIT},zscale=tin=smpte2084:min=bt2020nc:pin=bt2020:rin=tv:t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p" ;;
  *)             VF="fps=30,${FIT},format=yuv420p" ;;
esac
if [ "$ENC" = "libx264" ]; then ENCARGS="-c:v libx264 -preset fast -crf 12"; else ENCARGS="-c:v $ENC -preset p5 -rc constqp -qp 15"; fi
T0=$(date +%s)
$FF -y -v error -i "$SRC" -vf "$VF" $ENCARGS -an -colorspace bt709 -color_primaries bt709 -color_trc bt709 "$WD/mezz.mp4"
$FF -y -v error -i "$SRC" -vn -ac 1 -ar 48000 -c:a pcm_s16le "$WD/a48.wav"
echo "mezz ready in $(( $(date +%s)-T0 ))s: $WD/mezz.mp4 + $WD/a48.wav"
