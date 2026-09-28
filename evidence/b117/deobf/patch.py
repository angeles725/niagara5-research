# Detect-only preparation: copy .class entries with major version lowered to 61 so the
# ASM bundled in java-deobfuscator (rejects major 69) can parse them. Method bodies unchanged.
import sys,zipfile,os
src,dst=sys.argv[1],sys.argv[2]
n=0
with zipfile.ZipFile(src) as zi, zipfile.ZipFile(dst,"w",zipfile.ZIP_DEFLATED) as zo:
    for i in zi.infolist():
        if not i.filename.endswith(".class"): continue
        b=bytearray(zi.read(i))
        if b[:4]==b"\xca\xfe\xba\xbe" and int.from_bytes(b[6:8],"big")>61: b[6:8]=b"\x00\x3d"
        zo.writestr(i.filename,bytes(b)); n+=1
print(n)
