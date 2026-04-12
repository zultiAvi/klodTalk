package com.klodtalk.app

import android.content.Context

class CrashHandler(
    private val context: Context,
    private val default: Thread.UncaughtExceptionHandler?
) : Thread.UncaughtExceptionHandler {

    companion object {
        private const val PREFS = "klodtalk_prefs"
        const val KEY = "last_crash"

        fun install(context: Context) {
            val default = Thread.getDefaultUncaughtExceptionHandler()
            Thread.setDefaultUncaughtExceptionHandler(CrashHandler(context.applicationContext, default))
        }
    }

    override fun uncaughtException(t: Thread, e: Throwable) {
        try {
            val msg = "${System.currentTimeMillis()} thread=${t.name}\n${e.stackTraceToString()}"
            context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .edit().putString(KEY, msg).commit()
        } catch (_: Exception) {}
        default?.uncaughtException(t, e)
    }
}
