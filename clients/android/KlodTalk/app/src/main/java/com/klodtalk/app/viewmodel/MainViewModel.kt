package com.klodtalk.app.viewmodel

import android.app.Application
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import android.util.Log
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.klodtalk.app.network.*
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import java.util.Locale

enum class AppState {
    IDLE, LISTENING, PROCESSING, REVIEW, ADDING, ADD_PROCESSING
}

enum class Screen {
    SETTINGS, SESSIONS, HISTORY
}

data class SessionHistory(
    val session: SessionInfo,
    val messages: List<HistoryMessage>,
)

data class PreparingSession(
    val tempId: String,
    val projectName: String,
)

class MainViewModel(application: Application) : AndroidViewModel(application) {

    companion object {
        private const val TAG = "MainViewModel"
        private const val PREFS_NAME = "klodtalk_prefs"
        private const val PROCESSING_TIMEOUT_MS = 5000L
    }

    private val mainHandler = Handler(Looper.getMainLooper())
    private val prefs = application.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    private val _screen = MutableStateFlow(Screen.SETTINGS)
    val screen: StateFlow<Screen> = _screen

    private val _appState = MutableStateFlow(AppState.IDLE)
    val appState: StateFlow<AppState> = _appState

    private val _transcribedText = MutableStateFlow("")
    val transcribedText: StateFlow<String> = _transcribedText

    private var finalizedText = ""
    private var currentPartial = ""
    private var pendingStop = false
    private var isAddMode = false
    private var addFinalized = ""
    private var addPartial = ""

    private val _addedSnippet = MutableStateFlow("")
    val addedSnippet: StateFlow<String> = _addedSnippet

    private val _addLivePreview = MutableStateFlow("")
    val addLivePreview: StateFlow<String> = _addLivePreview

    private val _connectionStatus = MutableStateFlow("")
    val connectionStatus: StateFlow<String> = _connectionStatus

    private val _lastServerMessage = MutableStateFlow("")
    val lastServerMessage: StateFlow<String> = _lastServerMessage

    private val _projects = MutableStateFlow<List<ProjectInfo>>(emptyList())
    val projects: StateFlow<List<ProjectInfo>> = _projects

    private val _sessions = MutableStateFlow<Map<String, SessionInfo>>(emptyMap())
    val sessions: StateFlow<Map<String, SessionInfo>> = _sessions

    private val _sessionHistories = MutableStateFlow<Map<String, SessionHistory>>(emptyMap())
    val sessionHistories: StateFlow<Map<String, SessionHistory>> = _sessionHistories

    private val _unreadSessions = MutableStateFlow<Set<String>>(emptySet())
    val unreadSessions: StateFlow<Set<String>> = _unreadSessions

    private val _preparingSessions = MutableStateFlow<List<PreparingSession>>(emptyList())
    val preparingSessions: StateFlow<List<PreparingSession>> = _preparingSessions

    private val _justCreatedSessions = MutableStateFlow<Set<String>>(emptySet())
    val justCreatedSessions: StateFlow<Set<String>> = _justCreatedSessions

    private val _currentSessionId = MutableStateFlow<String?>(null)
    val currentSessionId: StateFlow<String?> = _currentSessionId

    private val _workingSessions = MutableStateFlow<Set<String>>(emptySet())
    val workingSessions: StateFlow<Set<String>> = _workingSessions

    private val _selectedTeam = MutableStateFlow<Map<String, String>>(emptyMap())  // sessionId → team name
    val selectedTeam: StateFlow<Map<String, String>> = _selectedTeam

    private val _isAppInForeground = MutableStateFlow(true)
    fun setAppForeground(fg: Boolean) { _isAppInForeground.value = fg }

    var serverIp: String
        get() = prefs.getString("server_ip", "") ?: ""
        private set(value) { prefs.edit().putString("server_ip", value).apply() }

    var serverPort: String
        get() = prefs.getString("server_port", "9000") ?: "9000"
        private set(value) { prefs.edit().putString("server_port", value).apply() }

    var serverProtocol: String
        get() = prefs.getString("server_protocol", "wss") ?: "wss"
        private set(value) { prefs.edit().putString("server_protocol", value).apply() }

    var clientName: String
        get() = prefs.getString("client_name", "") ?: ""
        private set(value) { prefs.edit().putString("client_name", value).apply() }

    var clientPassword: String
        get() = prefs.getString("client_password", "") ?: ""
        private set(value) { prefs.edit().putString("client_password", value).apply() }

    private var speechRecognizer: SpeechRecognizer? = null
    private var tts: TextToSpeech? = null
    private var ttsReady = false

    private val wsClient = WebSocketClient(object : KlodTalkWebSocketListener {
        override fun onStatusChange(status: String) { _connectionStatus.value = status }

        override fun onProjectsReceived(projects: List<ProjectInfo>) {
            _projects.value = projects
            // Auto-navigate from settings to sessions on successful authentication
            if (_screen.value == Screen.SETTINGS) {
                _screen.value = Screen.SESSIONS
            }
        }

        override fun onSessionsReceived(sessions: List<SessionInfo>, unread: List<String>) {
            val map = sessions.associateBy { it.sessionId }
            _sessions.value = map
            _unreadSessions.value = _unreadSessions.value + unread.toSet()
            _workingSessions.value = map.values
                .filter { it.working }
                .map { it.sessionId }
                .toSet()
        }

        override fun onSessionPreparing(tempId: String, projectName: String) {
            _preparingSessions.value = _preparingSessions.value + PreparingSession(tempId, projectName)
        }

        override fun onSessionCreated(session: SessionInfo) {
            // Remove matching preparing session
            if (session.tempId != null) {
                _preparingSessions.value = _preparingSessions.value.filter { it.tempId != session.tempId }
            }
            val sessionWithUsers = if (session.users.isEmpty()) {
                session.copy(users = listOf(clientName))
            } else session
            _sessions.value = _sessions.value + (session.sessionId to sessionWithUsers)
            _sessionHistories.value = _sessionHistories.value + (session.sessionId to SessionHistory(session, emptyList()))
            // Briefly mark as just-created for glow animation
            _justCreatedSessions.value = _justCreatedSessions.value + session.sessionId
            viewModelScope.launch {
                delay(3000L)
                _justCreatedSessions.value = _justCreatedSessions.value - session.sessionId
            }
            navigateToSession(session.sessionId)
        }

        override fun onSessionClosing(sessionId: String) {
            val existing = _sessions.value[sessionId]
            if (existing != null) {
                _sessions.value = _sessions.value + (sessionId to existing.copy(status = "closing"))
            }
        }

        override fun onSessionClosed(sessionId: String) {
            val existing = _sessions.value[sessionId]
            if (existing != null) {
                _sessions.value = _sessions.value + (sessionId to existing.copy(status = "closed"))
            }
        }

        override fun onSessionReopening(sessionId: String) {
            val existing = _sessions.value[sessionId]
            if (existing != null) {
                _sessions.value = _sessions.value + (sessionId to existing.copy(status = "reopening"))
            }
        }

        override fun onSessionReopened(sessionId: String) {
            val existing = _sessions.value[sessionId]
            if (existing != null) {
                _sessions.value = _sessions.value + (sessionId to existing.copy(status = "active"))
            }
        }

        override fun onNewMessage(sessionId: String, project: String, role: String, content: String, timestamp: String, model: String, team: String) {
            val msg = HistoryMessage(role = role, content = content, timestamp = timestamp, sessionId = sessionId, model = model, team = team)
            val existing = _sessionHistories.value[sessionId]
            val session = _sessions.value[sessionId] ?: SessionInfo(sessionId, project, "", "active", "")
            val msgs = (existing?.messages ?: emptyList()) + msg
            _sessionHistories.value = _sessionHistories.value + (sessionId to SessionHistory(session, msgs))

            if (sessionId != _currentSessionId.value || !_isAppInForeground.value) {
                if (role == "agent" || role == "review") {
                    _unreadSessions.value = _unreadSessions.value + sessionId
                    if (!_isAppInForeground.value) {
                        NotificationHelper.showNewMessage(
                            getApplication(), sessionId, project, content
                        )
                    }
                }
            }
        }

        override fun onHistoryReceived(
            sessions: List<Pair<SessionInfo, List<HistoryMessage>>>,
            unread: List<String>
        ) {
            // Replace from server — do not merge into old map (avoids stuck "closing" after reconnect)
            val newSessions = sessions.associate { (session, _) -> session.sessionId to session }
            val newHistories = sessions.associate { (session, messages) ->
                session.sessionId to SessionHistory(session, messages)
            }
            _sessions.value = newSessions
            _sessionHistories.value = newHistories
            _unreadSessions.value = unread.toSet()
            _workingSessions.value = newSessions.values
                .filter { it.working }
                .map { it.sessionId }
                .toSet()
            val current = _currentSessionId.value
            if (current != null && current !in newSessions) {
                _currentSessionId.value = null
                _screen.value = Screen.SESSIONS
            }
        }

        override fun onReadAck(sessionId: String) {
            _unreadSessions.value = _unreadSessions.value - sessionId
        }

        override fun onAckReceived(sessionId: String?, content: String) {
            _lastServerMessage.value = content
        }

        override fun onSessionWorking(sessionId: String, working: Boolean) {
            _workingSessions.value = if (working) {
                _workingSessions.value + sessionId
            } else {
                _workingSessions.value - sessionId
            }
        }

        override fun onSessionUserAdded(sessionId: String, targetUser: String, users: List<String>) {
            mainHandler.post {
                val existing = _sessions.value[sessionId] ?: return@post
                _sessions.value = _sessions.value + (sessionId to existing.copy(users = users))
            }
        }

        override fun onSessionUserRemoved(sessionId: String, targetUser: String, users: List<String>) {
            mainHandler.post {
                if (targetUser == clientName) {
                    // We were removed from this session
                    _sessions.value = _sessions.value - sessionId
                    _sessionHistories.value = _sessionHistories.value - sessionId
                    _unreadSessions.value = _unreadSessions.value - sessionId
                    if (_currentSessionId.value == sessionId) {
                        _currentSessionId.value = null
                        _screen.value = Screen.SESSIONS
                    }
                } else {
                    val existing = _sessions.value[sessionId] ?: return@post
                    _sessions.value = _sessions.value + (sessionId to existing.copy(users = users))
                }
            }
        }

        override fun onErrorReceived(sessionId: String?, message: String) {
            _lastServerMessage.value = "Error: $message"
            Log.e(TAG, "Server error: $message")
            // Clear preparing sessions if session creation failed (no session_id on creation errors)
            if (sessionId == null && _preparingSessions.value.isNotEmpty()) {
                _preparingSessions.value = emptyList()
            }
            // Revert closing session to active on close failure
            // Revert reopening session to closed on reopen failure
            if (sessionId != null) {
                val existing = _sessions.value[sessionId]
                if (existing != null && existing.status == "closing") {
                    _sessions.value = _sessions.value + (sessionId to existing.copy(status = "active"))
                }
                if (existing != null && existing.status == "reopening") {
                    _sessions.value = _sessions.value + (sessionId to existing.copy(status = "closed"))
                }
            }
        }
    })

    init {
        NotificationHelper.createChannel(application)
        val crash = prefs.getString(com.klodtalk.app.CrashHandler.KEY, null)
        if (crash != null) {
            Log.e(TAG, "=== PREVIOUS CRASH ===\n$crash\n======================")
            prefs.edit().remove(com.klodtalk.app.CrashHandler.KEY).apply()
        }
        initTts()
        // If already configured, skip settings screen
        if (serverIp.isNotEmpty()) {
            _screen.value = Screen.SESSIONS
        }
    }

    private fun initTts() {
        tts = TextToSpeech(getApplication()) { status ->
            if (status == TextToSpeech.SUCCESS) {
                tts?.language = Locale.US
                ttsReady = true
            }
        }
    }

    fun saveSettings(ip: String, port: String, protocol: String, name: String, password: String) {
        serverIp = ip; serverPort = port; serverProtocol = protocol
        clientName = name; clientPassword = password
    }

    fun connect() {
        wsClient.connect(serverIp, serverPort, clientName, clientPassword, serverProtocol)
    }

    fun requestHistory() {
        wsClient.sendGetHistory()
    }

    fun createSession(projectName: String) {
        wsClient.sendNewSession(projectName)
    }

    fun closeSession(sessionId: String) {
        val existing = _sessions.value[sessionId]
        if (existing != null) {
            _sessions.value = _sessions.value + (sessionId to existing.copy(status = "closing"))
        }
        wsClient.sendCloseSession(sessionId)
    }

    fun reopenSession(sessionId: String) {
        wsClient.sendReopenSession(sessionId)
    }

    fun deleteSession(sessionId: String) {
        wsClient.sendDeleteSession(sessionId)
        _sessions.value = _sessions.value - sessionId
        _sessionHistories.value = _sessionHistories.value - sessionId
        _unreadSessions.value = _unreadSessions.value - sessionId
    }

    fun navigateToSession(sessionId: String) {
        _currentSessionId.value = sessionId
        _screen.value = Screen.HISTORY
        // Mark as read
        if (_unreadSessions.value.contains(sessionId)) {
            _unreadSessions.value = _unreadSessions.value - sessionId
            wsClient.sendMarkRead(sessionId)
        }
    }

    fun goToSessions() {
        _currentSessionId.value = null
        _screen.value = Screen.SESSIONS
    }

    fun goToSettings() {
        _screen.value = Screen.SETTINGS
    }

    fun addUserToSession(sessionId: String, targetUser: String) {
        wsClient.sendAddUserToSession(sessionId, targetUser.trim())
    }

    fun removeUserFromSession(sessionId: String, targetUser: String) {
        wsClient.sendRemoveUserFromSession(sessionId, targetUser)
    }

    fun isSessionOwner(sessionId: String): Boolean {
        val session = _sessions.value[sessionId] ?: return false
        return session.userName == clientName
    }

    fun getCurrentUserName(): String = clientName

    fun selectTeam(sessionId: String, teamName: String) {
        _selectedTeam.value = _selectedTeam.value + (sessionId to teamName)
    }

    fun sendStop() {
        val sessionId = _currentSessionId.value ?: return
        wsClient.sendStop(sessionId)
    }

    fun sendBtw() {
        val sessionId = _currentSessionId.value ?: return
        val text = _transcribedText.value.trim()
        if (text.isEmpty()) return
        wsClient.sendBtw(sessionId, text)
        _transcribedText.value = ""
    }

    fun sendWithMode(mode: SendMode) {
        val sessionId = _currentSessionId.value ?: run {
            _lastServerMessage.value = "No session selected"; return
        }
        val text = _transcribedText.value.trim()
        if (text.isEmpty()) { _lastServerMessage.value = "Nothing to send"; _appState.value = AppState.IDLE; return }
        // Get team override: if selected team differs from agent default, send it
        val session = _sessions.value[sessionId]
        val projectInfo = _projects.value.find { it.name == session?.project }
        val defaultTeam = projectInfo?.team ?: ""
        val chosenTeam = _selectedTeam.value[sessionId] ?: defaultTeam
        val teamOverride = if (chosenTeam != defaultTeam) chosenTeam else ""
        val sent = wsClient.sendText(sessionId, text, mode, teamOverride)
        if (sent) {
            _lastServerMessage.value = if (mode == SendMode.EXECUTE) "Request sent" else "Processing..."
        }
        _transcribedText.value = ""
        _appState.value = AppState.IDLE
    }

    fun startTyping() {
        if (_appState.value != AppState.IDLE) return
        _transcribedText.value = ""
        _appState.value = AppState.REVIEW
    }

    fun startListening() {
        if (_appState.value != AppState.IDLE && _appState.value != AppState.REVIEW) return
        finalizedText = ""; currentPartial = ""; pendingStop = false
        _transcribedText.value = ""
        _appState.value = AppState.LISTENING
        if (ttsReady) {
            tts?.speak("Listening", TextToSpeech.QUEUE_FLUSH, null, "listening_announce")
            tts?.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
                override fun onStart(id: String?) {}
                override fun onDone(id: String?) {
                    if (id == "listening_announce") { tts?.setOnUtteranceProgressListener(null); mainHandler.post { startSpeechRecognition() } }
                }
                @Deprecated("Deprecated in Java")
                override fun onError(id: String?) { tts?.setOnUtteranceProgressListener(null); mainHandler.post { startSpeechRecognition() } }
            })
        } else { startSpeechRecognition() }
    }

    fun stopListening() {
        if (_appState.value != AppState.LISTENING) return
        pendingStop = true; _appState.value = AppState.PROCESSING
        speechRecognizer?.stopListening()
        mainHandler.postDelayed({
            if (_appState.value == AppState.PROCESSING) finalizeStop()
        }, PROCESSING_TIMEOUT_MS)
    }

    private fun finalizeStop() {
        if (currentPartial.isNotEmpty()) {
            finalizedText = if (finalizedText.isEmpty()) currentPartial else "$finalizedText $currentPartial"
            currentPartial = ""
            _transcribedText.value = finalizedText
        }
        speechRecognizer?.destroy(); speechRecognizer = null
        pendingStop = false; _appState.value = AppState.REVIEW
    }

    fun updateText(newText: String) { _transcribedText.value = newText }

    fun startAddListening() {
        if (_appState.value != AppState.REVIEW) return
        isAddMode = true; addFinalized = ""; addPartial = ""; pendingStop = false
        _addedSnippet.value = ""; _addLivePreview.value = ""
        _appState.value = AppState.ADDING
        startSpeechRecognition()
    }

    fun stopAddListening() {
        if (_appState.value != AppState.ADDING) return
        pendingStop = true; _appState.value = AppState.ADD_PROCESSING
        speechRecognizer?.stopListening()
        mainHandler.postDelayed({
            if (_appState.value == AppState.ADD_PROCESSING) finalizeAddStop()
        }, PROCESSING_TIMEOUT_MS)
    }

    private fun finalizeAddStop() {
        if (addPartial.isNotEmpty()) {
            addFinalized = if (addFinalized.isEmpty()) addPartial else "$addFinalized $addPartial"
            addPartial = ""
        }
        speechRecognizer?.destroy(); speechRecognizer = null
        pendingStop = false; isAddMode = false
        _addedSnippet.value = addFinalized; _addLivePreview.value = ""
        _appState.value = AppState.REVIEW
    }

    fun clearAddedSnippet() { _addedSnippet.value = "" }

    fun hearMessage(text: String) {
        if (text.isNotEmpty() && ttsReady) tts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, "hear_message")
    }

    fun hearText() {
        val text = _transcribedText.value
        if (text.isNotEmpty() && ttsReady) tts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, "hear_text")
    }

    fun cancelText() {
        tts?.stop(); _transcribedText.value = ""; _appState.value = AppState.IDLE
    }

    fun onAppBackgrounded() {
        _isAppInForeground.value = false
        when (_appState.value) {
            AppState.LISTENING, AppState.PROCESSING -> { pendingStop = true; speechRecognizer?.stopListening(); finalizeStop() }
            AppState.ADDING, AppState.ADD_PROCESSING -> { pendingStop = true; speechRecognizer?.stopListening(); finalizeAddStop() }
            else -> {}
        }
    }

    fun onAppForegrounded() {
        _isAppInForeground.value = true
        if (!wsClient.isConnected() && serverIp.isNotEmpty()) {
            connect()
        }
    }

    private fun startSpeechRecognition() {
        val app = getApplication<Application>()
        if (!SpeechRecognizer.isRecognitionAvailable(app)) {
            _lastServerMessage.value = "Speech recognition not available"; _appState.value = AppState.IDLE; return
        }
        speechRecognizer?.destroy()
        speechRecognizer = SpeechRecognizer.createSpeechRecognizer(app).apply {
            setRecognitionListener(object : RecognitionListener {
                override fun onReadyForSpeech(p: Bundle?) {}
                override fun onBeginningOfSpeech() {}
                override fun onRmsChanged(rms: Float) {}
                override fun onBufferReceived(buf: ByteArray?) {}
                override fun onEndOfSpeech() {}
                override fun onEvent(t: Int, p: Bundle?) {}
                override fun onError(error: Int) {
                    if (pendingStop) { if (isAddMode) finalizeAddStop() else finalizeStop(); return }
                    if (error == SpeechRecognizer.ERROR_NO_MATCH || error == SpeechRecognizer.ERROR_SPEECH_TIMEOUT) {
                        val activeState = if (isAddMode) AppState.ADDING else AppState.LISTENING
                        if (_appState.value == activeState) startRecognizerIntent()
                    } else { if (isAddMode) finalizeAddStop() else finalizeStop() }
                }
                override fun onResults(results: Bundle?) {
                    results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)?.firstOrNull()?.let { txt ->
                        if (isAddMode) { addFinalized = if (addFinalized.isEmpty()) txt else "$addFinalized $txt"; addPartial = ""; _addLivePreview.value = addFinalized }
                        else { finalizedText = if (finalizedText.isEmpty()) txt else "$finalizedText $txt"; currentPartial = ""; _transcribedText.value = finalizedText }
                    }
                    if (pendingStop) { if (isAddMode) finalizeAddStop() else finalizeStop() }
                    else { val s = if (isAddMode) AppState.ADDING else AppState.LISTENING; if (_appState.value == s) startRecognizerIntent() }
                }
                override fun onPartialResults(pr: Bundle?) {
                    pr?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)?.firstOrNull()?.let { txt ->
                        if (isAddMode) { addPartial = txt; _addLivePreview.value = if (addFinalized.isEmpty()) txt else "$addFinalized $txt" }
                        else { currentPartial = txt; _transcribedText.value = if (finalizedText.isEmpty()) txt else "$finalizedText $txt" }
                    }
                }
            })
        }
        startRecognizerIntent()
    }

    private fun startRecognizerIntent() {
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, "en-US")
            putExtra("android.speech.extra.EXTRA_ADDITIONAL_LANGUAGES", arrayOf<String>())
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
        }
        speechRecognizer?.startListening(intent)
    }

    override fun onCleared() {
        super.onCleared()
        mainHandler.removeCallbacksAndMessages(null)
        speechRecognizer?.destroy()
        tts?.shutdown()
        wsClient.disconnect()
    }
}
