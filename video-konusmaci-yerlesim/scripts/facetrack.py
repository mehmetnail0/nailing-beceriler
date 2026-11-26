#!/usr/bin/env python3
"""Face track of the mezz (YuNet): per frame eye-centre x,y, inter-ocular distance, face box, in mezz pixels, plus "jumps": the frames where the
picture changes at once (a card, a flash frame, a cut in the source). usage: facetrack.py mezz.mp4 model.onnx out.json"""
import json, sys, cv2, numpy as np
cap = cv2.VideoCapture(sys.argv[1]); W0, H0 = int(cap.get(3)), int(cap.get(4)); k = 360 / W0
det = cv2.FaceDetectorYN.create(sys.argv[2], '', (360, int(H0 * k)), 0.6, 0.3, 5000)
out = []; dif = []; prev = None
while True:
    ok, f = cap.read()
    if not ok: break
    s = cv2.resize(f, (360, int(H0 * k)))
    th = cv2.resize(cv2.cvtColor(s, cv2.COLOR_BGR2GRAY), (32, 32), interpolation=cv2.INTER_AREA).astype(np.float32)
    dif.append(float(np.abs(th - prev).mean()) if prev is not None else 0.0); prev = th
    _, faces = det.detect(s)
    if faces is None or len(faces) == 0: out.append(None); continue
    fa = max(faces, key=lambda r: r[2] * r[3]); r = fa / k
    ex, ey = (r[4] + r[6]) / 2, (r[5] + r[7]) / 2
    out.append([round(float(ex), 1), round(float(ey), 1), round(float(np.hypot(r[6] - r[4], r[7] - r[5])), 1),
                round(float(r[0]), 1), round(float(r[1]), 1), round(float(r[2]), 1), round(float(r[3]), 1), round(float(fa[14]), 3)])
io = np.array([x[2] for x in out if x])
ref = np.percentile(io, 90) if len(io) else 0          # the speaker is the big face; faces on a screen, a poster or far behind are small
drop = 0
for i, x in enumerate(out):
    if x and x[2] < 0.5 * ref: out[i] = None; drop += 1
i = 0
while i < len(out):                                   # a face seen for under half a second is a flash on a screen, not the speaker
    if out[i] is None: i += 1; continue
    j = i
    while j < len(out) and out[j] is not None: j += 1
    if j - i < 15:
        for k in range(i, j): out[k] = None
        drop += j - i
    i = j
D = np.array(dif); jumps = [i for i in range(1, len(D)) if D[i] > 18 and D[i] > 4 * np.median(D[max(0, i - 15):i + 16])]
json.dump(dict(w=W0, h=H0, fps=30, speaker_io=round(float(ref), 1), jumps=jumps, f=out), open(sys.argv[3], 'w'))
print('frames', len(out), 'missing', sum(x is None for x in out), 'dropped small faces', drop, 'picture jumps', len(jumps))
