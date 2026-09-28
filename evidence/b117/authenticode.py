import sys,struct,subprocess
for p in sys.argv[1:]:
    b=open(p,'rb').read()
    pe=struct.unpack_from('<I',b,0x3c)[0]; opt=pe+24
    magic=struct.unpack_from('<H',b,opt)[0]
    dd=opt+(96 if magic==0x10b else 112)
    off,size=struct.unpack_from('<II',b,dd+8*4)
    if not size: print(p.split('/')[-1],"UNSIGNED"); continue
    blob=b[off+8:off+size]
    r=subprocess.run(["openssl","pkcs7","-inform","DER","-print_certs","-noout"],input=blob,capture_output=True)
    subj=[l for l in r.stdout.decode().splitlines() if l.startswith("subject")]
    leaf=[s for s in subj if "DigiCert" not in s and "Microsoft Root" not in s and "Time" not in s]; print(p.split("/")[-1],"SIGNED",leaf[:1] or subj[:1])
