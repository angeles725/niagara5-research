package b118;
import java.lang.instrument.*;
import java.security.ProtectionDomain;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.io.*;
import org.objectweb.asm.*;
import org.objectweb.asm.commons.AdviceAdapter;

/** B118 M4: exact dynamic call-edge tracer. Instruments every method of classes whose internal name starts with the
 *  agent-arg prefix; at entry, records the (caller frame -> this method) edge via StackWalker. Dumps edges at exit. */
public class TraceAgent {
  static final Set<String> EDGES = ConcurrentHashMap.newKeySet();
  static final Set<String> ENTERED = ConcurrentHashMap.newKeySet();
  static final StackWalker SW = StackWalker.getInstance(StackWalker.Option.RETAIN_CLASS_REFERENCE);
  public static void enter(String callee) {
    ENTERED.add(callee);
    String caller = SW.walk(s -> s.skip(2).findFirst().map(f -> f.getClassName() + "." + f.getMethodName() + f.getDescriptor()).orElse("?")) ;
    EDGES.add(caller + " -> " + callee);
  }
  public static void premain(String arg, Instrumentation inst) {
    String[] a = arg.split(",", 2); String prefix = a[0]; String out = a[1];
    Runtime.getRuntime().addShutdownHook(new Thread(() -> {
      try (PrintWriter w = new PrintWriter(new FileWriter(out))) {
        new TreeSet<>(EDGES).forEach(e -> w.println("EDGE " + e)); new TreeSet<>(ENTERED).forEach(m -> w.println("ENTER " + m));
      } catch (IOException e) { e.printStackTrace(); }
    }));
    inst.addTransformer(new ClassFileTransformer() {
      public byte[] transform(ClassLoader l, String name, Class<?> c, ProtectionDomain pd, byte[] b) {
        if (name == null || !name.startsWith(prefix)) return null;
        try {
        ClassReader cr = new ClassReader(b); ClassWriter cw = new ClassWriter(cr, ClassWriter.COMPUTE_MAXS);
        cr.accept(new ClassVisitor(Opcodes.ASM9, cw) {
          public MethodVisitor visitMethod(int acc, String mn, String desc, String sig, String[] ex) {
            MethodVisitor mv = super.visitMethod(acc, mn, desc, sig, ex);
            if ((acc & (Opcodes.ACC_ABSTRACT | Opcodes.ACC_NATIVE)) != 0) return mv;
            String id = name.replace('/', '.') + "." + mn + desc;
            return new AdviceAdapter(Opcodes.ASM9, mv, acc, mn, desc) {
              protected void onMethodEnter() { visitLdcInsn(id); visitMethodInsn(INVOKESTATIC, "b118/TraceAgent", "enter", "(Ljava/lang/String;)V", false); }
            };
          }
        }, ClassReader.EXPAND_FRAMES);
        return cw.toByteArray();
        } catch (Throwable t) { System.err.println("TRACE-AGENT transform failed " + name + ": " + t); return null; }
      }
    });
  }
}
