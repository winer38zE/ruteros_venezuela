allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

val newBuildDir: Directory =
    rootProject.layout.buildDirectory
        .dir("../../build")
        .get()
rootProject.layout.buildDirectory.value(newBuildDir)

subprojects {
    val newSubprojectBuildDir: Directory = newBuildDir.dir(project.name)
    project.layout.buildDirectory.value(newSubprojectBuildDir)
}

// Plugins viejos (isar_flutter_libs) no declaran namespace. AGP 8 lo exige
// antes de crear las variantes, y el compileSdk 30 ya no está instalado.
subprojects {
    afterEvaluate {
        val androidExt = extensions.findByName("android") ?: return@afterEvaluate
        val namespace = androidExt.javaClass.methods
            .firstOrNull { it.name == "getNamespace" && it.parameterCount == 0 }
            ?.invoke(androidExt) as? String
        if (namespace.isNullOrBlank()) {
            val fallback = group.toString().takeIf { it.isNotBlank() && it != "unspecified" } ?: name
            androidExt.javaClass.methods
                .firstOrNull { it.name == "setNamespace" && it.parameterCount == 1 }
                ?.invoke(androidExt, fallback)
        }
        val compileSdk = androidExt.javaClass.methods
            .firstOrNull { it.name == "getCompileSdk" && it.parameterCount == 0 }
            ?.invoke(androidExt) as? Int
        if (compileSdk != null && compileSdk < 34) {
            androidExt.javaClass.methods
                .firstOrNull { it.name == "setCompileSdk" && it.parameterCount == 1 }
                ?.invoke(androidExt, 36)
        }
    }
}
subprojects {
    project.evaluationDependsOn(":app")
}

tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}
