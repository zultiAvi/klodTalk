package com.klodtalk.app

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.*
import androidx.core.content.ContextCompat
import androidx.core.view.WindowCompat
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.ViewModelProvider
import com.klodtalk.app.ui.screens.HistoryScreen
import com.klodtalk.app.ui.screens.SessionsScreen
import com.klodtalk.app.ui.screens.SettingsScreen
import com.klodtalk.app.ui.theme.KlodTalkTheme
import com.klodtalk.app.viewmodel.MainViewModel
import com.klodtalk.app.viewmodel.Screen
import com.klodtalk.app.KlodTalkService

class MainActivity : ComponentActivity() {

    private lateinit var viewModel: MainViewModel

    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { /* permissions are checked again before speech recognition starts */ }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        CrashHandler.install(this)

        // Enable edge-to-edge layout; each screen's Scaffold consumes the resulting insets.
        WindowCompat.setDecorFitsSystemWindows(window, false)
        viewModel = ViewModelProvider(this)[MainViewModel::class.java]
        requestPermissions()

        // Start foreground service to keep WebSocket alive when app is backgrounded
        startForegroundService(
            Intent(this, KlodTalkService::class.java).also { it.action = KlodTalkService.ACTION_START }
        )

        lifecycle.addObserver(LifecycleEventObserver { _, event ->
            if (event == Lifecycle.Event.ON_STOP) {
                viewModel.onAppBackgrounded()
            }
        })

        // Handle cold-start from notification
        intent?.let { handleOpenSessionIntent(it) }

        setContent {
            KlodTalkTheme {
                val screen by viewModel.screen.collectAsState()

                when (screen) {
                    Screen.SETTINGS -> SettingsScreen(
                        viewModel = viewModel,
                        onConnected = { viewModel.goToSessions() }
                    )
                    Screen.SESSIONS -> SessionsScreen(viewModel = viewModel)
                    Screen.HISTORY -> HistoryScreen(viewModel = viewModel)
                }
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        // Don't stop the service during configuration changes (e.g. rotation)
        if (!isChangingConfigurations) {
            startService(
                Intent(this, KlodTalkService::class.java).also { it.action = KlodTalkService.ACTION_STOP }
            )
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        handleOpenSessionIntent(intent)
    }

    override fun onResume() {
        super.onResume()
        viewModel.onAppForegrounded()
    }

    private fun handleOpenSessionIntent(intent: Intent) {
        if (intent.action == "OPEN_SESSION") {
            val sessionId = intent.getStringExtra("session_id") ?: return
            viewModel.navigateToSession(sessionId)
        }
    }

    private fun requestPermissions() {
        val needed = mutableListOf<String>()

        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
            != PackageManager.PERMISSION_GRANTED) {
            needed.add(Manifest.permission.RECORD_AUDIO)
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
            != PackageManager.PERMISSION_GRANTED) {
            needed.add(Manifest.permission.POST_NOTIFICATIONS)
        }

        if (needed.isNotEmpty()) {
            if (needed.contains(Manifest.permission.RECORD_AUDIO) &&
                shouldShowRequestPermissionRationale(Manifest.permission.RECORD_AUDIO)) {
                android.app.AlertDialog.Builder(this)
                    .setTitle("Microphone Permission")
                    .setMessage(
                        "KlodTalk uses your microphone only for speech-to-text on your device. " +
                        "No audio is ever recorded, stored, or sent anywhere — only the " +
                        "transcribed text is used."
                    )
                    .setPositiveButton("Continue") { _, _ ->
                        permissionLauncher.launch(needed.toTypedArray())
                    }
                    .setNegativeButton("Not Now", null)
                    .show()
            } else {
                permissionLauncher.launch(needed.toTypedArray())
            }
        }
    }
}
