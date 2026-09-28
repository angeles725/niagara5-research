import java.util.*;
public class F {
  static int inst(Object o){ if (o instanceof String) { String s=(String)o; return s.length(); } return 0; }
  static int v(){ ArrayList<String> l=new ArrayList<String>(); return l.size(); }
  static String tb(){ return "line1\n" + "line2\n"; }
  static int ef(int[] a){ int t=0; for(int i=0;i<a.length;i++){ int x=a[i]; t+=x; } return t; }
  static int efi(List<String> l){ int t=0; for(Iterator<String> it=l.iterator(); it.hasNext();){ String s=it.next(); t+=s.length(); } return t; }
  static int sw(int k){ int r; switch(k){ case 1: r=10; break; case 2: r=20; break; default: r=0; } return r; }
  static int ss(String k){ switch(k){ case "a": return 1; case "b": return 2; default: return 0; } }
  static String cat(String a,int b){ return a + b; }
  static Runnable lam(){ return new Runnable(){ public void run(){} }; }
  static int tsw(Object o){ if (o instanceof String) return 1; else if (o instanceof Integer) return 2; return 0; }
}
