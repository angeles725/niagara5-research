package b118;
import java.util.*;
import sootup.core.model.SourceType;
import sootup.core.signatures.MethodSignature;
import sootup.core.inputlocation.AnalysisInputLocation;
import sootup.java.core.views.JavaView;
import sootup.java.bytecode.frontend.inputlocation.JavaClassPathAnalysisInputLocation;
import sootup.callgraph.*;
/** Dump CHA and RTA call edges reachable from <mainClass>.main(String[]) as "caller -> callee" in JVM descriptor form. */
public class EdgeDump {
  public static void main(String[] a) {
    List<AnalysisInputLocation> l = new ArrayList<>();
    l.add(new JavaClassPathAnalysisInputLocation(a[0], SourceType.Application));
    for (int i = 2; i < a.length; i++) l.add(new JavaClassPathAnalysisInputLocation(a[i], SourceType.Application));
    if (System.getProperty("b118.jrt") != null) l.add(new sootup.java.bytecode.frontend.inputlocation.DefaultRuntimeAnalysisInputLocation());
    JavaView v = new JavaView(l);
    MethodSignature main = v.getIdentifierFactory().parseMethodSignature("<" + a[1] + ": void main(java.lang.String[])>");
    for (String algo : new String[]{"CHA", "RTA"}) {
      CallGraph cg = (algo.equals("CHA") ? new ClassHierarchyAnalysisAlgorithm(v) : new RapidTypeAnalysisAlgorithm(v)).initialize(List.of(main));
      TreeSet<String> out = new TreeSet<>();
      for (CallGraph.Call c : cg.getCalls()) out.add(algo + " " + id(c.sourceMethodSignature()) + " -> " + id(c.targetMethodSignature()));
      out.forEach(System.out::println);
    }
  }
  static String id(MethodSignature m) {
    StringBuilder d = new StringBuilder("(");
    for (var t : m.getParameterTypes()) d.append(desc(t.toString()));
    d.append(")").append(desc(m.getType().toString()));
    return m.getDeclClassType().getFullyQualifiedName() + "." + m.getName() + d;
  }
  static String desc(String t) {
    int dims = 0; while (t.endsWith("[]")) { dims++; t = t.substring(0, t.length() - 2); }
    String b = switch (t) { case "int" -> "I"; case "long" -> "J"; case "boolean" -> "Z"; case "byte" -> "B"; case "char" -> "C";
      case "short" -> "S"; case "float" -> "F"; case "double" -> "D"; case "void" -> "V"; default -> "L" + t.replace('.', '/') + ";"; };
    return "[".repeat(dims) + b;
  }
}
