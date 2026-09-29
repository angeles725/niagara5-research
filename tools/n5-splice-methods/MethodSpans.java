import com.sun.source.tree.*;
import com.sun.source.util.*;

import javax.lang.model.element.*;
import javax.lang.model.type.*;
import javax.lang.model.util.*;
import javax.tools.*;
import java.io.File;
import java.io.IOException;
import java.nio.file.*;
import java.util.*;

/**
 * Attributing scanner for tools/n5-splice-methods.py (T21/F9).
 *
 * Usage: java MethodSpans <classpath-file|-> <file.java>...
 *
 * Each file is parsed AND attributed (javac analyze(), -proc:none, the given
 * classpath) in its own task, so every JVM descriptor is javac's own erasure,
 * never a regex over source text. One JSON line per file:
 *   methods  every method/constructor declared directly in the top-level class:
 *            name ("<init>" for constructors), JVM descriptor, source offsets
 *            (start, after the modifiers, end, body start)
 *   members  "owner|name|descriptor" of every member element (incl. implicit
 *            ones: default constructor, enum values/valueOf) of every class of
 *            the top-level class's nest (the class and its member types)
 *   refs     every reference with its source offset: type (simple name ->
 *            qualified/binary), member of the nest (owner/name/descriptor),
 *            static (bare identifier bound to a static member of a class outside
 *            the nest), local_class (local or anonymous class declaration)
 *   imports  every import declaration with offsets; package_end; errors
 * Offsets are javac's (UTF-16 code units).
 */
public class MethodSpans {
    public static void main(String[] args) throws IOException {
        String cp = args[0].equals("-") ? "" : Files.readString(Path.of(args[0])).strip();
        JavaCompiler javac = ToolProvider.getSystemJavaCompiler();
        StandardJavaFileManager fm = javac.getStandardFileManager(null, null, null);
        List<File> cpFiles = new ArrayList<>();
        if (!cp.isEmpty()) for (String e : cp.split(File.pathSeparator)) cpFiles.add(new File(e));
        fm.setLocation(StandardLocation.CLASS_PATH, cpFiles);
        for (int i = 1; i < args.length; i++) {
            String a = args[i];
            List<String> errors = new ArrayList<>();
            DiagnosticListener<JavaFileObject> dl = d -> {
                if (d.getKind() == Diagnostic.Kind.ERROR && errors.size() < 5) errors.add(d.getMessage(Locale.ROOT));
            };
            JavacTask task = (JavacTask) javac.getTask(null, fm, dl,
                    List.of("-proc:none", "--release", "25", "-implicit:none"), null, fm.getJavaFileObjects(Path.of(a)));
            Iterable<? extends CompilationUnitTree> cus = task.parse();
            task.analyze();
            for (CompilationUnitTree cu : cus) {
                Scan s = new Scan(task, cu);
                s.scan(cu, null);
                StringBuilder out = new StringBuilder();
                out.append("{\"file\":").append(q(a))
                        .append(",\"package\":").append(q(cu.getPackageName() == null ? "" : cu.getPackageName().toString()))
                        .append(",\"package_end\":").append(cu.getPackage() == null ? -1 : s.end(cu.getPackage()))
                        .append(",\"top\":").append(q(s.topBinary == null ? "" : s.topBinary))
                        .append(",\"imports\":").append(s.imports)
                        .append(",\"methods\":").append(s.methods)
                        .append(",\"members\":").append(s.members())
                        .append(",\"refs\":").append(s.refs)
                        .append(",\"errors\":").append(list(errors)).append("}");
                System.out.println(out);
            }
        }
    }

    static final class Scan extends TreePathScanner<Void, Void> {
        final Trees trees;
        final Types types;
        final Elements elements;
        final SourcePositions pos;
        final CompilationUnitTree cu;
        final StringJoiner imports = new StringJoiner(",", "[", "]");
        final StringJoiner methods = new StringJoiner(",", "[", "]");
        final StringJoiner refs = new StringJoiner(",", "[", "]");
        TypeElement top;
        String topBinary;

        Scan(JavacTask task, CompilationUnitTree cu) {
            this.trees = Trees.instance(task);
            this.types = task.getTypes();
            this.elements = task.getElements();
            this.pos = trees.getSourcePositions();
            this.cu = cu;
        }

        long start(Tree t) { return pos.getStartPosition(cu, t); }
        long end(Tree t) { return pos.getEndPosition(cu, t); }

        String binary(TypeElement te) { return elements.getBinaryName(te).toString().replace('.', '/'); }

        boolean inNest(Element owner) {
            if (!(owner instanceof TypeElement te) || topBinary == null) return false;
            if (te.getNestingKind() == NestingKind.LOCAL || te.getNestingKind() == NestingKind.ANONYMOUS) return true;
            String b = binary(te);
            return b.equals(topBinary) || b.startsWith(topBinary + "$");
        }

        String desc(TypeMirror t) {
            TypeMirror e = types.erasure(t);
            switch (e.getKind()) {
                case BOOLEAN: return "Z";
                case BYTE: return "B";
                case CHAR: return "C";
                case SHORT: return "S";
                case INT: return "I";
                case LONG: return "J";
                case FLOAT: return "F";
                case DOUBLE: return "D";
                case VOID: return "V";
                case ARRAY: return "[" + desc(((ArrayType) e).getComponentType());
                case DECLARED: return "L" + binary((TypeElement) ((DeclaredType) e).asElement()) + ";";
                default: return "!" + e.getKind();
            }
        }

        String methodDesc(ExecutableElement m) {
            StringBuilder sb = new StringBuilder("(");
            if (m.getKind() == ElementKind.CONSTRUCTOR && m.getEnclosingElement().getKind() == ElementKind.ENUM)
                sb.append("Ljava/lang/String;I");  // javac's synthetic enum constructor prefix
            for (VariableElement p : m.getParameters()) sb.append(desc(p.asType()));
            return sb.append(")").append(desc(m.getReturnType())).toString();
        }

        String memberKey(Element e) {
            String owner = binary((TypeElement) e.getEnclosingElement());
            if (e instanceof ExecutableElement m) return owner + "|" + m.getSimpleName() + "|" + methodDesc(m);
            return owner + "|" + e.getSimpleName() + "|" + desc(e.asType());
        }

        String members() {
            StringJoiner sj = new StringJoiner(",", "[", "]");
            if (top != null) addMembers(top, sj);
            return sj.toString();
        }

        void addMembers(TypeElement te, StringJoiner sj) {
            for (Element e : te.getEnclosedElements()) {
                switch (e.getKind()) {
                    case METHOD, CONSTRUCTOR, FIELD, ENUM_CONSTANT -> sj.add(q(memberKey(e)));
                    case CLASS, INTERFACE, ENUM, RECORD, ANNOTATION_TYPE -> {
                        sj.add(q("type|" + binary((TypeElement) e)));
                        addMembers((TypeElement) e, sj);
                    }
                    default -> { }
                }
            }
        }

        void ref(Element e, Tree at, boolean bare, String simple) {
            if (e == null) return;
            long p = start(at);
            if (e instanceof TypeElement te) {
                if (simple != null)
                    refs.add("{\"kind\":\"type\",\"pos\":" + p + ",\"simple\":" + q(simple)
                            + ",\"qname\":" + q(te.getQualifiedName().toString())
                            + ",\"binary\":" + q(binary(te)) + ",\"nest\":" + inNest(te) + "}");
                return;
            }
            Name n = e.getSimpleName();
            if (n.contentEquals("this") || n.contentEquals("super")) return;  // javac's implicit variables
            ElementKind k = e.getKind();
            if (k != ElementKind.METHOD && k != ElementKind.CONSTRUCTOR && k != ElementKind.FIELD
                    && k != ElementKind.ENUM_CONSTANT) return;
            Element owner = e.getEnclosingElement();
            if (!(owner instanceof TypeElement ote)) return;
            if (inNest(owner)) {
                refs.add("{\"kind\":\"member\",\"pos\":" + p + ",\"key\":" + q(memberKey(e))
                        + ",\"local\":" + (ote.getNestingKind() == NestingKind.LOCAL
                        || ote.getNestingKind() == NestingKind.ANONYMOUS) + "}");
            } else if (bare && e.getModifiers().contains(Modifier.STATIC)) {
                refs.add("{\"kind\":\"static\",\"pos\":" + p + ",\"owner\":" + q(ote.getQualifiedName().toString())
                        + ",\"name\":" + q(e.getSimpleName().toString()) + "}");
            }
        }

        @Override
        public Void visitImport(ImportTree it, Void v) {
            imports.add("{\"static\":" + it.isStatic() + ",\"name\":" + q(it.getQualifiedIdentifier().toString())
                    + ",\"start\":" + start(it) + ",\"end\":" + end(it) + "}");
            return null;  // import names are not references of any method body
        }

        @Override
        public Void visitClass(ClassTree ct, Void v) {
            Tree parent = getCurrentPath().getParentPath().getLeaf();
            TypeElement te = (TypeElement) trees.getElement(getCurrentPath());
            if (parent instanceof CompilationUnitTree && top == null && te != null) {
                top = te;
                topBinary = binary(te);
                for (Tree member : ct.getMembers()) {
                    if (member instanceof MethodTree mt) method(mt, new TreePath(getCurrentPath(), mt));
                }
            } else if (!(parent instanceof ClassTree) && !(parent instanceof CompilationUnitTree)) {
                refs.add("{\"kind\":\"local_class\",\"pos\":" + start(ct) + "}");
            }
            return super.visitClass(ct, v);
        }

        void method(MethodTree mt, TreePath path) {
            Element e = trees.getElement(path);
            if (!(e instanceof ExecutableElement ee)) return;
            long s = start(mt);
            long modsEnd = end(mt.getModifiers());
            long after = modsEnd > s ? modsEnd : s;
            methods.add("{\"name\":" + q(mt.getName().toString()) + ",\"desc\":" + q(methodDesc(ee))
                    + ",\"start\":" + s + ",\"after_mods\":" + after + ",\"end\":" + end(mt)
                    + ",\"body_start\":" + (mt.getBody() == null ? -1 : start(mt.getBody())) + "}");
        }

        @Override
        public Void visitNewClass(NewClassTree nt, Void v) {
            ref(trees.getElement(getCurrentPath()), nt, false, null);
            if (nt.getClassBody() != null) refs.add("{\"kind\":\"local_class\",\"pos\":" + start(nt) + "}");
            return super.visitNewClass(nt, v);
        }

        @Override
        public Void visitIdentifier(IdentifierTree it, Void v) {
            ref(trees.getElement(getCurrentPath()), it, true, it.getName().toString());
            return super.visitIdentifier(it, v);
        }

        @Override
        public Void visitMemberSelect(MemberSelectTree mt, Void v) {
            ref(trees.getElement(getCurrentPath()), mt, false, null);
            return super.visitMemberSelect(mt, v);
        }

        @Override
        public Void visitMemberReference(MemberReferenceTree mt, Void v) {
            ref(trees.getElement(getCurrentPath()), mt, false, null);
            return super.visitMemberReference(mt, v);
        }
    }

    static String list(List<String> xs) {
        StringJoiner sj = new StringJoiner(",", "[", "]");
        for (String x : xs) sj.add(q(x));
        return sj.toString();
    }

    static String q(String s) {
        StringBuilder sb = new StringBuilder("\"");
        for (char c : s.toCharArray()) {
            switch (c) {
                case '"' -> sb.append("\\\"");
                case '\\' -> sb.append("\\\\");
                case '\n' -> sb.append("\\n");
                case '\r' -> sb.append("\\r");
                case '\t' -> sb.append("\\t");
                default -> {
                    if (c < 0x20) sb.append(String.format("\\u%04x", (int) c));
                    else sb.append(c);
                }
            }
        }
        return sb.append('"').toString();
    }
}
