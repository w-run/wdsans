import json
cps = json.load(open("/workspace/wdsans2/build/box_lr.json"))
S = set(cps)
print("total %d" % len(S))
print()
probe = "昨晴暗晚旺昧昭昕晌晖明哲剖部陪都郵郭鄙叩叫叶吗味"
out = []
for ch in probe:
    out.append(ch + ("=IN " if ord(ch) in S else "=-- "))
print("probe: " + " ".join(out))
print()
print("first 60: " + "".join(chr(x) for x in sorted(S)[:60]))
print("last 30:  " + "".join(chr(x) for x in sorted(S)[-30:]))