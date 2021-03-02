---
title: How Jetpack Compose Works
date: 2021-02-28
---

# How Jetpack Compose works
!!! warning "**Under Construction**"
    This document is not completed.


While I'm using jetpack compose, I was quite impressed
how it was beautiful to write UI.
(but note that Jetpack Compose itself has to do nothing with UI; it's a tool for building trees)

I wondered how it works, I digged its runtime and compiler plugin.
These are what I found.

!!! note
    Compose is in beta stage; these contents may be obsolete.
    Disclaimer: you may expect poor English & explaination

## How it diffs the tree
Composable functions are what is called every time it recomposes.
Calling another composable function marks that invocation into the **Composer**,
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
It finally calls `composer.recordReadOf(state)` so your composable
function automatically subscribes to that state.
This is why you should not use normal mutable objects: they
do not subscribe to the current snapshot.

There are some predefined types: `SnapshotStateList` and
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


``` kotlin
@Composable
fun MyComposable(name: String, $composer: Composer<*>, $changed: Int) {
```



``` kotlin
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



* **Uncertain**(000)
  Indicates that nothing is certain about the current state of the parameter. It could be different than it was during the last execution, or it could be the same, but it is not known so the current function looking at it must call equals on it in order to find out.
  This is the only state that can cause the function to spend slot table space in order to look at it.
* **Same**(001)
  This indicates that the value is known to be the same since the last time the function was executed. There is no need to store the value in the slot table in this case because the calling function will *always* know whether the value was the same or different as it was in the previous execution.
* **Static**(011)
  This indicates that the value is known to be different since the last time the function was executed. There is no need to store the value in the slot table in this case because the calling function will *always* know whether the value was the same or different as it was in the previous execution.
* **Different**(010)
  This indicates that the value is known to *never change* for the duration of the running program.



