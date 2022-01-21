---
title: Transparent status bar in Android
date: 2022-01-17
---

# Transparent status bar in Android

I didn't like that if I want to something a little complex, I need to google all around, and common
example for this is handling status bar and navigation bar, or handling insets in common.
Also I wanted to use Compose for these thingy.

Once I wanted to implement [Full Screen Dialog](https://material.io/components/dialogs#full-screen-dialog),
**which lays below system insets**.  
I googled around, but I found some do not fit for modern Android frameworke as they are deprecated.


## TL; DR

1. Insert the following style into your dialog style.

``` xml
<style name="AppTheme.Dialog">
  <item name="android:windowDrawsSystemBarBackgrounds">true</item>
  <item name="android:windowBackground">@null</item>
  <item name="android:windowFrame">@null</item>
  <item name="android:windowIsFloating">false</item>
  <item name="android:windowContentOverlay">@null</item>
  <item name="android:windowAnimationStyle">@android:style/Animation.Dialog</item>
</style>
```

Vital items are:

- `android:windowDrawsSystemBarBackgrounds`: Enables drawing under system bar.
- `android:windowFrame`: If dialog frame exists, it won't fill the whole screen.
- `android:windowIsFloating`: `true` value of this enforces window insets not to be passed
  to views, causing Window itself consuming it with color.


2. In your dialog code, put the following code.

``` kotlin
window.setLayout(WindowManager.LayoutParams.MATCH_PARENT, WindowManager.LayoutParams.MATCH_PARENT)
WindowCompat.setDecorFitsSystemWindows(window, false)
```

`#!kotlin WindowCompat.setDecorFitsSystemWindows` will fall back to setting system ui visibility under
Android API 30, so you don't need to write system ui ones by yourself.
