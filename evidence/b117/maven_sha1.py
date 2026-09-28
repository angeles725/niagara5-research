# Identify third-party jars by SHA-1 against Maven Central (search.maven.org solrsearch q=1:<sha1>).
import zipfile,glob,hashlib,os,io,json,time,urllib.request,sys
MOD="/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules"
P="/mnt/c/Program Files/Niagara/5.0.0.28"
TRI=("com/tridium/","niagara/","javax/baja/")
items=[]
def tri(zb):
    z=zipfile.ZipFile(io.BytesIO(zb)); c=[n for n in z.namelist() if n.endswith(".class")]
    return sum(n.startswith(TRI) for n in c), len(c)
for j in sorted(glob.glob(MOD+"/*.jar")):
    z=zipfile.ZipFile(j)
    for n in z.namelist():
        if n.startswith("LIB-INF/") and n.endswith(".jar"):
            b=z.read(n); items.append(("LIB-INF",os.path.basename(j)+"!"+n,b))
for j in sorted(glob.glob(P+"/bin/ext/**/*.jar",recursive=True))+sorted(glob.glob(P+"/etc/m2/**/*.jar",recursive=True)):
    b=open(j,'rb').read(); items.append(("bin/ext" if "/bin/ext/" in j else "etc/m2",os.path.relpath(j,P),b))
out=[]
for kind,name,b in items:
    t,c=tri(b)
    if c and t/c>0.5: continue
    s1=hashlib.sha1(b).hexdigest()
    url=f"https://search.maven.org/solrsearch/select?q=1:{s1}&rows=3&wt=json"
    try:
        d=json.load(urllib.request.urlopen(url,timeout=30)); docs=d["response"]["docs"]
        ids=[x["id"] for x in docs]; ec=[x.get("ec",[]) for x in docs]
        src=any("-sources.jar" in e for e in ec)
    except Exception as e:
        ids=["ERROR:"+type(e).__name__]; src=False
    out.append({"kind":kind,"name":name,"sha1":s1,"sha256":hashlib.sha256(b).hexdigest(),"maven":ids,"sources_jar":src})
    time.sleep(0.25)
json.dump(out,open(sys.argv[1],"w"),indent=1)
print(len(out))
