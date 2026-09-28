import net.jqwik.api.*;
import java.io.*;
import java.lang.reflect.*;
import java.net.*;
import java.nio.file.*;
import java.util.*;

/** B118 M3: property-based differential test. Three builds of niagara.xml (original nre.jar bytecode, Vineflower
 *  recompiled, docSource-original recompiled) are loaded in ISOLATED class loaders in one JVM; every property asserts
 *  the three arms produce identical observable results (value or exception class+message). */
class XmlArmsProperties {
  static final String NRE = "/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/nre.jar";
  static final String X = System.getProperty("b118.xp");
  static final ClassLoader[] ARMS; static final String[] NAMES = {"orig", "vf", "ds"};
  static {
    try {
      URL nre = Paths.get(NRE).toUri().toURL();
      ClassLoader p = ClassLoader.getPlatformClassLoader();
      ARMS = new ClassLoader[]{ new URLClassLoader(new URL[]{nre}, p),
        new URLClassLoader(new URL[]{Paths.get(X, "vf").toUri().toURL(), nre}, p),
        new URLClassLoader(new URL[]{Paths.get(X, "ds").toUri().toURL(), nre}, p) };
    } catch (Exception e) { throw new ExceptionInInitializerError(e); }
  }
  static String safe(ClassLoader cl, String s, boolean ws) {
    try { StringWriter w = new StringWriter();
      cl.loadClass("niagara.xml.XWriter").getMethod("safe", Writer.class, String.class, boolean.class).invoke(null, w, s, ws);
      return "OK:" + w; } catch (InvocationTargetException e) { return "EXC:" + e.getCause(); } catch (Exception e) { throw new RuntimeException(e); }
  }
  static String parse(ClassLoader cl, String xml, boolean ws) {
    try {
      Class<?> xp = cl.loadClass("niagara.xml.XParser");
      Object parser = xp.getMethod("make", String.class, boolean.class).invoke(null, xml, ws);
      Object root = xp.getMethod("parse").invoke(parser);
      StringBuilder b = new StringBuilder(); dump(cl, root, b); return "OK:" + b;
    } catch (InvocationTargetException e) { return "EXC:" + e.getCause(); } catch (Exception e) { throw new RuntimeException(e); }
  }
  static void dump(ClassLoader cl, Object e, StringBuilder b) throws Exception {
    Class<?> xe = cl.loadClass("niagara.xml.XElem"), xt = cl.loadClass("niagara.xml.XText");
    b.append('<').append(xe.getMethod("qname").invoke(e)).append('@').append(xe.getMethod("line").invoke(e));
    int n = (int) xe.getMethod("attrSize").invoke(e);
    for (int i = 0; i < n; i++) b.append(' ').append(xe.getMethod("attrName", int.class).invoke(e, i)).append("=[").append(xe.getMethod("attrValue", int.class).invoke(e, i)).append(']');
    b.append('>');
    int c = (int) xe.getMethod("contentSize").invoke(e);
    for (int i = 0; i < c; i++) { Object k = xe.getMethod("content", int.class).invoke(e, i);
      if (xe.isInstance(k)) dump(cl, k, b); else b.append((boolean) xt.getMethod("isCDATA").invoke(k) ? "C[" : "T[").append(xt.getMethod("string").invoke(k)).append(']'); }
    b.append("</>");
  }
  static void same(String what, java.util.function.Function<ClassLoader, String> f) {
    String a = f.apply(ARMS[0]);
    for (int i = 1; i < 3; i++) { String o = f.apply(ARMS[i]);
      if (!a.equals(o)) throw new AssertionError(what + " orig!=" + NAMES[i] + "\n orig=" + a + "\n " + NAMES[i] + "=" + o); }
  }
  @Property(tries = 5000, seed = "118") void safeEscapingAgrees(@ForAll String s, @ForAll boolean ws) { same("safe", cl -> safe(cl, s, ws)); }
  @Property(tries = 5000, seed = "118") void escapedRoundTripAgrees(@ForAll String s, @ForAll boolean ws) {
    same("roundtrip", cl -> { String e = safe(cl, s, true); if (!e.startsWith("OK:")) return e; String v = e.substring(3);
      return parse(cl, "<r a=\"" + v + "\">" + v + "</r>", ws); }); }
  @Provide Arbitrary<String> xmlish() { return Arbitraries.strings().withChars("<>/&;=\"' \n\t\rab:#x![]-?é\u0000\ud800").ofMaxLength(40)
      .map(s -> "<r" + s + "</r>"); }
  @Property(tries = 10000, seed = "118") void rawParseAgrees(@ForAll("xmlish") String xml, @ForAll boolean ws) { same("raw", cl -> parse(cl, xml, ws)); }
}
