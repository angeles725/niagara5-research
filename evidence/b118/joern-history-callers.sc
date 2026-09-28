importCpg("history.cpg.bin")
println("TYPES=" + cpg.typeDecl.isExternal(false).size + " METHODS=" + cpg.method.isExternal(false).size)
cpg.call.name("getPermissions").filter(_.methodFullName.contains("BRootHistoryFolder")).map(c => "SITE " + c.method.fullName + " line=" + c.lineNumber.getOrElse(-1) + " -> " + c.methodFullName).l.sorted.foreach(println)
cpg.method.fullNameExact("com.tridium.history.BRootHistoryFolder.getPermissions:niagara.security.BPermissions(niagara.sys.Context)").caller.fullName.l.distinct.sorted.foreach(c => println("CALLER " + c))
