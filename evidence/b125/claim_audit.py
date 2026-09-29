#!/usr/bin/env python3
"""B125 step 5: audit corpus claims that cite a Kotlin-plugin wall method. Each claim lists the class family (class + its nested/lambda classes)
and the constants/members the claim says the method touches; the check is `javap -v -p` over the shipped class family (ground truth, not the
Kotlin plugin and not Java mode). SAFE = every token found (and every 'absent' token absent); SUSPECT = a token is missing.
Usage: claim_audit.py > claim-audit.tsv"""
import glob, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b125_lib import *
P = "com/tridium/gradle/plugins"
_c = {}
def family(jar, cls):
    if (jar, cls) not in _c:
        fs = sorted(glob.glob(f"{extracted(jar)}/{cls}.class") + glob.glob(f"{extracted(jar)}/{cls}$*.class"))
        _c[(jar, cls)] = "\n".join(subprocess.run([f"{JAVA_BIN}/javap", "-v", "-p", f], capture_output=True, text=True).stdout.replace("\\'", "'").replace("\\\\", "\\") for f in fs), len(fs)
    return _c[(jar, cls)]
# (block, location, claim, jar, class, tokens present, tokens absent)
CLAIMS = [
 ("B36", "§36.5 :195-204", "GruntPlugin.apply() registers gruntBuild/gruntCi/gruntIntegration, wired through withPlugin(com.tridium.n-module)", "n-plugin", f"{P}/grunt/GruntPlugin",
  ['String gruntBuild', 'String gruntCi', 'String gruntIntegration', 'String com.tridium.n-module', 'TaskContainer.register'], []),
 ("B36", "§36.5 :195 'exactly 3'", "exactly 3 TaskContainer.register call sites (GruntBuildTask once, GruntCiTask twice) in the GruntPlugin class family", "n-plugin", f"{P}/grunt/GruntPlugin",
  ["count:invokeinterface.*TaskContainer.register:3", "class com/tridium/gradle/plugins/grunt/task/GruntBuildTask", "class com/tridium/gradle/plugins/grunt/task/GruntCiTask"], []),
 ("B36", "§36.1 :60-66, :111-119", "findPackage() carries the first-party error text about 'npm', PATH and the Gradle property nodeHome", "n-plugin", f"{P}/node/task/CheckNodePackageGloballyInstalled",
  ["Could not start 'npm'. Ensure 'node' and 'npm' are available on your PATH", "nodeHome"], []),
 ("B36", "§36.3 :157", "wireSkipJsConvention wires a skipjs property and onlyIf skips the task when it is true", "n-plugin", f"{P}/node/task/JavaScriptTaskKt",
  ["String skipjs", "onlyIf", "String true"], []),
 ("B36", "§36.4 :181-186", "YarnWorkspacePlugin.apply refuses the root project and publishes yarnWorkspaceElements", "n-plugin", f"{P}/node/YarnWorkspacePlugin",
  ["This plugin must not be applied to the root project of a build", "yarnWorkspaceElements", "IllegalArgumentException"], []),
 ("B74", "§74.3 :212-226", "RootProjectNiagaraNativePlugin.apply: depth != 0 throws IllegalStateException; two devkit regexes; devkitProperties service; dumpDevkits task", "n-plugin", f"{P}/natives/RootProjectNiagaraNativePlugin",
  ["Can only be applied to the root project", r"^devkit.*\.properties$", r"^local\.devkit.*\.properties$", "devkitProperties", "dumpDevkits", "getDepth", "IllegalStateException"], []),
 ("B89", "§89.4 :94-111", "NativePlatformFactory.create: read-only guard, new NiagaraNativePlatform(name), three NiagaraNativePluginKt configuration calls, one TaskContainer.register", "n-plugin", f"{P}/natives/extension/DefaultNiagaraNativeExtension$NativePlatformFactory",
  ["getPlatformsReadOnly", "IllegalStateException", "NiagaraNativePlatform.\"<init>\":(Ljava/lang/String;)V", "createLinkPathConfiguration", "createRuntimeElementsConfiguration", "createBinaryProducerConfigurations", "TaskContainer.register"], []),
 ("B2", "§2.6 :355-361", "NiagaraAnnotationProcessorsPlugin.apply builds one niagaraAnnotationProcessor configuration that annotationProcessor and moduleTestAnnotationProcessor extend", "n-plugin", f"{P}/module/NiagaraAnnotationProcessorsPlugin",
  ["String niagaraAnnotationProcessor", "String annotationProcessor", "String moduleTestAnnotationProcessor", "extendsFrom"], []),
 ("B2", "§2.7 :437-441", "NiagaraJavaPlugin.apply adds compact3, limitModules, apt and modulePath argument providers to JavaCompile", "n-plugin", f"{P}/java/NiagaraJavaPlugin",
  ["String java", "Compact3ArgumentProvider", "LimitModulesArgumentProvider", "AnnotationProcessorArgumentProvider", "ModulePathArgumentProvider", "getCompilerArgumentProviders"], []),
 ("B51", "§51 :73-78", "NiagaraJavaPlugin has no subprojects/allprojects traversal (per-module application)", "n-plugin", f"{P}/java/NiagaraJavaPlugin",
  ["withPlugin"], ["getSubprojects", "getAllprojects", "subprojects", "allprojects"]),
 ("B2", "§2.3 :192-196; B51 :121", "VendorExtension.defaultModuleVersion sets ModuleXml.vendorVersion; defaultVendor sets ModuleXml.vendor convention", "n-plugin", f"{P}/vendor/VendorExtension",
  ["getVendorVersion", "getVendor", "Property.set", "Property.convention"], []),
 ("B108", "§108.2 :183", "registerModuleTasks jarTask$1$4.execute calls CopySpec.into(\"LIB-INF\")", "n-plugin", f"{P}/module/NiagaraModulePlugin$registerModuleTasks$jarTask$1$4",
  ["String LIB-INF", "CopySpec.into"], []),
 ("B89", "§89.x :165", "registerModuleTasks$lambda$2$0 is the Compact3 provider wiring (uses ExtensionsKt.isCompact3)", "n-plugin", f"{P}/module/NiagaraModulePlugin",
  ["isCompact3", "Compact3ArgumentProvider"], []),
]
print("block\tcited_location\tclaim\tverdict\tmissing_or_unexpected\tclass_files")
for blk, loc, claim, jar, cls, present, absent in CLAIMS:
    txt, n = family(jar, cls)
    def has(t):
        if t.startswith("count:"):
            _, rx, n = t.split(":"); return len(re.findall(rx, txt)) == int(n)
        return re.search(re.escape(t), txt) is not None
    miss = [t for t in present if not has(t)]
    unexp = [t for t in absent if re.search(re.escape(t), txt)]
    v = "SAFE" if not miss and not unexp else "SUSPECT"
    print(f"{blk}\t{loc}\t{claim}\t{v}\t{'; '.join(['missing ' + m for m in miss] + ['present ' + u for u in unexp]) or '-'}\t{n}")
