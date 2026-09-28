# Identify third-party jars: read META-INF/maven/<g>/<a>/pom.properties (g,a,v), fetch
# repo1.maven.org/<g>/<a>/<v>/<a>-<v>.jar.sha1, compare with the local jar's SHA-1.
import zipfile,glob,hashlib,os,io,json,urllib.request,sys,re,concurrent.futures as cf
MOD="/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules"; P="/mnt/c/Program Files/Niagara/5.0.0.28"
TRI=("com/tridium/","niagara/","javax/baja/")
items=[]
for j in sorted(glob.glob(MOD+"/*.jar")):
    z=zipfile.ZipFile(j)
    for n in z.namelist():
        if n.startswith("LIB-INF/") and n.endswith(".jar"): items.append(("LIB-INF",os.path.basename(j)+"!"+n,z.read(n)))
for j in sorted(glob.glob(P+"/bin/ext/**/*.jar",recursive=True))+sorted(glob.glob(P+"/etc/m2/**/*.jar",recursive=True)):
    items.append(("bin/ext" if "/bin/ext/" in j else "etc/m2",os.path.relpath(j,P),open(j,'rb').read()))
def work(it):
    kind,name,b=it; z=zipfile.ZipFile(io.BytesIO(b))
    cls=[n for n in z.namelist() if n.endswith(".class")]
    if cls and sum(n.startswith(TRI) for n in cls)/len(cls)>0.5: return None
    s1=hashlib.sha1(b).hexdigest(); gav=[]
    for n in z.namelist():
        if re.match(r"META-INF/maven/[^/]+/[^/]+/pom.properties$",n):
            p=dict(l.split("=",1) for l in z.read(n).decode("utf8","replace").splitlines() if "=" in l and not l.startswith("#"))
            gav.append((p.get("groupId","").strip(),p.get("artifactId","").strip(),p.get("version","").strip()))
    if not gav and kind=="etc/m2":
        parts=name.split("/"); gav=[(".".join(parts[2:-3]),parts[-3],parts[-2])]
    res="no-pom-properties"; match=None
    for g,a,v in gav:
        url=f"https://repo1.maven.org/maven2/{g.replace('.','/')}/{a}/{v}/{a}-{v}.jar.sha1"
        try:
            r=urllib.request.urlopen(url,timeout=20).read().decode().split()[0].strip()
            if r==s1: res="exact"; match=f"{g}:{a}:{v}"; break
            res="differs"; match=f"{g}:{a}:{v}"
        except Exception as e: res="not-on-central:"+type(e).__name__; match=f"{g}:{a}:{v}"
    return {"kind":kind,"name":name,"sha1":s1,"gav_candidates":gav,"result":res,"match":match}
with cf.ThreadPoolExecutor(8) as ex: out=[r for r in ex.map(work,items) if r]
json.dump(out,open(sys.argv[1],"w"),indent=1)
import collections; print(len(out),collections.Counter((o["kind"],o["result"].split(":")[0]) for o in out))
