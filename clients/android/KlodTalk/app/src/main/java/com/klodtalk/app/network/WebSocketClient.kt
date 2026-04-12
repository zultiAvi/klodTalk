package com.klodtalk.app.network

import android.util.Log
import okhttp3.*
import org.json.JSONArray
import org.json.JSONObject
import java.security.MessageDigest
import java.util.concurrent.TimeUnit

data class TeamInfo(val name: String, val description: String)

data class ProjectInfo(val name: String, val description: String, val team: String = "", val availableTeams: List<TeamInfo> = emptyList())

data class SessionInfo(
    val sessionId: String,
    val project: String,
    val branch: String,
    val status: String,
    val createdAt: String,
    val closedAt: String? = null,
    val userName: String? = null,
    val tempId: String? = null,
    val working: Boolean = false,
)

data class HistoryMessage(
    val role: String,
    val content: String,
    val timestamp: String,
    val sessionId: String,
    val model: String = "",
    val team: String = "",
)

interface KlodTalkWebSocketListener {
    fun onStatusChange(status: String)
    fun onProjectsReceived(projects: List<ProjectInfo>)
    fun onSessionsReceived(sessions: List<SessionInfo>, unread: List<String>)
    fun onSessionPreparing(tempId: String, projectName: String)
    fun onSessionCreated(session: SessionInfo)
    fun onSessionClosing(sessionId: String)
    fun onSessionClosed(sessionId: String)
    fun onSessionReopening(sessionId: String)
    fun onSessionReopened(sessionId: String)
    fun onNewMessage(sessionId: String, project: String, role: String, content: String, timestamp: String, model: String = "", team: String = "")
    fun onHistoryReceived(sessions: List<Pair<SessionInfo, List<HistoryMessage>>>, unread: List<String>)
    fun onReadAck(sessionId: String)
    fun onAckReceived(sessionId: String?, content: String)
    fun onErrorReceived(sessionId: String?, message: String)
    fun onSessionWorking(sessionId: String, working: Boolean)
}

class WebSocketClient(private val listener: KlodTalkWebSocketListener) {
    companion object {
        private const val TAG = "WebSocketClient"
    }

    private val client = OkHttpClient.Builder()
        .readTimeout(0, TimeUnit.MILLISECONDS)
        .build()

    private var webSocket: WebSocket? = null
    private var isConnected = false
    private var isConnecting = false

    fun connect(ip: String, port: String, name: String, password: String, protocol: String = "wss") {
        if (isConnected || isConnecting) {
            Log.w(TAG, "connect() called while already connected/connecting, ignoring")
            return
        }
        isConnecting = true
        webSocket?.cancel()
        val proto = if (protocol == "ws") "ws" else "wss"
        val url = "$proto://$ip:$port"
        Log.i(TAG, "Connecting to $url")
        listener.onStatusChange("Connecting to $url...")

        val request = Request.Builder().url(url).build()

        webSocket = client.newWebSocket(request, object : okhttp3.WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                Log.i(TAG, "Connected to $url")
                isConnecting = false
                isConnected = true
                listener.onStatusChange("Connected to $url")
                val hello = JSONObject().apply {
                    put("type", "hello")
                    put("name", name)
                    put("password_hash", sha256(password))
                }
                webSocket.send(hello.toString())
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                Log.d(TAG, "Received: ${text.take(200)}")
                try {
                    val json = JSONObject(text)
                    when (val msgType = json.optString("type")) {
                        MsgType.PROJECTS -> {
                            val arr = json.getJSONArray("projects")
                            val projects = (0 until arr.length()).map { i ->
                                val o = arr.getJSONObject(i)
                                val teamsArr = o.optJSONArray("available_teams")
                                val teams = if (teamsArr != null) (0 until teamsArr.length()).map { j ->
                                    val t = teamsArr.getJSONObject(j)
                                    TeamInfo(t.optString("name", ""), t.optString("description", ""))
                                } else emptyList()
                                ProjectInfo(o.getString("name"), o.optString("description", ""), o.optString("team", ""), teams)
                            }
                            listener.onProjectsReceived(projects)
                        }
                        MsgType.SESSIONS -> {
                            val sessions = parseSessionArray(json.optJSONArray("sessions"))
                            val unread = parseStringArray(json.optJSONArray("unread"))
                            listener.onSessionsReceived(sessions, unread)
                        }
                        MsgType.SESSION_PREPARING -> {
                            listener.onSessionPreparing(
                                tempId = json.optString("temp_id", ""),
                                projectName = json.optString("project", ""),
                            )
                        }
                        MsgType.SESSION_CREATED -> {
                            val session = parseSession(json)
                            listener.onSessionCreated(session)
                        }
                        MsgType.SESSION_CLOSING -> {
                            listener.onSessionClosing(json.optString("session_id", ""))
                        }
                        MsgType.SESSION_CLOSED -> {
                            listener.onSessionClosed(json.getString("session_id"))
                        }
                        MsgType.SESSION_DELETED -> {
                            // Local state already cleaned up in MainViewModel.deleteSession(); nothing to do here.
                        }
                        MsgType.SESSION_REOPENING -> {
                            listener.onSessionReopening(json.optString("session_id", ""))
                        }
                        MsgType.SESSION_REOPENED -> {
                            listener.onSessionReopened(json.getString("session_id"))
                        }
                        MsgType.NEW_MESSAGE -> {
                            listener.onNewMessage(
                                sessionId = json.getString("session_id"),
                                project = json.optString("project", ""),
                                role = json.optString("role", "agent"),
                                content = json.optString("content", ""),
                                timestamp = json.optString("timestamp", ""),
                                model = json.optString("model", ""),
                                team = json.optString("team", ""),
                            )
                        }
                        MsgType.HISTORY -> {
                            val sessionData = mutableListOf<Pair<SessionInfo, List<HistoryMessage>>>()
                            val arr = json.optJSONArray("sessions") ?: JSONArray()
                            for (i in 0 until arr.length()) {
                                val so = arr.getJSONObject(i)
                                val session = parseSession(so)
                                val msgs = mutableListOf<HistoryMessage>()
                                val msgArr = so.optJSONArray("messages") ?: JSONArray()
                                for (j in 0 until msgArr.length()) {
                                    val mo = msgArr.getJSONObject(j)
                                    msgs.add(HistoryMessage(
                                        role = mo.optString("role", "agent"),
                                        content = mo.optString("content", ""),
                                        timestamp = mo.optString("timestamp", ""),
                                        sessionId = mo.optString("session_id", session.sessionId),
                                        model = mo.optString("model", ""),
                                        team = mo.optString("team", ""),
                                    ))
                                }
                                sessionData.add(Pair(session, msgs))
                            }
                            val unread = parseStringArray(json.optJSONArray("unread"))
                            listener.onHistoryReceived(sessionData, unread)
                        }
                        MsgType.READ_ACK -> {
                            listener.onReadAck(json.optString("session_id", ""))
                        }
                        MsgType.ACK -> {
                            listener.onAckReceived(
                                json.optString("session_id").ifEmpty { null },
                                json.optString("content", "Working on it...")
                            )
                        }
                        MsgType.ERROR -> {
                            listener.onErrorReceived(
                                json.optString("session_id").ifEmpty { null },
                                json.optString("message", json.optString("content", "An error occurred"))
                            )
                        }
                        MsgType.SESSION_WORKING -> {
                            listener.onSessionWorking(
                                sessionId = json.optString("session_id", ""),
                                working = json.optBoolean("working", false),
                            )
                        }
                        MsgType.RESPONSE -> {
                            // Legacy compat — treat as new_message with role=agent
                            listener.onNewMessage(
                                sessionId = json.optString("session_id", ""),
                                project = json.optString("project", ""),
                                role = "agent",
                                content = json.optString("content", ""),
                                timestamp = "",
                            )
                        }
                        else -> Log.w(TAG, "Unknown message type: $msgType")
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "Failed to parse message: ${e.message}")
                }
            }

            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                Log.w(TAG, "onClosing: code=$code reason='$reason'")
                webSocket.close(1000, null)
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                Log.w(TAG, "onClosed: code=$code reason='$reason'")
                isConnecting = false
                isConnected = false
                val status = if (code == 4001) "Authentication failed" else "Disconnected"
                listener.onStatusChange(status)
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                Log.e(TAG, "onFailure: ${t.message}", t)
                if (response != null) Log.e(TAG, "onFailure response: $response")
                isConnecting = false
                isConnected = false
                listener.onStatusChange("Connection failed: ${t.message}")
            }
        })
    }

    fun sendNewSession(projectName: String): Boolean = send {
        put("type", "new_session"); put("project", projectName)
    }

    fun sendCloseSession(sessionId: String): Boolean = send {
        put("type", "close_session"); put("session_id", sessionId)
    }

    fun sendDeleteSession(sessionId: String): Boolean = send {
        put("type", "delete_session"); put("session_id", sessionId)
    }

    fun sendReopenSession(sessionId: String): Boolean = send {
        put("type", "reopen_session"); put("session_id", sessionId)
    }

    fun sendText(sessionId: String, content: String, mode: SendMode, team: String = ""): Boolean = send {
        put("type", "text"); put("session_id", sessionId)
        put("content", content); put("mode", mode.value)
        if (team.isNotEmpty()) put("team", team)
    }

    fun sendGetHistory(): Boolean = send { put("type", "get_history") }

    fun sendMarkRead(sessionId: String): Boolean = send {
        put("type", "mark_read"); put("session_id", sessionId)
    }

    fun sendStop(sessionId: String): Boolean = send {
        put("type", "stop"); put("session_id", sessionId)
    }

    fun sendBtw(sessionId: String, content: String): Boolean = send {
        put("type", "btw"); put("session_id", sessionId); put("content", content)
    }

    fun disconnect() {
        webSocket?.close(1000, "Client disconnected")
        webSocket = null
        isConnected = false
        isConnecting = false
    }

    fun isConnected(): Boolean = isConnected

    private fun send(block: JSONObject.() -> Unit): Boolean {
        if (!isConnected || webSocket == null) {
            Log.w(TAG, "Not connected, cannot send")
            listener.onStatusChange("Not connected")
            return false
        }
        return webSocket!!.send(JSONObject().apply(block).toString())
    }

    private fun parseSession(json: JSONObject): SessionInfo = SessionInfo(
        sessionId = json.optString("session_id", ""),
        project = json.optString("project", ""),
        branch = json.optString("branch", ""),
        status = json.optString("status", "active"),
        createdAt = json.optString("created_at", ""),
        closedAt = json.optString("closed_at").ifEmpty { null },
        userName = json.optString("user_name").ifEmpty { null },
        tempId = json.optString("temp_id").ifEmpty { null },
        working = json.optBoolean("working", false),
    )

    private fun parseSessionArray(arr: JSONArray?): List<SessionInfo> {
        if (arr == null) return emptyList()
        return (0 until arr.length()).map { parseSession(arr.getJSONObject(it)) }
    }

    private fun parseStringArray(arr: JSONArray?): List<String> {
        if (arr == null) return emptyList()
        return (0 until arr.length()).map { arr.getString(it) }
    }

    private fun sha256(input: String): String {
        val bytes = MessageDigest.getInstance("SHA-256").digest(input.toByteArray(Charsets.UTF_8))
        return bytes.joinToString("") { "%02x".format(it) }
    }
}
