/*
 * n5-hello PoC — module subproject build script.
 * Resolved by hand from gradle/module/module.gradle.kts.vm +
 * gradle/includes/niagara/modulePlugins.vm + gradle/includes/niagara/moduleDependencies.vm.
 */

import com.tridium.gradle.plugins.bajadoc.task.Bajadoc

plugins {
  id("com.tridium.n-module")
  id("com.tridium.n-helper-modularity")
  id("com.tridium.n-java")
  id("com.tridium.sign")
  id("com.tridium.bajadoc")
  id("com.tridium.jacoco")
  id("com.tridium.nap")
  id("com.tridium.conv.n-repo")
}

moduleManifest {
  moduleName.set("n5Hello")
  checkModuleName.set(false)
}

// See doc/buildN5.html "Dependency Configurations" table.
dependencies {
  // NRE dependencies
  nre(":niagaraAnnotationProcessors")
  nre(":nre")

  // Niagara annotation processor dependency (split from :nre in N5 — doc/buildN5.html
  // "Niagara annotation processors" section)
  niagaraAnnotationProcessor(":niagaraAnnotationProcessors")

  // Niagara module dependencies — BComponent lives in baja; dependsOnBaja defaults true
  // in ModuleXml but this makes the Gradle compile-classpath dependency explicit too.
  api(":baja")
}

tasks.named<Bajadoc>("bajadoc") {
  includePackage("poc.n5hello")
}
