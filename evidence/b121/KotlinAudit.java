// B121: bytecode + kotlin.Metadata audit of the Kotlin-compiled Tridium build jars.
// Deps (classpath): ASM 9.10.1 (Niagara bin/ext), kotlin-stdlib 2.4.10 (Niagara bin/ext),
//                   kotlin-metadata-jvm 2.4.10 (Maven Central, sha1-verified; see README.md).
// Usage: java -cp ... KotlinAudit <outDir> <jar>...
// Writes: <outDir>/summary.tsv, <outDir>/classes.tsv, <outDir>/residual.tsv,
//         <outDir>/kotlin-signatures/<jarname>/<binary class name>.kt.txt   (out of git)
import kotlin.Metadata;
import kotlin.metadata.*;
import kotlin.metadata.jvm.*;
import org.objectweb.asm.*;
import org.objectweb.asm.tree.*;

import java.io.*;
import java.lang.reflect.Proxy;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.zip.*;

public class KotlinAudit {
    static final Map<String, Map<String, long[]>> SUM = new TreeMap<>(); // jar -> category -> {classes, occurrences}
    static final Map<String, Map<String, Integer>> TOP = new TreeMap<>(); // category -> key -> count
    static final List<String> CLASS_ROWS = new ArrayList<>();
    static final List<String> RESIDUAL = new ArrayList<>();
    static Path outDir;

    static void bump(String jar, Set<String> seen, String cat, long n) {
        if (n == 0) return;
        long[] a = SUM.computeIfAbsent(jar, k -> new TreeMap<>()).computeIfAbsent(cat, k -> new long[2]);
        if (seen.add(cat)) a[0]++;
        a[1] += n;
    }

    static void top(String cat, String key, int n) {
        TOP.computeIfAbsent(cat, k -> new HashMap<>()).merge(key, n, Integer::sum);
    }

    public static void main(String[] args) throws Exception {
        outDir = Paths.get(args[0]);
        Files.createDirectories(outDir);
        for (int i = 1; i < args.length; i++) auditJar(Paths.get(args[i]));
        writeOutputs();
    }

    static void auditJar(Path jar) throws Exception {
        String jarName = jar.getFileName().toString().replaceAll("-\\d[\\d.]*\\.jar$", "");
        try (ZipFile zf = new ZipFile(jar.toFile())) {
            List<? extends ZipEntry> es = Collections.list(zf.entries());
            for (ZipEntry e : es) {
                if (!e.getName().endsWith(".class") || e.getName().startsWith("META-INF/")) continue;
                byte[] b = zf.getInputStream(e).readAllBytes();
                ClassNode cn = new ClassNode();
                new ClassReader(b).accept(cn, ClassReader.SKIP_FRAMES);
                analyse(jarName, cn);
            }
        }
    }

    static Metadata metaOf(ClassNode cn) {
        if (cn.visibleAnnotations == null) return null;
        for (AnnotationNode an : cn.visibleAnnotations) {
            if (!"Lkotlin/Metadata;".equals(an.desc)) continue;
            Map<String, Object> v = new HashMap<>();
            for (int i = 0; i < an.values.size(); i += 2) v.put((String) an.values.get(i), an.values.get(i + 1));
            return (Metadata) Proxy.newProxyInstance(Metadata.class.getClassLoader(), new Class[]{Metadata.class}, (p, m, a) -> {
                String n = m.getName();
                switch (n) {
                    case "k": return v.getOrDefault("k", 1);
                    case "xi": return v.getOrDefault("xi", 0);
                    case "xs": return v.getOrDefault("xs", "");
                    case "pn": return v.getOrDefault("pn", "");
                    case "mv": case "bv": return intArr(v.get(n));
                    case "d1": case "d2": return strArr(v.get(n));
                    case "annotationType": return Metadata.class;
                    case "toString": return "@kotlin.Metadata";
                    case "hashCode": return 1;
                    case "equals": return p == a[0];
                }
                return null;
            });
        }
        return null;
    }

    static int[] intArr(Object o) {
        if (!(o instanceof List<?> l)) return new int[0];
        int[] r = new int[l.size()];
        for (int i = 0; i < r.length; i++) r[i] = (Integer) l.get(i);
        return r;
    }

    static String[] strArr(Object o) {
        if (!(o instanceof List<?> l)) return new String[0];
        return l.stream().map(String::valueOf).toArray(String[]::new);
    }

    // ---------------------------------------------------------------- per-class analysis
    static void analyse(String jar, ClassNode cn) throws IOException {
        Metadata md = metaOf(cn);
        if (md == null) return;
        Set<String> seen = new HashSet<>();
        Map<String, Long> c = new TreeMap<>();
        bump(jar, seen, "kotlin-classes", 1);
        int k = md.k();
        String kindName = switch (k) { case 1 -> "class"; case 2 -> "file-facade"; case 3 -> "synthetic"; case 4 -> "multifile-facade"; case 5 -> "multifile-part"; default -> "k" + k; };
        bump(jar, seen, "kind:" + kindName, 1);
        bump(jar, seen, "metadata-version:" + Arrays.toString(md.mv()).replace(" ", ""), 1);
        if (cn.name.endsWith("Kt")) bump(jar, seen, "name-ends-Kt", 1);

        KotlinClassMetadata km = null;
        String metaErr = null;
        try { km = KotlinClassMetadata.readStrict(md); } catch (Throwable t) { metaErr = t.toString(); }
        if (km == null) { bump(jar, seen, "metadata-decode-FAILED", 1); RESIDUAL.add(jar + "\t" + cn.name + "\tdecode-failed\t" + metaErr); }

        KmClass kc = null; KmPackage kp = null; KmFunction lam = null;
        if (km instanceof KotlinClassMetadata.Class x) kc = x.getKmClass();
        else if (km instanceof KotlinClassMetadata.FileFacade x) kp = x.getKmPackage();
        else if (km instanceof KotlinClassMetadata.MultiFileClassPart x) kp = x.getKmPackage();
        else if (km instanceof KotlinClassMetadata.SyntheticClass x) {
            KmLambda l = x.getKmLambda(); if (l != null) lam = l.getFunction();
            bump(jar, seen, l != null ? "meta:synthetic-class-WITH-lambda-declaration" : "meta:synthetic-class-WITHOUT-any-declaration(no d1 payload)", 1);
        }

        // ---- declaration inventory from metadata
        List<KmFunction> fns = new ArrayList<>(); List<KmProperty> props = new ArrayList<>(); List<KmConstructor> ctors = new ArrayList<>();
        if (kc != null) { fns.addAll(kc.getFunctions()); props.addAll(kc.getProperties()); ctors.addAll(kc.getConstructors()); }
        if (kp != null) { fns.addAll(kp.getFunctions()); props.addAll(kp.getProperties()); }
        if (lam != null) fns.add(lam);
        bump(jar, seen, "decl:functions", fns.size());
        bump(jar, seen, "decl:properties", props.size());
        bump(jar, seen, "decl:constructors", ctors.size());
        Set<String> declared = new HashSet<>(); // name+desc of JVM members explained by declarations
        Set<String> declaredFields = new HashSet<>();
        Set<String> fnNames = new HashSet<>(), delegNames = new HashSet<>(), propAccessorNames = new HashSet<>();
        for (KmFunction f : fns) {
            JvmMethodSignature s = JvmExtensionsKt.getSignature(f);
            if (s != null) declared.add(s.getName() + s.getDescriptor()); else bump(jar, seen, "meta:fun-without-jvm-signature(derived by compiler)", 1);
            fnNames.add(f.getName());
            if (Attributes.getKind(f) == MemberKind.DELEGATION) delegNames.add(f.getName());
            if (Attributes.isInline(f)) bump(jar, seen, "meta:inline-fun", 1);
            if (Attributes.isSuspend(f)) bump(jar, seen, "meta:suspend-fun", 1);
            if (Attributes.isOperator(f)) bump(jar, seen, "meta:operator-fun", 1);
            if (Attributes.isInfix(f)) bump(jar, seen, "meta:infix-fun", 1);
            if (Attributes.isTailrec(f)) bump(jar, seen, "meta:tailrec-fun", 1);
            if (f.getReceiverParameterType() != null) bump(jar, seen, "meta:extension-fun", 1);
            if (!f.getContextParameters().isEmpty() || !f.getContextReceiverTypes().isEmpty()) bump(jar, seen, "meta:context-param-fun", 1);
            if (Attributes.getVisibility(f) == Visibility.INTERNAL) {
                bump(jar, seen, "meta:internal-fun", 1);
                if (s != null && !s.getName().equals(f.getName())) bump(jar, seen, "meta:internal-fun-name-mangled", 1);
            }
            if (Attributes.getKind(f) == MemberKind.SYNTHESIZED) bump(jar, seen, "meta:synthesized-fun(data component/copy)", 1);
            if (Attributes.getKind(f) == MemberKind.DELEGATION) bump(jar, seen, "meta:delegation-fun(by)", 1);
            for (KmTypeParameter tp : f.getTypeParameters()) if (Attributes.isReified(tp)) bump(jar, seen, "meta:reified-type-param", 1);
            boolean anyDefault = false;
            for (KmValueParameter vp : f.getValueParameters()) {
                if (Attributes.getDeclaresDefaultValue(vp)) { anyDefault = true; bump(jar, seen, "meta:default-value-params", 1); }
                if (vp.getVarargElementType() != null) bump(jar, seen, "meta:vararg-params", 1);
                if (Attributes.isCrossinline(vp)) bump(jar, seen, "meta:crossinline-params", 1);
                if (Attributes.isNoinline(vp)) bump(jar, seen, "meta:noinline-params", 1);
                nullInfo(jar, seen, vp.getType());
            }
            if (anyDefault) bump(jar, seen, "meta:fun-with-defaults", 1);
            nullInfo(jar, seen, f.getReturnType());
        }
        for (KmConstructor ct : ctors) {
            JvmMethodSignature s = JvmExtensionsKt.getSignature(ct);
            if (s != null) declared.add(s.getName() + s.getDescriptor());
            boolean anyDefault = false;
            for (KmValueParameter vp : ct.getValueParameters()) {
                if (Attributes.getDeclaresDefaultValue(vp)) { anyDefault = true; bump(jar, seen, "meta:default-value-params", 1); }
                nullInfo(jar, seen, vp.getType());
            }
            if (anyDefault) bump(jar, seen, "meta:ctor-with-defaults", 1);
            if (Attributes.isSecondary(ct)) bump(jar, seen, "meta:secondary-ctor", 1);
        }
        for (KmProperty p : props) {
            String pn = p.getName(), cap = pn.isEmpty() ? pn : Character.toUpperCase(pn.charAt(0)) + pn.substring(1);
            propAccessorNames.add("get" + cap); propAccessorNames.add("set" + cap); propAccessorNames.add(pn);
            if (pn.startsWith("is") && pn.length() > 2) propAccessorNames.add("set" + pn.substring(2));
            if (JvmExtensionsKt.getGetterSignature(p) == null) bump(jar, seen, "meta:property-without-getter-signature(default accessor)", 1);
            for (JvmMethodSignature s : new JvmMethodSignature[]{JvmExtensionsKt.getGetterSignature(p), JvmExtensionsKt.getSetterSignature(p),
                    JvmExtensionsKt.getSyntheticMethodForAnnotations(p), JvmExtensionsKt.getSyntheticMethodForDelegate(p)})
                if (s != null) declared.add(s.getName() + s.getDescriptor());
            JvmFieldSignature fs = JvmExtensionsKt.getFieldSignature(p);
            if (fs != null) declaredFields.add(fs.getName());
            if (Attributes.isVar(p)) bump(jar, seen, "meta:var-property", 1); else bump(jar, seen, "meta:val-property", 1);
            if (Attributes.isLateinit(p)) bump(jar, seen, "meta:lateinit-property", 1);
            if (Attributes.isConst(p)) bump(jar, seen, "meta:const-property", 1);
            if (Attributes.isDelegated(p)) bump(jar, seen, "meta:delegated-property", 1);
            if (p.getReceiverParameterType() != null) bump(jar, seen, "meta:extension-property", 1);
            if (Attributes.getVisibility(p) == Visibility.PRIVATE && JvmExtensionsKt.getGetterSignature(p) == null) bump(jar, seen, "meta:private-property-without-getter", 1);
            nullInfo(jar, seen, p.getReturnType());
        }
        if (kc != null) {
            ClassKind ck = Attributes.getKind(kc);
            bump(jar, seen, "meta:classkind:" + ck, 1);
            if (Attributes.isData(kc)) bump(jar, seen, "meta:data-class", 1);
            if (Attributes.isValue(kc)) bump(jar, seen, "meta:value-class", 1);
            if (Attributes.isFunInterface(kc)) bump(jar, seen, "meta:fun-interface", 1);
            if (Attributes.getModality(kc) == Modality.SEALED) bump(jar, seen, "meta:sealed-class", 1);
            if (Attributes.getVisibility(kc) == Visibility.INTERNAL) bump(jar, seen, "meta:internal-class", 1);
            if (kc.getCompanionObject() != null) bump(jar, seen, "meta:has-companion", 1);
            if (ck == ClassKind.COMPANION_OBJECT) bump(jar, seen, "meta:is-companion", 1);
            if (!kc.getEnumEntries().isEmpty()) bump(jar, seen, "meta:enum-entries", kc.getEnumEntries().size());
            for (KmTypeParameter tp : kc.getTypeParameters()) bump(jar, seen, "meta:class-type-params", 1);
        }

        // ---- bytecode census
        String companionDesc = "L" + cn.name + "$Companion;";
        boolean hasCompanionField = cn.fields.stream().anyMatch(f -> f.name.equals("Companion") && f.desc.equals(companionDesc));
        if (hasCompanionField) bump(jar, seen, "bc:Companion-static-field", 1);
        if (cn.fields.stream().anyMatch(f -> f.name.equals("INSTANCE") && f.desc.equals("L" + cn.name + ";"))) bump(jar, seen, "bc:object-INSTANCE-field", 1);
        boolean isEnum = (cn.access & Opcodes.ACC_ENUM) != 0;
        boolean isDataCls = kc != null && Attributes.isData(kc);
        long explained = 0, unexplained = 0;
        Map<String, Long> unexplainedKinds = new TreeMap<>();
        boolean isSusp = cn.superName != null && (cn.superName.equals("kotlin/coroutines/jvm/internal/ContinuationImpl") || cn.superName.equals("kotlin/coroutines/jvm/internal/SuspendLambda") || cn.superName.equals("kotlin/coroutines/jvm/internal/RestrictedSuspendLambda") || cn.superName.equals("kotlin/coroutines/jvm/internal/BaseContinuationImpl"));
        if (isSusp) bump(jar, seen, "bc:coroutine-state-machine-class(" + cn.superName.substring(cn.superName.lastIndexOf('/') + 1) + ")", 1);
        if (cn.superName != null && cn.superName.equals("kotlin/jvm/internal/Lambda")) bump(jar, seen, "bc:kotlin-Lambda-subclass", 1);
        if (cn.interfaces.stream().anyMatch(i -> i.startsWith("kotlin/jvm/functions/Function"))) bump(jar, seen, "bc:implements-FunctionN", 1);
        if (cn.name.endsWith("$WhenMappings")) bump(jar, seen, "bc:WhenMappings-class", 1);
        if (cn.name.endsWith("$DefaultImpls")) bump(jar, seen, "bc:DefaultImpls-class", 1);

        for (MethodNode m : cn.methods) {
            boolean synth = (m.access & Opcodes.ACC_SYNTHETIC) != 0, stat = (m.access & Opcodes.ACC_STATIC) != 0, bridge = (m.access & Opcodes.ACC_BRIDGE) != 0;
            String key = m.name + m.desc;
            String cls; // classification of the JVM method
            boolean fwd = false;
            if (stat && !synth && hasCompanionField && !m.name.startsWith("<")) {
                for (AbstractInsnNode in : m.instructions)
                    if (in instanceof MethodInsnNode mi && mi.owner.equals(cn.name + "$Companion") && mi.name.equals(m.name)) { fwd = true; break; }
            }
            if (declared.contains(key)) cls = "declared";
            else if (fwd) cls = "jvmstatic-forwarder";
            else if (!m.name.endsWith("$default") && (fnNames.contains(m.name) || fnNames.stream().anyMatch(n -> m.name.startsWith(n + "$") || m.name.startsWith(n + "-")))) cls = "declared(by-name; signature derived)";
            else if (propAccessorNames.contains(m.name)) cls = "declared(property accessor by-name)";
            else if (delegNames.contains(m.name)) cls = "class-delegation-generated";
            else if (readOnlyStub(m)) { cls = "read-only-collection-mutator-stub"; bump(jar, seen, "bc:read-only-collection-mutator-stub(throws UnsupportedOperationException)", 1); }
            else if (k == 3 && !synth && !stat && !m.name.startsWith("<")) cls = "synthetic-class-member(lambda/SAM body)";
            else if (m.name.equals("<clinit>")) cls = "clinit";
            else if (m.name.endsWith("$default")) { cls = "default-args-synthetic"; bump(jar, seen, "bc:$default-synthetic-method", 1); }
            else if (m.name.equals("<init>") && m.desc.endsWith("Lkotlin/jvm/internal/DefaultConstructorMarker;)V")) { cls = "default-args-ctor-synthetic"; bump(jar, seen, "bc:ctor-default-marker-synthetic", 1); }
            else if (m.name.startsWith("access$")) cls = "access$-synthetic";
            else if (bridge) cls = "bridge";
            else if (m.name.contains("$lambda$") || m.name.matches(".*\\$lambda\\$\\d+")) cls = "lambda-body";
            else if (isEnum && (m.name.equals("values") || m.name.equals("valueOf") || m.name.equals("$values") || m.name.equals("getEntries"))) cls = "enum-generated";
            else if (isDataCls && (m.name.matches("component\\d+") || m.name.equals("copy") || m.name.equals("equals") || m.name.equals("hashCode") || m.name.equals("toString"))) cls = "data-class-generated";
            else if (m.name.equals("box-impl") || m.name.equals("unbox-impl") || m.name.endsWith("-impl") || m.name.contains("-impl$")) cls = "value-class-impl";
            else if (m.name.startsWith("<") ) cls = "ctor-undeclared";
            else if (synth) cls = "other-synthetic";
            else if (isSusp) cls = "coroutine-class-member";
            else if (cn.superName != null && cn.superName.equals("kotlin/jvm/internal/Lambda") ) cls = "lambda-class-member";
            else if (cn.interfaces.stream().anyMatch(i -> i.startsWith("kotlin/jvm/functions/Function")) && (m.name.equals("invoke") || m.name.equals("getArity"))) cls = "lambda-class-member";
            else cls = "UNEXPLAINED";
            top("method-class:" + jar, cls, 1);
            if (cls.startsWith("declared")) explained++;
            else if (cls.equals("UNEXPLAINED")) { unexplained++; RESIDUAL.add(jar + "\t" + cn.name + "\t" + m.name + m.desc + "\taccess=0x" + Integer.toHexString(m.access)); }
            else unexplainedKinds.merge(cls, 1L, Long::sum);

            // @JvmStatic forwarders
            if (stat && !synth && !m.name.startsWith("<") && hasCompanionField) {
                for (AbstractInsnNode in : m.instructions) {
                    if (in instanceof MethodInsnNode mi && mi.owner.equals(cn.name + "$Companion") && mi.name.equals(m.name)) {
                        bump(jar, seen, "bc:JvmStatic-companion-forwarder", 1); break;
                    }
                }
            }
            if (stat && !synth && kc != null && Attributes.getKind(kc) == ClassKind.OBJECT && !m.name.startsWith("<") && !isEnum) bump(jar, seen, "bc:static-method-in-object(@JvmStatic)", 1);
            if (stat && !synth && kc != null && Attributes.getKind(kc) == ClassKind.COMPANION_OBJECT) bump(jar, seen, "bc:static-method-in-companion", 1);

            // last param Continuation => suspend
            if (m.desc.contains("Lkotlin/coroutines/Continuation;)")) bump(jar, seen, "bc:method-with-Continuation-last-param(suspend)", 1);

            if (m.localVariables != null) for (LocalVariableNode lv : m.localVariables) {
                if (lv.name.startsWith("$i$f$")) { bump(jar, seen, "bc:inlined-fun-callsite-marker($i$f$)", 1); top("inline-fun-expanded", lv.name.substring(5), 1); }
                else if (lv.name.startsWith("$i$a$")) bump(jar, seen, "bc:inlined-lambda-marker($i$a$)", 1);
                else if (lv.name.startsWith("$this$")) bump(jar, seen, "bc:extension-receiver-lvt($this$)", 1);
                else if (lv.name.startsWith("$$") && false) { }
            }
            for (AbstractInsnNode in : m.instructions) {
                if (in instanceof MethodInsnNode mi) {
                    if (mi.getOpcode() == Opcodes.INVOKESTATIC && mi.owner.equals("kotlin/jvm/internal/Intrinsics")) {
                        bump(jar, seen, "bc:Intrinsics-call", 1);
                        bump(jar, seen, "bc:Intrinsics." + mi.name, 1);
                    }
                    if (mi.getOpcode() == Opcodes.INVOKESTATIC && mi.name.endsWith("$default") && !mi.owner.equals(cn.name)) bump(jar, seen, "bc:$default-callsite(other class)", 1);
                    if (mi.getOpcode() == Opcodes.INVOKESTATIC && mi.name.endsWith("$default") && mi.owner.equals(cn.name)) bump(jar, seen, "bc:$default-callsite(same class)", 1);
                    if (mi.getOpcode() == Opcodes.INVOKESTATIC && mi.owner.startsWith("kotlin/") && mi.owner.contains("Kt")) { bump(jar, seen, "bc:kotlin-stdlib-Kt-static-call(ext fun)", 1); top("stdlib-Kt-owner", mi.owner + "." + mi.name, 1); }
                    if (mi.owner.equals("kotlin/jvm/internal/Intrinsics") && mi.name.equals("reifiedOperationMarker")) bump(jar, seen, "bc:reifiedOperationMarker", 1);
                    if (mi.owner.startsWith("kotlin/jvm/internal/Ref$")) bump(jar, seen, "bc:captured-var-Ref-box", 1);
                    if (mi.owner.equals("kotlin/LazyKt") && mi.name.equals("lazy")) bump(jar, seen, "bc:lazy-delegate-call", 1);
                } else if (in instanceof InvokeDynamicInsnNode di) {
                    if (di.bsm.getOwner().equals("java/lang/invoke/LambdaMetafactory")) bump(jar, seen, "bc:indy-lambda(LambdaMetafactory)", 1);
                    else if (di.bsm.getOwner().equals("java/lang/invoke/StringConcatFactory")) bump(jar, seen, "bc:indy-string-concat", 1);
                    else bump(jar, seen, "bc:indy-other", 1);
                } else if (in instanceof FieldInsnNode fi && fi.getOpcode() == Opcodes.GETSTATIC) {
                    if (fi.owner.endsWith("$WhenMappings")) bump(jar, seen, "bc:WhenMappings-read(when on enum)", 1);
                } else if (in instanceof LdcInsnNode ld && ld.cst instanceof String s && s.startsWith("This function has a reified type parameter")) {
                    bump(jar, seen, "bc:reified-inline-stub-method(throws UnsupportedOperationException)", 1);
                }
            }
        }
        for (FieldNode f : cn.fields) {
            String cat;
            if (declaredFields.contains(f.name)) cat = "declared-property-backing";
            else if (f.name.equals("Companion")) cat = "Companion";
            else if (f.name.equals("INSTANCE")) cat = "INSTANCE";
            else if (f.name.endsWith("$delegate")) cat = "delegate";
            else if (f.name.startsWith("$$")) cat = "compiler-$$";
            else if ((f.access & Opcodes.ACC_SYNTHETIC) != 0) cat = "synthetic";
            else if (isEnum && (f.access & Opcodes.ACC_ENUM) != 0) cat = "enum-constant";
            else if (isEnum && f.name.equals("$VALUES")) cat = "enum-generated";
            else if (isEnum && f.name.equals("$ENTRIES")) cat = "enum-generated";
            else if (f.name.startsWith("label") || f.name.startsWith("L$") || f.name.startsWith("I$") || f.name.equals("result")) cat = isSusp ? "coroutine-state" : "other";
            else if (f.name.startsWith("this$") || f.name.startsWith("$")) cat = "captured/outer";
            else cat = "other";
            top("field-class:" + jar, cat, 1);
        }
        if (unexplained > 0) bump(jar, seen, "residual:classes-with-unexplained-jvm-methods", 1);

        CLASS_ROWS.add(String.join("\t", jar, cn.name, kindName, String.valueOf(cn.version & 0xffff), String.valueOf(fns.size()), String.valueOf(props.size()), String.valueOf(ctors.size()),
                String.valueOf(cn.methods.size()), String.valueOf(explained), String.valueOf(unexplainedKinds.values().stream().mapToLong(Long::longValue).sum()), String.valueOf(unexplained)));

        // ---- Kotlin declaration listing (out of git)
        if (km != null) writeListing(jar, cn, kc, kp, lam, kindName);
    }

    static boolean readOnlyStub(MethodNode m) {
        for (AbstractInsnNode in : m.instructions)
            if (in instanceof LdcInsnNode ld && "Operation is not supported for read-only collection".equals(ld.cst)) return true;
        return false;
    }

    static void nullInfo(String jar, Set<String> seen, KmType t) {
        if (t == null) return;
        if (Attributes.isNullable(t)) bump(jar, seen, "meta:nullable-types-in-signatures", 1);
        for (KmTypeProjection tp : t.getArguments()) {
            if (tp.getType() != null) {
                if (Attributes.isNullable(tp.getType())) bump(jar, seen, "meta:nullable-TYPE-ARGUMENT(not in JVM generic signature)", 1);
                nullInfo(jar, seen, tp.getType());
            }
        }
    }

    // ---------------------------------------------------------------- listing
    static String ty(KmType t, Map<Integer, String> tps) {
        if (t == null) return "?";
        StringBuilder sb = new StringBuilder();
        if (Attributes.isSuspend(t)) sb.append("suspend ");
        KmClassifier c = t.getClassifier();
        if (c instanceof KmClassifier.Class cc) sb.append(cc.getName().replace('/', '.'));
        else if (c instanceof KmClassifier.TypeParameter tp) sb.append(tps.getOrDefault(tp.getId(), "T#" + tp.getId()));
        else if (c instanceof KmClassifier.TypeAlias ta) sb.append(ta.getName().replace('/', '.'));
        if (!t.getArguments().isEmpty()) {
            sb.append('<');
            for (int i = 0; i < t.getArguments().size(); i++) {
                KmTypeProjection p = t.getArguments().get(i);
                if (i > 0) sb.append(", ");
                if (p.getType() == null) sb.append('*');
                else {
                    if (p.getVariance() == KmVariance.IN) sb.append("in ");
                    else if (p.getVariance() == KmVariance.OUT) sb.append("out ");
                    sb.append(ty(p.getType(), tps));
                }
            }
            sb.append('>');
        }
        if (Attributes.isNullable(t)) sb.append('?');
        return sb.toString();
    }

    static String tparams(List<KmTypeParameter> l, Map<Integer, String> tps) {
        if (l.isEmpty()) return "";
        StringBuilder sb = new StringBuilder("<");
        for (int i = 0; i < l.size(); i++) {
            KmTypeParameter p = l.get(i);
            if (i > 0) sb.append(", ");
            if (Attributes.isReified(p)) sb.append("reified ");
            if (p.getVariance() == KmVariance.IN) sb.append("in ");
            else if (p.getVariance() == KmVariance.OUT) sb.append("out ");
            sb.append(p.getName());
            if (!p.getUpperBounds().isEmpty()) sb.append(" : ").append(ty(p.getUpperBounds().get(0), tps));
        }
        return sb.append("> ").toString();
    }

    static String params(List<KmValueParameter> l, Map<Integer, String> tps) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < l.size(); i++) {
            KmValueParameter p = l.get(i);
            if (i > 0) sb.append(", ");
            if (Attributes.isCrossinline(p)) sb.append("crossinline ");
            if (Attributes.isNoinline(p)) sb.append("noinline ");
            if (p.getVarargElementType() != null) sb.append("vararg ");
            sb.append(p.getName()).append(": ").append(ty(p.getVarargElementType() != null ? p.getVarargElementType() : p.getType(), tps));
            if (Attributes.getDeclaresDefaultValue(p)) sb.append(" = <default>");
        }
        return sb.toString();
    }

    static String fn(KmFunction f, Map<Integer, String> tps0) {
        Map<Integer, String> tps = new HashMap<>(tps0);
        for (KmTypeParameter p : f.getTypeParameters()) tps.put(p.getId(), p.getName());
        StringBuilder sb = new StringBuilder("  ");
        sb.append(Attributes.getVisibility(f).name().toLowerCase()).append(' ');
        Modality mo = Attributes.getModality(f);
        if (mo != Modality.FINAL) sb.append(mo.name().toLowerCase()).append(' ');
        if (Attributes.isInline(f)) sb.append("inline ");
        if (Attributes.isSuspend(f)) sb.append("suspend ");
        if (Attributes.isOperator(f)) sb.append("operator ");
        if (Attributes.isInfix(f)) sb.append("infix ");
        if (Attributes.isTailrec(f)) sb.append("tailrec ");
        sb.append("fun ").append(tparams(f.getTypeParameters(), tps));
        if (f.getReceiverParameterType() != null) sb.append(ty(f.getReceiverParameterType(), tps)).append('.');
        sb.append(f.getName()).append('(').append(params(f.getValueParameters(), tps)).append("): ").append(ty(f.getReturnType(), tps));
        JvmMethodSignature s = JvmExtensionsKt.getSignature(f);
        if (s != null) sb.append("   // jvm ").append(s.getName()).append(s.getDescriptor());
        return sb.toString();
    }

    static void writeListing(String jar, ClassNode cn, KmClass kc, KmPackage kp, KmFunction lam, String kindName) throws IOException {
        StringBuilder sb = new StringBuilder();
        Map<Integer, String> tps = new HashMap<>();
        if (kc != null) {
            for (KmTypeParameter p : kc.getTypeParameters()) tps.put(p.getId(), p.getName());
            ClassKind ck = Attributes.getKind(kc);
            sb.append("// ").append(cn.name).append("  (kotlin.Metadata k=1)\n");
            sb.append(Attributes.getVisibility(kc).name().toLowerCase()).append(' ').append(Attributes.getModality(kc).name().toLowerCase()).append(' ');
            if (Attributes.isData(kc)) sb.append("data ");
            if (Attributes.isValue(kc)) sb.append("value ");
            if (Attributes.isFunInterface(kc)) sb.append("fun ");
            if (Attributes.isInner(kc)) sb.append("inner ");
            sb.append(ck.name().toLowerCase().replace('_', ' ')).append(' ').append(kc.getName()).append(' ').append(tparams(kc.getTypeParameters(), tps));
            if (!kc.getSupertypes().isEmpty()) {
                sb.append(": ");
                for (int i = 0; i < kc.getSupertypes().size(); i++) { if (i > 0) sb.append(", "); sb.append(ty(kc.getSupertypes().get(i), tps)); }
            }
            sb.append('\n');
            if (kc.getCompanionObject() != null) sb.append("  companion object ").append(kc.getCompanionObject()).append('\n');
            if (!kc.getEnumEntries().isEmpty()) sb.append("  enum entries: ").append(String.join(", ", kc.getEnumEntries())).append('\n');
            if (!kc.getSealedSubclasses().isEmpty()) sb.append("  sealed subclasses: ").append(String.join(", ", kc.getSealedSubclasses())).append('\n');
            for (KmConstructor c : kc.getConstructors()) {
                sb.append("  ").append(Attributes.getVisibility(c).name().toLowerCase()).append(Attributes.isSecondary(c) ? " constructor(" : " primary constructor(")
                        .append(params(c.getValueParameters(), tps)).append(')');
                JvmMethodSignature s = JvmExtensionsKt.getSignature(c);
                if (s != null) sb.append("   // jvm ").append(s.getName()).append(s.getDescriptor());
                sb.append('\n');
            }
        } else {
            sb.append("// ").append(cn.name).append("  (kotlin.Metadata ").append(kindName).append(")\n");
        }
        List<KmProperty> props = kc != null ? kc.getProperties() : kp != null ? kp.getProperties() : List.of();
        List<KmFunction> fns = kc != null ? kc.getFunctions() : kp != null ? kp.getFunctions() : lam != null ? List.of(lam) : List.of();
        for (KmProperty p : props) {
            sb.append("  ").append(Attributes.getVisibility(p).name().toLowerCase()).append(' ');
            if (Attributes.isLateinit(p)) sb.append("lateinit ");
            if (Attributes.isConst(p)) sb.append("const ");
            sb.append(Attributes.isVar(p) ? "var " : "val ");
            if (p.getReceiverParameterType() != null) sb.append(ty(p.getReceiverParameterType(), tps)).append('.');
            sb.append(p.getName()).append(": ").append(ty(p.getReturnType(), tps));
            if (Attributes.isDelegated(p)) sb.append(" by <delegate>");
            JvmMethodSignature g = JvmExtensionsKt.getGetterSignature(p), st = JvmExtensionsKt.getSetterSignature(p);
            JvmFieldSignature fs = JvmExtensionsKt.getFieldSignature(p);
            sb.append("   //");
            if (g != null) sb.append(" get=").append(g.getName()).append(g.getDescriptor());
            if (st != null) sb.append(" set=").append(st.getName()).append(st.getDescriptor());
            if (fs != null) sb.append(" field=").append(fs.getName()).append(':').append(fs.getDescriptor());
            sb.append('\n');
        }
        for (KmFunction f : fns) sb.append(fn(f, tps)).append('\n');
        Path p = outDir.resolve("kotlin-signatures").resolve(jar).resolve(cn.name + ".kt.txt");
        Files.createDirectories(p.getParent());
        Files.writeString(p, sb.toString(), StandardCharsets.UTF_8);
    }

    // ---------------------------------------------------------------- outputs
    static void writeOutputs() throws IOException {
        StringBuilder sb = new StringBuilder("jar\tcategory\tclasses\toccurrences\n");
        for (var je : SUM.entrySet()) for (var ce : je.getValue().entrySet())
            sb.append(je.getKey()).append('\t').append(ce.getKey()).append('\t').append(ce.getValue()[0]).append('\t').append(ce.getValue()[1]).append('\n');
        Files.writeString(outDir.resolve("summary.tsv"), sb.toString());
        Collections.sort(CLASS_ROWS);
        Files.writeString(outDir.resolve("classes.tsv"), "jar\tclass\tkind\tclassfile_major\tkm_functions\tkm_properties\tkm_ctors\tjvm_methods\tjvm_declared\tjvm_generated\tjvm_unexplained\n" + String.join("\n", CLASS_ROWS) + "\n");
        Collections.sort(RESIDUAL);
        Files.writeString(outDir.resolve("residual.tsv"), "jar\tclass\tmember\tnote\n" + String.join("\n", RESIDUAL) + "\n");
        sb = new StringBuilder("group\tkey\tcount\n");
        for (var ge : TOP.entrySet()) {
            boolean big = ge.getKey().equals("inline-fun-expanded") || ge.getKey().equals("stdlib-Kt-owner");
            var ents = new ArrayList<>(ge.getValue().entrySet());
            ents.sort((a, b) -> b.getValue() - a.getValue() != 0 ? b.getValue() - a.getValue() : a.getKey().compareTo(b.getKey()));
            int lim = big ? 25 : Integer.MAX_VALUE;
            for (int i = 0; i < ents.size() && i < lim; i++) sb.append(ge.getKey()).append('\t').append(ents.get(i).getKey()).append('\t').append(ents.get(i).getValue()).append('\n');
            if (big) sb.append(ge.getKey()).append("\t(distinct keys)\t").append(ents.size()).append('\n');
        }
        Files.writeString(outDir.resolve("top.tsv"), sb.toString());
    }
}
