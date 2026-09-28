import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import niagara.xml.*;
/** B118 M3 differential harness: parse every input with niagara.xml.XParser (whichever build is first on the classpath),
 *  print a canonical dump + re-serialization. Deterministic; one line per (input, mode). */
public class XpDiff {
  public static void main(String[] a) throws Exception {
    File[] fs = new File(a[0]).listFiles(); Arrays.sort(fs);
    PrintStream out = new PrintStream(new FileOutputStream(a[1]), true, "UTF-8");
    out.println("# XParser from: " + XParser.class.getProtectionDomain().getCodeSource().getLocation());
    for (File f : fs) for (boolean ws : new boolean[]{false, true}) {
      String xml = new String(Files.readAllBytes(f.toPath()), StandardCharsets.UTF_8);
      StringBuilder d = new StringBuilder();
      try {
        XElem root = XParser.make(xml, ws).parse();
        dump(root, d);
        ByteArrayOutputStream bo = new ByteArrayOutputStream(); XWriter w = new XWriter(bo); root.write(w); w.flush();
        d.append(" |W|").append(new String(bo.toByteArray(), StandardCharsets.UTF_8));
      } catch (Throwable t) { d.append("EXC ").append(t.getClass().getName()).append(": ").append(t.getMessage()); }
      out.println(f.getName() + "\tws=" + ws + "\t" + sha(d.toString()) + "\t" + d.toString().replace("\n", "\\n").replace("\r", "\\r"));
    }
  }
  static void dump(XElem e, StringBuilder b) {
    b.append("<").append(e.qname()).append("{").append(e.uri()).append("}@").append(e.line());
    for (int i = 0; i < e.attrSize(); i++) b.append(" ").append(e.attrNs(i) == null ? "" : e.attrNs(i).prefix() + ":").append(e.attrName(i)).append("=[").append(e.attrValue(i)).append("]");
    b.append(">");
    for (int i = 0; i < e.contentSize(); i++) {
      XContent c = e.content(i);
      if (c instanceof XElem ce) dump(ce, b); else { XText t = (XText) c; b.append(t.isCDATA() ? "C[" : "T[").append(t.string()).append("]"); }
    }
    b.append("</>");
  }
  static String sha(String s) throws Exception { byte[] h = MessageDigest.getInstance("SHA-256").digest(s.getBytes(StandardCharsets.UTF_8)); StringBuilder b = new StringBuilder(); for (int i = 0; i < 8; i++) b.append(String.format("%02x", h[i])); return b.toString(); }
}
