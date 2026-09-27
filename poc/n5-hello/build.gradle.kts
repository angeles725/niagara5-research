/*
 * n5-hello PoC — root build script.
 * Resolved by hand from gradle/build.gradle.kts.vm.
 */

plugins {
  id("com.tridium.niagara")
  id("com.tridium.vendor")
  id("com.tridium.sign")
  id("com.tridium.conv.n-repo")
}

vendor {
  defaultVendor("poc")
  defaultModuleVersion("1.0.0")
}

subprojects {
  repositories {
    mavenCentral()
    mavenLocal()
  }
}
