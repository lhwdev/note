---
title: How Compose Works
date: 2021-02-28
---

# How Compose works
{{ head() }}

!!! warning "**Under Construction**"
    This document is not completed. (but still usable)


While I'm using compose(or Jetpack Compose), I was quite impressed
how it was beautiful to write UI.
(but note that Jetpack Compose itself has to do nothing with UI; it's a tool for building trees)

I wondered how it works, I digged its runtime and compiler plugin.
These are what I found.

!!! note
    You are expected to have a background about Compose model.
    This document only covers Compose itself, not Compose UI or related.
    Compose is in beta stage; these contents may be obsolete.
    Disclaimer: you may expect poor English & explaination

## Terms
- **Composer** is what manages the state of tree. Every Composable function
  receives this as a parameter.
- **Composition** is an act building up a tree.
- **Recomposition** is an act rebuilding a tree. You can access the
  corresponding part of the previous tree if exists.


## How it diffs the tree
Composable functions are what is called every time it recomposes.
Calling another composable function marks that invocation into the Composer,
which the function receives through its parameter. Of course you cannot see it in the code,
but it does receive after transformed by compiler plugin.
Then, Composer internally builds a **slot table** which is built on gap array.

Slot table elements are called `slot`.
The types of `slot` are: normal slot, `group`, `node`, `data`, etc.
These are well explained in the [source code of SlotTable](https://android.googlesource.com/platform/frameworks/support/+/refs/heads/androidx-main/compose/runtime/runtime/src/commonMain/kotlin/androidx/compose/runtime/SlotTable.kt).
One important thing is: `node`. Node is tracked by the Composer.
When adapting Compose to your need(again, compose is a tree managing tool), you use `Applier`.
When a node is inserted or removed, you get a callback from this.

When first composing, Composer just writes down your composable into slot table.
In the recomposition, if structure changes composer diffs your tree.
But note that this diffing is not so same as something like React. Compiler plugin
provides some diffing(it gives composer some hints about control flows
and loops), so it has less overhead.

There is [a great video describing about this](https://youtu.be/Q9MtlmmN4Q0).

I'll explain more about other things.


## How it detects state changes
Consider the code below:
``` kotlin
val state = mutableStateOf("Apple") // just for example

@Composable
fun A() {
	Text("wow, ${state.value}!")
	Button(onClick = { state.value = "Banana" }) {
		Text("hi")
	}
}
```
Clicking the button changes the `state`, and
`A` is recomposed automatically. But how?

**Snapshot** system handles this.
While composing, your composer registers an observer to the current snapshot,
and reading the state will fire the observer.
It finally calls `#!kotlin composer.recordReadOf(state)` so your composable
function automatically subscribes to that state.
This is why you should not use normal mutable objects: they
do not subscribe to the current snapshot by themselves.

There are some predefined types to do this: `SnapshotStateList` and
`SnapshotStateMap`, in addition to `SnapshotMutableState`.


## How it compiles
**Compose compiler plugin** is built on the Backend IR,
and transforms your Composable functions.

Your code:
``` kotlin
@Composable
fun MyComposable(name: String) {
	var count by remember { mutableStateOf(1) }

	Text("Clicked $count times", style = MaterialTheme.typography.h2)
	Button(onClick = { count++ }) {
		Text("Click $name")
	}
}


// stubs for Compose UI

@Composable
fun Text(text: String, style: TextStyle = TextStyle())

@Composable
fun Button(onClick: () -> Unit, content: @Composable () -> Unit)

object MaterialTheme {
	val typography: Typography
		@Composable get() = TODO()
}

data class Typography(val h2: TextStyle)
```

Compiled output(pseudo code):
``` kotlin
@Composable
fun MyComposable(name: String, $composer: Composer<*>, $changed: Int) {
	$composer.startRestartGroup(193822) // a hash of source location, eg) "com.example/myFile.kt/MyComposable"
	val $dirty = $changed // 'val' is not a typo

	if($dirty and 0b0110 == 0)
		$dirty = $dirty or if($composer.changed(name)) 0b0010 else 0b0100

	if($dirty and 0b1011 xor 0b1010 != 0 || !$composer.skipping) {
		var count by $composer.cache(true) { mutableStateOf(1) }

		Text(
			"Clicked $count times",
			style = MaterialTheme.<get-typography>($composer, 0b0).h2,
			$composer = $composer,
			$changed = 0b0000000,
			$default = 0b0
		)
		Button(onClick = { count++ }, composableLambda($composer, key = 193702, tracked = true, null) { $composer, $changed ->
			Text(
				"Click $name", style = null,
				$composer = $composer,
				$changed = 0b0000000 or ($dirty and 0b1110),
				$default = 0b1
			)
		}, $composer, 0b0000000)
	} else {
		$composer.skipToGroupEnd()
	}
	$composer.endRestartGroup()?.updateScope { composer -> MyComposable(name, composer, $dirty or 0b1) }
}

// ...
```

Wow, lots of things are done!
Let's break up these things into pieces.

The semantic of Composable function is similar to `#!kotlin suspend fun`.

> `#!kotlin suspend fun` can call `#!kotlin suspend fun`;
  normal function cannot call `#!kotlin suspend fun`.

Likewise, normal function cannot call `#!kotlin @Composable fun`.
This is because, basically they are a different kind of function, and they
receives an additional synthetic parameter: Composer.


``` kotlin
@Composable
fun MyComposable(name: String, $composer: Composer<*>, $changed: Int) {
	// ...
}
```
You can see an synthetic paremeter `#!kotlin $composer: Composer<*>` is added.

There's one more parameter: `$changed`.

Composable function tries to skip execution when its parameters are unchanged.
But comparing if parameters are changed is quite expensive in some cases.
So Compose tries to avoid the comparison.
When you just passes your argument to another Composable function as-is,
Compose propagates the state, whether it is changed. The state is passed through
`$changed`, which consists of 3-bit per parameter integer.

The highest bit(0) indicates if it is *stable*. Stability is indicated via
`#!kotlin @Stable` etc, or inferred by the compiler plugin.
1 means unstable, and 0 means stable.

Two lower bits(1, 2) indicates the status of the parameter like below.

* **Uncertain**(00)
  Indicates that nothing is certain about the current state of the parameter.
  It could be different than it was during the last execution, or it could be
  the same, but it is not known so the current function looking at it must call
  equals on it in order to find out.
  This is the only state that can cause the function to spend slot table space
  in order to look at it.

* **Same**(01)
  This indicates that the value is known to be the same since the last time
  the function was executed.
  There is no need to store the value in the slot table in this case because
  the calling function will *always* know whether the value was the same or
  different as it was in the previous execution.

* **Different**(10)
  This indicates that the value is known to be different since the last time
  the function was executed.
  There is no need to store the value in the slot table in this case because
  the calling function will *always* know whether the value was the same or
  different as it was in the previous execution.

* **Static**(11)
  This indicates that the value is known to *never change* for the duration
  of the running program.

(documentation copied from Compose source)

The lowest bit(2) indicates if it is changed, 1 for same and 0 for different.
If the state is Uncertain(00), it will be replaced by the result of comparison.

The lowest bit of `$changed` itself is a special bit indicating a force
recomposition, set to 1 when it recomposes.



``` kotlin
	$composer.startRestartGroup(193822)
```
Every Composable function produces a group.

``` kotlin
	val $dirty = $changed // 'val' is not a typo

	if($dirty and 0b0110 == 0b0000)
		$dirty = $dirty or if($composer.changed(name)) 0b0010 else 0b0100
```
As described above, it checks the `$changed` parameter(in turn `$dirty`).
If the state is Uncertain(00), it compares the parameter via
`#!kotlin $composer.changed(argument)`.

What it internally does:

1. Retrives the previous slot if exist(let be `previous`; if not exist then
  becomes a special singleton value `EMPTY`)
2. Saves the `argument` into the slot table
3. Returns `#!kotlin previous != argument`.

So if `argument` is changed, the state becomes Different(10).
If not, becomes Same(01).


``` kotlin
	if($dirty and 0b1011 xor 0b1010 != 0 || !$composer.skipping) {
		// ...
	}
```
If all parameters are Same(001) and Stable(100), and the composer allows
skipping, the execution is skipped. If not, it will execute.


``` kotlin
		var count by $composer.cache(true) { mutableStateOf(1) }
```
This is special kind of transformation. `#!kotlin remember(..) { expr }`
becomes `#!kotlin $composer.cache(..) { expr }`.
`true` means it does not always have to update.


``` kotlin
		Text(
			"Clicked $count times",
			style = MaterialTheme.<get-typography>($composer, 0b0).h2,
			$composer = $composer,
			$changed = 0b0000000,
			$default = 0b0
		)
```
This is a normal Composable function call.

You can see something strange:
`#!kotlin MaterialTheme.<get-typography>($composer, 0b0)`.
As you might know, every property consists of getter, optional setter, and
optional backing field. Getting property basically corresponds to calling getter
internally. Its name is called `<get-propertyName>` in IR.
As it is a normal function, compiler plugin can add a value parameter to getter.
(yet impossible in plain Kotlin code)

So, Composable function passes its `$composer` to Composable function,
and `$changed` argument. It checks for all dependencies associated with that
argument. For example, if the argument is `#!kotlin "Hello, $name($age)!"`,
it depends on `name` and `age`.

- If a variable is
  * `#!kotlin const val`, global `val`, object etc: Static
  * remember without keys(`#!kotlin remember(/* nothing here */) { .. }`): Static
  * parameter: delegated (like `#!kotlin $changedN and 0b1110 shl 3`)
- If an expression is
  * builtin expressions(Int.plus, "$variable, string, ${someExpr()}" etc):
    combine all of its value parameters/receivers
  * calling `#!kotlin @Stable fun`: combine all of
  * unknown arbitrary function call: Unknown

Also, whether all dependencies are *Stable* is marked.
For more information, you can check [the source code of StabilityInferencer](https://android.googlesource.com/platform/frameworks/support/+/refs/heads/androidx-main/compose/compiler/compiler-hosted/src/main/java/androidx/compose/compiler/plugins/kotlin/analysis/Stability.kt).


You can also see `$default`. Compose compiler plugin handles the default
parameter by itself. It is almost identical to that of Kotlin, but Compose
do not generate another function.

Bit `1` means caller did **not** provide that parameter so requires
special handling.


``` kotlin
		Button(onClick = { count++ }, composableLambda($composer, key = 193702, tracked = true, null) { $composer, $changed -> /* ... */ })
```
Composable lambda is handled specially.
Group is inserted surrounding most Composable functions, but it is inserted by
`composableLambda`.

Compose compiler plugin remembers the resulting lambda instance, and even
the original lambda itself if it does not have captures.
So the result of `#!kotlin composableLambda(..)`, hence seemingly all the
Composable lambda is ensured to be identical(`a === b`).


``` kotlin
			Text(
				"Click $name", style = null,
				$composer = $composer,
				$changed = 0b0000000 or ($dirty and 0b1110),
				$default = 0b1
			)
		}, $composer, 0b0000000)
```
Here we propagate the state of parameter `name` to the first argument `text`.
We also use the default value of `style`, so we pass `#!kotlin $default = 0b1`.


``` kotlin
	else {
		$composer.skipToGroupEnd()
	}
```
If we can skip this function, skip it.


``` kotlin
	$composer.endRestartGroup()?.updateScope { composer -> MyComposable(name, composer, $dirty or 0b1) }
```
Finally, ends the group.
`updateScope() { ... }` is related to Composable function Restart.
If it can, it updates the restartable scope.
The lambda provided to `updateScope` is used to restart the Composable function.
If something changes, like updating state happen, Compose finds the subscribers
(where the state is used) and retrieves the nearest restartable scope, and
invokes it.

You can see Compose compiler plugin is quite complex.


Composer does more: it transforms **control flows** and **loops**.


``` kotlin
if(condition) {
	simpleFunction()
	a += 1
}
```
Codes like this are not transformed, but

``` kotlin
if(condition) {
	ComposableFunction()
}
```
Codes that calls Composable fun in the condition or its result gets transformed.

Result:
``` kotlin
if(condition) {
	$composer.startReplaceableGroup(29381)
	ComposableFunction($composer, 0)
} else {
	$composer.startReplaceableGroup(193052)
}
$composer.endReplaceableGroup()
```

That is, Compose compiler handles code that **may not run only once**.
In the previous example, `ComposableFunction` may not run or may run once.

The reason composer handles this is: Composer call is sequential.
Without this transformation, the tree may go wrong.



