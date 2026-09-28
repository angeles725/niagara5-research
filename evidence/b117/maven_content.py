# For jars whose whole-file SHA-1 differs from Maven Central: download the upstream jar and compare every
# non-META-INF entry byte-for-byte (a vendor re-signature only adds/changes META-INF/*).
import json,zipfile,io,urllib.request,hashlib,sys,os,concurrent.futures as cf
S=sys.argv[1]; P="/mnt/c/Program Files/Niagara/5.0.0.28"; MOD="/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules"
d=json.load(open(S+"/maven-repo1.json"))
def local(o):
    if o["kind"]=="LIB-INF":
        j,n=o["name"].split("!",1); return zipfile.ZipFile(io.BytesIO(zipfile.ZipFile(MOD+"/"+j).read(n)))
    return zipfile.ZipFile(P+"/"+o["name"])
def work(o):
    if o["result"]!="differs": return o
    g,a,v=o["match"].split(":")
    try:
        up=zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(f"https://repo1.maven.org/maven2/{g.replace('.','/')}/{a}/{v}/{a}-{v}.jar",timeout=120).read()))
    except Exception as e:
        o["content"]="download-failed"; return o
    L=local(o)
    def ents(z): return {i.filename:hashlib.sha256(z.read(i)).hexdigest() for i in z.infolist() if not i.is_dir() and not i.filename.startswith("META-INF/")}
    le,ue=ents(L),ents(up)
    diff=[k for k in set(le)|set(ue) if le.get(k)!=ue.get(k)]
    o["content"]="identical-non-META-INF" if not diff else f"differs:{len(diff)}"
    o["content_diff_sample"]=sorted(diff)[:5]; o["entries"]=len(le)
    o["meta_inf_local"]=sorted(n for n in L.namelist() if n.startswith("META-INF/") and n.upper().endswith((".SF",".RSA",".EC",".DSA")))
    return o
with cf.ThreadPoolExecutor(8) as ex: out=list(ex.map(work,d))
json.dump(out,open(S+"/maven-repo1.json","w"),indent=1)
import collections; print(collections.Counter((o["kind"],o["result"].split(":")[0],o.get("content","-").split(":")[0]) for o in out))
for o in out:
    if o.get("content","").startswith(("differs","download")) or o["result"].startswith("not-on"): print(o["name"],o["match"],o["result"],o.get("content"),o.get("content_diff_sample"))
