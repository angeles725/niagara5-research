/*
 * n5-hello PoC — Block 9 (niagara5-research)
 * Resolved by hand from devkit.jar!LIB-INF/n-templates-5.0.54.9.2.jar
 * gradle/settings.gradle.kts.vm + gradle/includes/niagara/settingsRepoUrl.txt
 * + gradle/includes/niagara/settingsRepos.txt (Velocity #include directives
 * inlined manually — no Velocity engine run in this PoC).
 */

import com.tridium.gradle.plugins.settings.MultiProjectExtension
import com.tridium.gradle.plugins.settings.LocalSettingsExtension

pluginManagement {
  val niagaraHome: Provider<String> = providers.gradleProperty("niagara_home").orElse(
    providers.systemProperty("niagara_home").orElse(
      providers.environmentVariable("NIAGARA_HOME").orElse(
        providers.environmentVariable("niagara_home")
      )
    )
  )

  val gradlePluginHome: String = providers.gradleProperty("gradlePluginHome").orElse(
    providers.environmentVariable("GRADLE_PLUGIN_HOME").orElse(
      niagaraHome.map { "$it/etc/m2/repository" }
    )
  ).orNull ?: throw InvalidUserDataException("Could not derive gradlePluginHome/niagara_home")

  val gradlePluginRepoUrl = "file:///${gradlePluginHome.replace('\\', '/').replace(" ", "%20")}"

  val gradlePluginVersion: String = "5.0.54.9.2"
  val settingsPluginVersion: String = "5.0.9.8.14"

  repositories {
    maven(url = gradlePluginRepoUrl)
    gradlePluginPortal()
  }

  plugins {
    id("com.tridium.set.mpr") version (settingsPluginVersion)
    id("com.tridium.set.lsc") version (settingsPluginVersion)

    id("com.tridium.niagara") version (gradlePluginVersion)
    id("com.tridium.vendor") version (gradlePluginVersion)
    id("com.tridium.n-module") version (gradlePluginVersion)
    id("com.tridium.n-java") version (gradlePluginVersion)
    id("com.tridium.sign") version (gradlePluginVersion)
    id("com.tridium.bajadoc") version (gradlePluginVersion)
    id("com.tridium.jacoco") version (gradlePluginVersion)
    id("com.tridium.nap") version (gradlePluginVersion)

    id("com.tridium.conv.n-repo") version (gradlePluginVersion)
  }
}

plugins {
  // Discover all subprojects in this build
  id("com.tridium.set.mpr")

  // Apply local settings from local/my-settings.gradle(.kts) if they are present
  id("com.tridium.set.lsc")
}

configure<LocalSettingsExtension> {
  loadLocalSettings()
}

configure<MultiProjectExtension> {
  findProjects()
}

rootProject.name = "n5-hello"
