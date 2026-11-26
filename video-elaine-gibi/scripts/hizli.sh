#!/bin/bash
# hizli.sh: the user's materials + one ask -> a finished reel that passed the cut gate. Run it from the skill folder.
#   bash scripts/hizli.sh prep <run> <clip|folder> [more files] [-- "<ask>"]  copy the skill to <run>, prepare the media (cached per clip),
#                                                                         write <run>/work/brief.md: what the model reads to write work/decide.py
#   bash scripts/hizli.sh go <run> ["<lut args>"]     decide -> check -> render on all cores -> cut gate -> loudness, detached;
#                                                     ends with <run>/work/DONE (or FAILED) and <run>/work/final.mp4
#   bash scripts/hizli.sh quick <run>                 after a one-line ask changed work/decide.py or work/edit.json: redraw only what changed,
#                                                     detached too (DONE / FAILED as for go); HIZLI_FG=1 runs go or quick in the foreground
#   bash scripts/hizli.sh all <run> <materials> -- "<ask>"   prep, then the model step with a logged-in `claude` on this machine, then go
# Step times land in <run>/work/hizli.log. Env: HIZLI_CACHE (prepared media, default ~/.cache/video-beceri), HIZLI_JOBS, HIZLI_MODEL, CLAUDE,
# HIZLI_LANG, HIZLI_LOCK (a folder used as a mkdir lock around render + gate on a shared GPU box).
set -u
K=$(cd "$(dirname "$0")/.." && pwd); CMD=${1:?prep|go|quick|all}; RUN=${2:?run folder}; shift 2
mkdir -p "$RUN" && RUN=$(cd "$RUN" && pwd)   # absolute: go and quick cd into it
GPU=0; command -v nvidia-smi >/dev/null && nvidia-smi -L >/dev/null 2>&1 && GPU=1
ENC=libx264; [ $GPU = 1 ] && ENC=h264_nvenc
JOBS=${HIZLI_JOBS:-$(( $(nproc 2>/dev/null || sysctl -n hw.ncpu) / 12 ))}; [ "$JOBS" -lt 1 ] && JOBS=1; [ "$JOBS" -gt 12 ] && JOBS=12
W="$RUN/work"; LOG="$W/hizli.log"
now() { python3 -c 'import time; print(time.time())'; }
step() { echo "$(date +%T) $1 $(awk -v a="$(now)" -v b="$2" 'BEGIN{printf "%.1f", a-b}') s" >> "$LOG"; }

lock() {
  [ -n "${HIZLI_LOCK:-}" ] || return 0
  local t=$(now) o; until mkdir "$HIZLI_LOCK" 2>/dev/null; do
    o=$(awk '{print $NF}' "$HIZLI_LOCK/owner" 2>/dev/null)
    case "$o" in ''|*[!0-9]*) ;; *) kill -0 "$o" 2>/dev/null || { rm -rf "$HIZLI_LOCK"; continue; } ;; esac   # its owner died without letting go
    sleep 2; done
  echo "hizli $RUN $$" > "$HIZLI_LOCK/owner"; trap 'rm -rf "$HIZLI_LOCK"' EXIT; trap 'exit 143' INT TERM HUP; step "waited for the GPU lock" $t
}

prep() {
  local ASK="" FILES=()
  while [ $# -gt 0 ]; do [ "$1" = "--" ] && { ASK=${2:-}; break; }; FILES+=("$1"); shift; done
  mkdir -p "$W/malzeme"; T0=$(now)
  for d in SKILL.md example example-2 reference scripts fonts; do [ -e "$K/$d" ] && [ ! -e "$RUN/$d" ] && cp -r "$K/$d" "$RUN/"; done
  [ -e "$RUN/models" ] || { mkdir -p "$RUN/models"; for m in "$K"/models/*; do ln "$m" "$RUN/models/" 2>/dev/null || cp "$m" "$RUN/models/"; done; }
  local ALL=() f
  for f in "${FILES[@]}"; do if [ -d "$f" ]; then while IFS= read -r x; do ALL+=("$x"); done < <(find "$f" -type f ! -name '.*' | sort); else ALL+=("$f"); fi; done
  local CLIP="" BEST=0 d
  for f in "${ALL[@]}"; do   # the clip = the longest file with both a picture and a voice; everything else is material
    ffprobe -v error -show_entries stream=codec_type -of csv=p=0 "$f" 2>/dev/null | grep -q audio || continue
    ffprobe -v error -show_entries stream=codec_type -of csv=p=0 "$f" 2>/dev/null | grep -q video || continue
    d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f" | cut -d. -f1); [ "${d:-0}" -gt "$BEST" ] && { BEST=$d; CLIP=$f; }
  done
  [ -n "$CLIP" ] || { echo "no clip with picture and sound among: ${ALL[*]}" | tee -a "$LOG"; exit 1; }
  for f in "${ALL[@]}"; do [ "$f" = "$CLIP" ] || ln -f "$f" "$W/malzeme/" 2>/dev/null || cp "$f" "$W/malzeme/"; done
  printf '%s\n' "$ASK" > "$W/ask.txt"; echo "$(date +%T) prep $CLIP" >> "$LOG"
  local KEY C; KEY=$( { stat -c %s "$CLIP" 2>/dev/null || stat -f %z "$CLIP"; head -c 4000000 "$CLIP"; tail -c 4000000 "$CLIP"; } | shasum | cut -c1-16)
  C=${HIZLI_CACHE:-$HOME/.cache/video-beceri}/$KEY; mkdir -p "$C"
  if [ -s "$C/face.json" ] && [ -s "$C/words.json" ]; then
    for x in mezz.mp4 a48.wav words.json sil.json face.json src.jpg; do ln -f "$C/$x" "$W/$x" 2>/dev/null || cp "$C/$x" "$W/$x"; done; step "media from cache" $T0
  else
    local t=$(now) FFE=libx264; [ $GPU = 1 ] && FFE=hevc_nvenc
    ffmpeg -y -v error -i "$CLIP" -vn -ac 1 -ar 48000 -c:a pcm_s16le "$C/a48.wav"; step "voice track" $t
    # the voice does not wait for the picture: transcript and pauses run while the mezzanine is made
    ( t=$(now); python3 "$RUN/scripts/transcribe.py" "$C/a48.wav" "$C/words.json" $( [ $GPU = 1 ] && echo --gpu ) ${HIZLI_LANG:+--lang $HIZLI_LANG} > "$W/tr.log" 2>&1
      python3 "$RUN/scripts/silences.py" "$C/a48.wav" "$C/sil.json" > "$W/sil.log" 2>&1; step "transcript + pauses" $t ) &
    local TP=$!
    t=$(now); ENC=$FFE bash "$RUN/scripts/mezz.sh" "$CLIP" "$C.m" > "$W/mezz.log" 2>&1 && mv "$C.m/mezz.mp4" "$C/mezz.mp4"; rm -rf "$C.m"; step "mezzanine" $t
    t=$(now); python3 "$RUN/scripts/facetrack.py" "$C/mezz.mp4" "$RUN/models/yunet.onnx" "$C/face.json" > "$W/ft.log" 2>&1; step "face track" $t
    bash "$RUN/scripts/sheet.sh" "$C/mezz.mp4" "$C/src.jpg" 2 > /dev/null 2>&1
    wait $TP
    [ -s "$C/words.json" ] && [ -s "$C/face.json" ] || { echo "prep failed: see $W/tr.log $W/mezz.log $W/ft.log" | tee -a "$LOG"; exit 1; }
    for x in mezz.mp4 a48.wav words.json sil.json face.json src.jpg; do ln -f "$C/$x" "$W/$x" 2>/dev/null || cp "$C/$x" "$W/$x"; done
  fi
  python3 - "$W" "$BEST" <<'PY'
import json, os, sys
W, dur = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(os.path.dirname(W), 'scripts')); from timeline import noface
NF = noface(os.path.join(W, 'face.json'))
lines = [f"[{g['start']:.2f}-{g['end']:.2f}] {g['text'].strip()}" for g in json.load(open(os.path.join(W, 'words.json')))['segments']]
sil = json.load(open(os.path.join(W, 'sil.json')))['silences']
mat = sorted(os.listdir(os.path.join(W, 'malzeme')))
ask = open(os.path.join(W, 'ask.txt')).read().strip()
b = [f'# Brief', f'Ask: {ask or "(none: a finished reel in this style from the clip)"}', f'Clip: {dur} s, prepared as work/mezz.mp4 (1440x2560) + work/a48.wav; look: work/src.jpg',
     'Material given (work/malzeme/): ' + (', '.join(mat) if mat else 'none'),
     f'Pauses (work/sil.json): {len(sil)}; cut inside them. Face track: work/face.json. Word times: work/words.json.',
     'No speaker in the picture (source seconds; a title card, a logo, a cutaway: no take starts, ends or runs through one, check_edit refuses it): '
     + (', '.join(f'{a:.2f}-{b:.2f}' for a, b in NF) or 'none'), '', '## What was said (source seconds)'] + lines
open(os.path.join(W, 'brief.md'), 'w').write('\n'.join(b) + '\n')
PY
  cat > "$W/model_prompt.md" <<PR
You are the editor for one reel in this skill's style. Read SKILL.md (the style's numbers and steps), the files in example/ when there is one
(a finished edit in this style: keep its structure, not its choices), and work/brief.md (the user's ask, the material they gave, every line with source times).
Look at work/src.jpg. Write work/decide.py for this clip and this ask: it writes work/edit.json. Use the material in work/malzeme/ where the ask
or the story needs it; do not go looking for other material unless the ask asks for it. Run python3 work/decide.py, then
python3 scripts/check_edit.py work/edit.json, and fix until it prints ok. Do not render. End with the single line DONE.
PR
  step "prep total" $T0; echo "$W/brief.md"
}

model() {
  local t=$(now)
  ( cd "$RUN" && ${CLAUDE:-claude} -p "$(cat work/model_prompt.md)$( [ -s work/ask_next.txt ] && printf '\n\nThe ask now: %s' "$(cat work/ask_next.txt)")" \
      --model "${HIZLI_MODEL:-sonnet}" --permission-mode acceptEdits --allowedTools "Read,Write,Edit,Glob,Grep,Bash(python3:*)" > work/model.log 2>&1 )
  step "model" $t; tail -n 1 "$W/model.log" | grep -q DONE
}

edges() {   # every take edge against the source voice: a retake's first word, a clipped word end, room past the speaker's own pause
  local t=$(now); python3 scripts/edges.py work/edit.json work/words.json > "$W/edges.txt" 2>&1 || fail "edges: $(tail -n 3 "$W/edges.txt")"
  if python3 -c "import json,sys;sys.exit(json.load(open(sys.argv[1]))['changed']==0)" "$W/edges.txt"; then
    python3 work/decide.py > "$W/decide.txt" 2>&1 || fail "decide.py after edges failed: $(tail -n 3 "$W/decide.txt")"
  fi
  step "edges ($(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['changed'])" "$W/edges.txt") moved)" $t
}

go() {
  local LUTA=${1:---strength 0.75} T0=$(now) t TAG=h$(date +%H%M%S)
  rm -f "$W/DONE" "$W/FAILED"; cd "$RUN"
  fail() { echo "$1" | tee -a "$LOG" > "$W/FAILED"; exit 1; }
  t=$(now); python3 work/decide.py > "$W/decide.txt" 2>&1 || fail "decide.py failed: $(tail -n 3 "$W/decide.txt")"; step decide $t
  edges
  python3 scripts/yerlesim.py work/edit.json --fix > "$W/yerlesim.txt" 2>&1 || fail "placement: $(tail -n 4 "$W/yerlesim.txt")"
  [ -f work/look.cube ] || python3 scripts/lut.py work/look.cube $LUTA > /dev/null
  python3 scripts/check_edit.py work/edit.json > "$W/check.txt" 2>&1; tail -n 1 "$W/check.txt" | grep -q '^ok$' || fail "check: $(cat "$W/check.txt")"
  local R="python3 scripts/render.py work/edit.json work/out_$TAG.mp4 --encoder $ENC --jobs $JOBS"
  lock
  t=$(now); python3 scripts/render.py work/edit.json /dev/null --fit > "$W/fit.txt" 2>&1 || fail "fit: $(tail -n 3 "$W/fit.txt")"; step "fit (behind words, stills)" $t
  t=$(now); $R > "$W/render.txt" 2>&1 || fail "render: $(tail -n 5 "$W/render.txt")"; step "render ($JOBS slices)" $t
  t=$(now); python3 scripts/cutgate.py work/out_$TAG.mp4 --out work/cutqc --render "$R" > "$W/cutgate.txt" 2>&1; local g=$?; step "cut gate" $t
  [ $g = 0 ] || fail "cut gate exit $g: $(tail -n 3 "$W/cutgate.txt") (exit 2 = the model's ear: work/cutqc/judge.json)"
  ffmpeg -nostats -hide_banner -i work/out_$TAG.mp4 -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I:|Peak:)" | tr -s ' ' > "$W/loud.txt"
  ln -f work/out_$TAG.mp4 work/final.mp4; cp work/edit.json work/edit.last.json; [ -f work/out_$TAG.video.mp4 ] && ln -f work/out_$TAG.video.mp4 work/final.video.mp4
  step "go total" $T0; echo "$W/final.mp4" > "$W/DONE"
}

quick() {
  [ -s "$W/edit.last.json" ] && [ -s "$W/final.mp4" ] || { echo "$(date +%T) quick: no finished render yet, running go" >> "$LOG"; go; return; }
  local T0=$(now) t TAG=q$(date +%H%M%S); rm -f "$W/DONE" "$W/FAILED"; cd "$RUN"
  fail() { echo "$1" | tee -a "$LOG" > "$W/FAILED"; exit 1; }
  [ work/decide.py -nt work/edit.json ] && { python3 work/decide.py > "$W/decide.txt" 2>&1 || fail "decide.py failed: $(tail -n 3 "$W/decide.txt")"; }
  edges
  python3 scripts/yerlesim.py work/edit.json --fix > "$W/yerlesim.txt" 2>&1 || fail "placement: $(tail -n 4 "$W/yerlesim.txt")"
  python3 scripts/check_edit.py work/edit.json > "$W/check.txt" 2>&1; tail -n 1 "$W/check.txt" | grep -q '^ok$' || fail "check: $(cat "$W/check.txt")"
  lock
  t=$(now); python3 scripts/render.py work/edit.json /dev/null --fit > "$W/fit.txt" 2>&1 || fail "fit: $(tail -n 3 "$W/fit.txt")"; step "fit (behind words, stills)" $t
  t=$(now); python3 scripts/quick.py work/edit.last.json work/edit.json work/final.mp4 work/out_$TAG.mp4 --encoder $ENC --jobs $JOBS > "$W/quick.txt" 2>&1 || fail "quick: $(tail -n 3 "$W/quick.txt")"
  step "quick $(tail -n 1 "$W/quick.txt" | python3 -c 'import json,sys;print(json.load(sys.stdin)["path"])')" $t
  if ! python3 -c "import json,sys;a,b=(json.load(open(p))['segments'] for p in sys.argv[1:]);sys.exit(a!=b)" work/edit.last.json work/edit.json; then
    t=$(now); python3 scripts/cutgate.py work/out_$TAG.mp4 --out work/cutqc_$TAG --render "python3 scripts/render.py work/edit.json work/out_$TAG.mp4 --encoder $ENC --jobs $JOBS" \
      > "$W/cutgate.txt" 2>&1 || fail "cut gate: $(tail -n 3 "$W/cutgate.txt")"; step "cut gate" $t
  fi
  ln -f work/out_$TAG.mp4 work/final.mp4; [ -f work/out_$TAG.video.mp4 ] && ln -f work/out_$TAG.video.mp4 work/final.video.mp4; cp work/edit.json work/edit.last.json
  step "quick total" $T0; echo "$W/final.mp4" > "$W/DONE"
}

bg() { mkdir -p "$W"; HIZLI_FG=1 setsid nohup bash "$0" "$@" > "$W/hizli.out" 2>&1 < /dev/null & echo "$!" > "$W/hizli.pid"; echo "running in the background: tail $LOG"; }
case $CMD in
  prep) prep "$@" ;;
  go) if [ "${HIZLI_FG:-}" = 1 ]; then go "$@"; else bg go "$RUN" "$@"; fi ;;
  quick) if [ "${HIZLI_FG:-}" = 1 ]; then quick; else bg quick "$RUN"; fi ;;
  all) mkdir -p "$W"; prep "$@" > /dev/null || exit 1; model || { echo "model step did not finish: $W/model.log" | tee -a "$LOG"; exit 1; }; HIZLI_FG=1 go ;;
  *) echo "prep|go|quick|all"; exit 2 ;;
esac
