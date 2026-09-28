package b118;

import java.nio.file.*;
import java.util.*;
import java.util.stream.*;
import sootup.core.model.*;
import sootup.core.signatures.*;
import sootup.core.types.*;
import sootup.core.jimple.common.stmt.*;
import sootup.core.jimple.common.expr.*;
import sootup.java.core.*;
import sootup.java.core.views.JavaView;
import sootup.java.bytecode.frontend.inputlocation.JavaClassPathAnalysisInputLocation;
import sootup.callgraph.*;
import sootup.core.inputlocation.AnalysisInputLocation;

/** B118 M2 probe: SootUp 3.0.1 over N5 (major 69) jars. Non-executing (no class loading of analyzed code). */
public class Probe {
  public static void main(String[] a) throws Exception {
    String appJar = a[0]; String libDir = a[1]; String extDir = a[2];
    String entryClass = a[3]; String targetClass = a[4]; String targetName = a[5];
    List<AnalysisInputLocation> locs = new ArrayList<>();
    locs.add(new JavaClassPathAnalysisInputLocation(appJar, SourceType.Application));
    for (String d : new String[]{libDir, extDir})
      try (Stream<Path> s = Files.list(Paths.get(d))) {
        for (Path p : s.filter(p -> p.toString().endsWith(".jar")).sorted().toList())
          if (!p.toAbsolutePath().toString().equals(Paths.get(appJar).toAbsolutePath().toString()))
            locs.add(new JavaClassPathAnalysisInputLocation(p.toString(), SourceType.Library));
      }
    JavaView view = new JavaView(locs);
    long t0 = System.nanoTime();
    JavaIdentifierFactory f = view.getIdentifierFactory();
    ClassType entryT = f.getClassType(entryClass), targetT = f.getClassType(targetClass);
    JavaSootClass entry = view.getClass(entryT).orElseThrow(() -> new IllegalStateException("entry class not loaded: " + entryClass));
    System.out.println("ENTRY loaded: " + entry.getType() + " methods=" + entry.getMethods().size());
    // 1. Jimple call sites in entry that name targetName
    for (JavaSootMethod m : entry.getMethods()) {
      if (!m.hasBody()) continue;
      for (Stmt st : m.getBody().getStmts()) {
        if (st instanceof InvokableStmt is && is.getInvokeExpr().isPresent()) {
          AbstractInvokeExpr ie = is.getInvokeExpr().get();
          if (ie.getMethodSignature().getName().equals(targetName))
            System.out.println("SITE " + m.getSignature().getSubSignature() + " line=" + st.getPositionInfo().getStmtPosition().getFirstLine() + " : " + ie.getMethodSignature());
        }
      }
    }
    // 2. CHA and RTA from all entry methods; edges to targetName
    List<MethodSignature> entries = entry.getMethods().stream().filter(SootMethod::hasBody).map(SootMethod::getSignature).toList();
    for (String algo : new String[]{"CHA", "RTA"}) {
      long t = System.nanoTime();
      AbstractCallGraphAlgorithm alg = algo.equals("CHA") ? new ClassHierarchyAnalysisAlgorithm(view) : new RapidTypeAnalysisAlgorithm(view);
      CallGraph cg = alg.initialize(entries);
      Set<String> tg = new TreeSet<>();
      for (MethodSignature src : entries)
        for (MethodSignature dst : cg.callTargetsFrom(src))
          if (dst.getName().equals(targetName)) tg.add(src.getSubSignature().getName() + " -> " + dst);
      System.out.printf("%s calls=%d methods=%d t=%.1fs%n", algo, cg.callCount(), cg.getMethodSignatures().size(), (System.nanoTime() - t) / 1e9);
      tg.forEach(x -> System.out.println("  " + algo + " " + x));
    }
    // 3. who-calls: every body in the whole view invoking <anything>.targetName where owner is target or a supertype of target
    Set<String> supers = new HashSet<>();
    supers.add(targetT.getFullyQualifiedName());
    view.getTypeHierarchy().superClassesOf(targetT).forEach(c -> supers.add(c.getFullyQualifiedName()));
    view.getTypeHierarchy().implementedInterfacesOf(targetT).forEach(c -> supers.add(c.getFullyQualifiedName()));
    Set<String> subs = new TreeSet<>();
    view.getTypeHierarchy().subtypesOf(targetT).forEach(c -> subs.add(c.getFullyQualifiedName()));
    System.out.println("TARGET subtypes (whole install): " + subs);
    long t3 = System.nanoTime(); int classes = 0, bodies = 0, fails = 0;
    List<String> exact = new ArrayList<>(), viaSuper = new ArrayList<>();
    for (JavaSootClass c : view.getClasses().toList()) {
      classes++;
      for (JavaSootMethod m : c.getMethods()) {
        if (!m.isConcrete()) continue;
        Body b;
        try { b = m.getBody(); bodies++; } catch (Throwable e) { fails++; continue; }
        for (Stmt st : b.getStmts())
          if (st instanceof InvokableStmt is && is.getInvokeExpr().isPresent()) {
            MethodSignature s = is.getInvokeExpr().get().getMethodSignature();
            if (!s.getName().equals(targetName)) continue;
            String owner = s.getDeclClassType().getFullyQualifiedName();
            String rec = c.getType() + "." + m.getName() + ":" + st.getPositionInfo().getStmtPosition().getFirstLine() + " -> " + s;
            if (owner.equals(targetT.getFullyQualifiedName())) exact.add(rec);
            else if (supers.contains(owner)) viaSuper.add(rec);
          }
      }
    }
    System.out.printf("WHOCALLS scanned classes=%d bodies=%d bodyFailures=%d t=%.1fs%n", classes, bodies, fails, (System.nanoTime() - t3) / 1e9);
    System.out.println("WHOCALLS exact-owner sites=" + exact.size()); exact.forEach(x -> System.out.println("  EXACT " + x));
    System.out.println("WHOCALLS via-supertype-owner sites (CHA-may-dispatch)=" + viaSuper.size());
    viaSuper.stream().limit(15).forEach(x -> System.out.println("  SUPER " + x));
    System.out.printf("TOTAL t=%.1fs%n", (System.nanoTime() - t0) / 1e9);
  }
}
