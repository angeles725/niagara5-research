import java.util.*;
/** B118 M3: can Tridium classes load / static-init offline in a plain JVM? Prints typed outcome per class. */
public class InitProbe {
  public static void main(String[] a) {
    for (String n : a) {
      String load, init;
      try { Class.forName(n, false, InitProbe.class.getClassLoader()); load = "LOAD-OK"; }
      catch (Throwable t) { load = "LOAD-FAIL " + chain(t); }
      try { Class.forName(n, true, InitProbe.class.getClassLoader()); init = "INIT-OK"; }
      catch (Throwable t) { init = "INIT-FAIL " + chain(t); }
      System.out.println(n + "\t" + load + "\t" + init);
    }
  }
  static String chain(Throwable t) {
    StringBuilder b = new StringBuilder(); int d = 0;
    while (t != null && d++ < 6) { b.append(t.getClass().getSimpleName()).append(": ").append(String.valueOf(t.getMessage()).replace('\n',' ')); 
      StackTraceElement[] st = t.getStackTrace(); if (st.length > 0) b.append(" @").append(st[0]);
      t = t.getCause(); if (t != null) b.append(" <- "); }
    return b.toString();
  }
}
