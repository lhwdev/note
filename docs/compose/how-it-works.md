---
title: How Compose Works
date: 2021-02-28
---

# How Compose works
!!! warning "**Under Construction**"
    This document is not completed.


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
val state = mutableStateOf("Apple") // bad practice, but for example

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

There are some predefined types to so this: `SnapshotStateList` and
`SnapshotStateMap`, in addition to `SnapshotMutableState`.


## How it compiles
**Compose compiler plugin** was built on the Backend IR,
and transforms your composable functions.

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

@Composable
fun Text(text: String, style: TextStyle = TextStyle())

@Composable
fun Button(onClick: () -> Unit, content: @Composable () -> Unit)
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
			$default = 0b00
		)
		Button(onClick = { count++ }, composableLambda($composer, key = 193702, tracked = true, null) { $composer, $changed ->
	  	Text(
				"Click $name", style = null,
				$composer = $composer,
				$changed = 0b0000000 or ($dirty and 0b1110),
				$default = 0b10
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
```
You can see an synthetic paremeter `#!kotlin $composer: Composer<*>` is added.

There's one more parameter: `$changed`.

Composable function tries to skip execution when its parameters are unchanged.
But comparing if parameters are changed is quite expensive in some cases.
So Compose tries to avoid the comparison.  
When you just passes your argument to another Composable function as-is,
Compose propagates the state, if it is changed. The state is passed through
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
  
* **Static**(11)
  This indicates that the value is known to be different since the last time
  the function was executed.
  There is no need to store the value in the slot table in this case because
  the calling function will *always* know whether the value was the same or
  different as it was in the previous execution.
  
* **Different**(10)
  This indicates that the value is known to *never change* for the duration
  of the running program.

(documentation copied from Compose source)

The lowest bit(2) indicates if it is changed, 1 for same and 0 for different.
If the state is Uncertain(00), it will be replaced by the result of comparison.

The lowest bit of `$changed` itself(31) is a special bit indicating a force
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
As described above, it checks the `$changed` parameter(in turn `dirty`).
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
		var count by $composer.cache(true) { mutableStateOf(1) }
		
		Text(
			"Clicked $count times",
			style = MaterialTheme.<get-typography>($composer, 0b0).h2,
			$composer = $composer,
			$changed = 0b0000000,
			$default = 0b00
		)
		Button(onClick = { count++ }, composableLambda($composer, key = 193702, tracked = true, null) { $composer, $changed ->
	  	Text(
				"Click $name", style = null,
				$composer = $composer,
				$changed = 0b0000000 or ($dirty and 0b1110),
				$default = 0b10
			)
		}, $composer, 0b0000000)
	} else {
		$composer.skipToGroupEnd()
	}
	$composer.endRestartGroup()?.updateScope { composer -> MyComposable(name, composer, $dirty or 0b1) }
}

// ...
```



