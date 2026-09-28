import java.util.*;
public class F {
  static int inst(Object o){ if (o instanceof String s) { return s.length(); } return 0; }
  static int v(){ var l=new ArrayList<String>(); return l.size(); }
  static String tb(){ return """
      line1
      line2
      """; }
  static int ef(int[] a){ int t=0; for(int x: a){ t+=x; } return t; }
  static int efi(List<String> l){ int t=0; for(String s: l){ t+=s.length(); } return t; }
  static int sw(int k){ int r = switch(k){ case 1 -> 10; case 2 -> 20; default -> 0; }; return r; }
  static int ss(String k){ return switch(k){ case "a" -> 1; case "b" -> 2; default -> 0; }; }
  static String cat(String a,int b){ return a + b; }
  static Runnable lam(){ return () -> {}; }
  static int tsw(Object o){ return switch(o){ case String s -> 1; case Integer i -> 2; default -> 0; }; }
}
