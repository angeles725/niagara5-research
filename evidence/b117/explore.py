import zipfile, glob, os, collections, sys, json
MOD="/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules"
res={}
ext=collections.Counter(); nested=[]; mr=[]
for j in sorted(glob.glob(MOD+"/*.jar")):
    z=zipfile.ZipFile(j)
    names=z.namelist()
    for n in names:
        if n.endswith('/'): continue
        e=os.path.splitext(n)[1].lower()
        ext[e]+=1
        if e in ('.jar','.zip','.war','.ear','.jmod'): nested.append((os.path.basename(j),n,z.getinfo(n).file_size))
        if n.startswith('META-INF/versions/'): mr.append((os.path.basename(j),n))
    try:
        mf=z.read('META-INF/MANIFEST.MF').decode('utf8','replace')
        if 'Multi-Release' in mf: print("MRflag",os.path.basename(j),[l for l in mf.splitlines() if 'Multi' in l])
    except KeyError: pass
print(ext.most_common(60))
print("nested",len(nested)); [print(x) for x in nested[:80]]
print("mr",len(mr)); [print(x) for x in mr[:40]]
