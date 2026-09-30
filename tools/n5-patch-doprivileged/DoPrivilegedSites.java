import com.sun.source.tree.*;
import com.sun.source.util.*;

import javax.tools.*;
import java.io.IOException;
import java.nio.file.*;
import java.util.*;

/**
 * Parse-only scanner for tools/n5-patch-doprivileged.py (T21/F8).
 *
 * For each .java argument, prints one JSON line: every `doPrivileged(...)`
 * invocation with its source offsets, argument kind, enclosing class-body chain
 * and enclosing member, plus every class body (id, parent, kind, name, supertypes)
 * so the caller can compute javac binary names. No attribution, no classpath:
 * the source only has to parse. Run with `java DoPrivilegedSites.java <files...>`.
 */
public class DoPrivilegedSites {
    public static void main(String[] args) throws IOException {
        JavaCompiler javac = ToolProvider.getSystemJavaCompiler();
        for (String a : args) {
            StandardJavaFileManager fm = javac.getStandardFileManager(null, null, null);
            JavacTask task = (JavacTask) javac.getTask(null, fm, d -> {}, List.of("-proc:none"), null,
                    fm.getJavaFileObjects(Path.of(a)));
            StringBuilder out = new StringBuilder();
            for (CompilationUnitTree cu : task.parse()) {
                Scanner s = new Scanner(Trees.instance(task).getSourcePositions(), cu);
                s.scan(cu, null);
                out.append("{\"file\":").append(q(a))
                        .append(",\"classes\":").append(s.classes)
                        .append(",\"sites\":").append(s.sites).append("}");
            }
            System.out.println(out);
        }
    }

    static final class Scanner extends TreePathScanner<Void, Void> {
        final SourcePositions pos;
        final CompilationUnitTree cu;
        final StringJoiner classes = new StringJoiner(",", "[", "]");
        final StringJoiner sites = new StringJoiner(",", "[", "]");
        final Deque<Integer> classStack = new ArrayDeque<>();
        final Deque<String> memberStack = new ArrayDeque<>();
        final Deque<Integer> lambdaDepth = new ArrayDeque<>(List.of(0));
        int nextClassId = 0;

        Scanner(SourcePositions pos, CompilationUnitTree cu) {
            this.pos = pos;
            this.cu = cu;
        }

        long start(Tree t) { return pos.getStartPosition(cu, t); }
        long end(Tree t) { return pos.getEndPosition(cu, t); }

        @Override
        public Void visitClass(ClassTree ct, Void v) {
            int id = nextClassId++;
            Tree parent = getCurrentPath().getParentPath().getLeaf();
            String kind;
            List<String> supers = new ArrayList<>();
            if (parent instanceof NewClassTree nc) {
                kind = "anon";
                supers.add(nc.getIdentifier().toString());
            } else if (parent instanceof CompilationUnitTree) {
                kind = "top";
            } else if (parent instanceof ClassTree) {
                kind = "member";
            } else {
                kind = "local";
            }
            if (ct.getExtendsClause() != null) supers.add(ct.getExtendsClause().toString());
            for (Tree t : ct.getImplementsClause()) supers.add(t.toString());
            StringJoiner sj = new StringJoiner(",", "[", "]");
            for (String x : supers) sj.add(q(x));
            StringJoiner ctors = new StringJoiner(",", "[", "]");
            for (Tree m : ct.getMembers()) {
                if (m instanceof MethodTree mt && mt.getName().contentEquals("<init>")) ctors.add(memberJson(m));
            }
            classes.add("{\"id\":" + id + ",\"parent\":" + (classStack.isEmpty() ? -1 : classStack.peek())
                    + ",\"kind\":" + q(kind) + ",\"name\":" + q(ct.getSimpleName().toString())
                    + ",\"declkind\":" + q(ct.getKind().toString())
                    + ",\"start\":" + start(ct) + ",\"supers\":" + sj + ",\"ctors\":" + ctors + "}");
            classStack.push(id);
            memberStack.push("null");
            lambdaDepth.push(0);
            try {
                // members: record which member each nested tree belongs to
                for (Tree m : ct.getMembers()) {
                    memberStack.pop();
                    memberStack.push(memberJson(m));
                    scan(m, null);
                }
                memberStack.pop();
                memberStack.push("null");
            } finally {
                lambdaDepth.pop();
                memberStack.pop();
                classStack.pop();
            }
            return null;
        }

        String memberJson(Tree m) {
            if (m instanceof MethodTree mt) {
                boolean ctor = mt.getName().contentEquals("<init>");
                StringJoiner ps = new StringJoiner(",", "[", "]");
                for (VariableTree p : mt.getParameters()) ps.add(q(p.getType().toString()));
                boolean st = mt.getModifiers().getFlags().contains(javax.lang.model.element.Modifier.STATIC);
                return "{\"kind\":" + q(ctor ? "ctor" : "method") + ",\"name\":" + q(mt.getName().toString())
                        + ",\"params\":" + ps + ",\"static\":" + st
                        + (ctor ? ",\"delegates\":" + delegatesToThis(mt) : "") + "}";
            }
            if (m instanceof BlockTree bt) {
                return "{\"kind\":" + q(bt.isStatic() ? "clinit" : "instinit") + "}";
            }
            if (m instanceof VariableTree vt) {
                boolean st = vt.getModifiers().getFlags().contains(javax.lang.model.element.Modifier.STATIC);
                return "{\"kind\":" + q(st ? "clinit" : "instinit") + ",\"field\":" + q(vt.getName().toString()) + "}";
            }
            return "{\"kind\":\"other\"}";
        }

        /** true when the constructor's first statement is `this(...)`: such a constructor runs no initializers. */
        static boolean delegatesToThis(MethodTree mt) {
            if (mt.getBody() == null || mt.getBody().getStatements().isEmpty()) return false;
            StatementTree first = mt.getBody().getStatements().get(0);
            return first instanceof ExpressionStatementTree es
                    && es.getExpression() instanceof MethodInvocationTree mi
                    && mi.getMethodSelect() instanceof IdentifierTree id
                    && id.getName().contentEquals("this");
        }

        @Override
        public Void visitLambdaExpression(LambdaExpressionTree lt, Void v) {
            lambdaDepth.push(lambdaDepth.pop() + 1);
            try {
                return super.visitLambdaExpression(lt, v);
            } finally {
                lambdaDepth.push(lambdaDepth.pop() - 1);
            }
        }

        @Override
        public Void visitMethodInvocation(MethodInvocationTree mi, Void v) {
            ExpressionTree sel = mi.getMethodSelect();
            String name = null;
            String qual = "";
            if (sel instanceof IdentifierTree id) {
                name = id.getName().toString();
            } else if (sel instanceof MemberSelectTree ms) {
                name = ms.getIdentifier().toString();
                qual = ms.getExpression().toString();
            }
            if ("doPrivileged".equals(name)) {
                String argKind = "none";
                long as = -1, ae = -1;
                if (mi.getArguments().size() >= 1) {
                    ExpressionTree arg = mi.getArguments().get(0);
                    argKind = arg.getKind().toString();
                    as = start(arg);
                    ae = end(arg);
                }
                sites.add("{\"inv_start\":" + start(mi) + ",\"inv_end\":" + end(mi)
                        + ",\"qualifier\":" + q(qual) + ",\"nargs\":" + mi.getArguments().size()
                        + ",\"arg_kind\":" + q(argKind) + ",\"arg_start\":" + as + ",\"arg_end\":" + ae
                        + ",\"class_id\":" + (classStack.isEmpty() ? -1 : classStack.peek())
                        + ",\"member\":" + (memberStack.isEmpty() ? "null" : memberStack.peek())
                        + ",\"lambda_depth\":" + lambdaDepth.peek() + "}");
            }
            return super.visitMethodInvocation(mi, v);
        }
    }

    static String q(String s) {
        StringBuilder b = new StringBuilder("\"");
        for (char c : s.toCharArray()) {
            switch (c) {
                case '"' -> b.append("\\\"");
                case '\\' -> b.append("\\\\");
                case '\n' -> b.append("\\n");
                case '\r' -> b.append("\\r");
                case '\t' -> b.append("\\t");
                default -> {
                    if (c < 0x20) b.append(String.format("\\u%04x", (int) c));
                    else b.append(c);
                }
            }
        }
        return b.append('"').toString();
    }
}
