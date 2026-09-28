importCpg("signing.cpg.bin")
def src = cpg.call.name("getExtensions").filter(_.methodFullName.contains("NPKCS10CertificationRequest"))
def snk = cpg.call.name("addExtension").filter(_.methodFullName.contains("NSigningParameters")).argument(1)
println("SOURCES=" + src.size + " SINKS=" + snk.size)
snk.l.foreach(s => println("SINK line=" + s.lineNumber.getOrElse(-1) + " in " + s.method.name))
val flows = snk.reachableByFlows(src).l
println("FLOWS=" + flows.size)
flows.foreach(f => println("FLOW " + f.elements.map(e => e.lineNumber.getOrElse(-1)).mkString("->")))
