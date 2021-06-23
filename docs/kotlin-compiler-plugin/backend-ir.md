---
title: Writing a Kotlin Backend IR Compiler Plugin
date: 2021-03-15
---


# Writing a Kotlin Backend IR Compiler Plugin
{{ head() }}

!!! warning "**Under Construction**"
    This document is not completed.


**Backend IR** is a new, unified way of writing a compiler plugin.
Currently IR is in a beta stage, and will be the default backend in Kotlin 1.5.
Compared to a bare compiler plugin written for JVM, Backend IR has some benefits:

- easier to write (a lot!)
- not platform dependant
- works well with other compiler plugins


## Get started
You need to enable IR so far: kotlinc argument `-Xuse-ir`.

Add kotlin compiler plugin library:
``` kotlin
// gradle
dependencies {
	// ...
	compileOnly("org.jetbrains.kotlin:kotlin-compiler-embeddable:$kotlinVersion")
}
```

The entrypoint for all kotlin compiler plugin is CommandLineProcessor and
ComponentRegistrar.

``` kotlin
class MyCommandLineProcessor : CommandLineProcessor {
	override val pluginId = "com.myplugin"
	override val pluginOptions = emptyList<CliOption>()
}
```

``` kotlin
class MyComponentRegistrar : ComponentRegistrar {
	override fun registerProjectComponents(project: MockProject, configuration: CompilerConfiguration) {
		println("Hello, ComponentRegistrar!")
	}
}
```

You need to add services for these.
Go to resources di, make `META-INF/services/` 





