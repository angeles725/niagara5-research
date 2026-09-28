/**
 * @name B118 CSR extension to issued-certificate flow
 * @kind problem
 * @id b118/csr-ext-flow
 */
import java
import semmle.code.java.dataflow.DataFlow
import semmle.code.java.dataflow.TaintTracking
import semmle.code.java.controlflow.Guards

module CsrCfg implements DataFlow::ConfigSig {
  predicate isSource(DataFlow::Node n) {
    exists(MethodCall mc | mc.getMethod().hasName("getExtensions") and
      mc.getMethod().getDeclaringType().getName() = "NPKCS10CertificationRequest" and n.asExpr() = mc)
  }
  predicate isSink(DataFlow::Node n) {
    exists(MethodCall mc | mc.getMethod().hasName("addExtension") and
      mc.getMethod().getDeclaringType().getName() = "NSigningParameters" and n.asExpr() = mc.getArgument(0))
  }
  /** for-each element step: iterable expression -> every access of the loop variable (arrays carry no stored content here). */
  predicate isAdditionalFlowStep(DataFlow::Node a, DataFlow::Node b) {
    exists(EnhancedForStmt f | a.asExpr() = f.getExpr() and b.asExpr() = f.getVariable().getVariable().getAnAccess())
  }
}
module CsrFlow = TaintTracking::Global<CsrCfg>;

from DataFlow::Node src, DataFlow::Node snk, MethodCall add, string guard
where CsrFlow::flow(src, snk) and snk.asExpr() = add.getArgument(0) and
  (
    if exists(Guard g, MethodCall gm | g = gm and gm.getMethod().getName().matches("is%ExtensionValid") and g.controls(add.getBasicBlock(), true))
    then guard = concat(MethodCall gm, Guard g | g = gm and gm.getMethod().getName().matches("is%ExtensionValid") and g.controls(add.getBasicBlock(), true) | gm.getMethod().getName(), ",")
    else guard = "UNGUARDED"
  )
select add, "CSR getExtensions() at line " + src.getLocation().getStartLine() + " flows to addExtension at line " + add.getLocation().getStartLine() + " guard=" + guard
