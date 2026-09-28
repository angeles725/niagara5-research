import re,sys,glob
DS="/home/cristian/niagara5-research/organized/docSource"
pairs={"ValueDocDecoder":"baja/niagara/io/ValueDocDecoder.java","Column":"rdb/niagara/rdb/ddl/Column.java",
"StyleUtils":"bajaui/niagara/ui/style/StyleUtils.java","BNumericWritable":"control/niagara/control/BNumericWritable.java"}
KW=set("if else for while return new this super null true false int long boolean byte char short double float void final static public private protected var case default switch break continue try catch finally throw throws instanceof String Object".split())
tot=hit=0
for k,rel in pairs.items():
  orig=open(f"{DS}/{rel}",errors="replace").read().splitlines()
  dec=open(glob.glob(f"ts/{k}/vf-cons/**/{k}.java",recursive=True)[0]).read().splitlines()
  t=h=0; misses=[]
  for d in dec:
    m=re.search(r"// (\d+)(?:\s|$)",d)
    if not m: continue
    n=int(m.group(1)); code=d[:m.start()]
    ids=set(re.findall(r"[A-Za-z_]\w{2,}",code))-KW
    if not ids: continue
    t+=1
    window=" ".join(orig[max(0,n-1):n+2]) if n<=len(orig) else ""
    oids=set(re.findall(r"[A-Za-z_]\w{2,}",window))
    if ids & oids: h+=1
    else: misses.append((n,code.strip()[:70]))
  tot+=t;hit+=h
  print(f"{k}: mapped-lines={t} token-overlap-hits={h} ({100*h/max(t,1):.1f}%) misses={misses[:3]}")
print(f"TOTAL {hit}/{tot} = {100*hit/tot:.2f}%")
