package com.klodtalk.app.ui.screens

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.spring
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectHorizontalDragGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import com.klodtalk.app.network.ProjectInfo
import com.klodtalk.app.network.HistoryMessage
import com.klodtalk.app.viewmodel.SessionHistory
import com.klodtalk.app.network.SessionInfo
import com.klodtalk.app.viewmodel.MainViewModel
import com.klodtalk.app.viewmodel.PreparingSession
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import kotlin.math.abs
import kotlin.math.roundToInt
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SessionsScreen(viewModel: MainViewModel) {
    val sessions by viewModel.sessions.collectAsState()
    val sessionHistories by viewModel.sessionHistories.collectAsState()
    val unreadSessions by viewModel.unreadSessions.collectAsState()
    val agents by viewModel.projects.collectAsState()
    val connectionStatus by viewModel.connectionStatus.collectAsState()
    val preparingSessions by viewModel.preparingSessions.collectAsState()
    val justCreatedSessions by viewModel.justCreatedSessions.collectAsState()

    var showProjectPicker by remember { mutableStateOf(false) }
    var sessionToClose by remember { mutableStateOf<String?>(null) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Sessions") },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer
                ),
                actions = {
                    IconButton(onClick = { viewModel.goToSettings() }) {
                        Icon(Icons.Filled.Settings, contentDescription = "Settings")
                    }
                }
            )
        },
        floatingActionButton = {
            FloatingActionButton(
                onClick = { showProjectPicker = true },
                containerColor = MaterialTheme.colorScheme.primary
            ) {
                Icon(Icons.Filled.Add, contentDescription = "New session")
            }
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            // Connection status bar
            if (connectionStatus.isNotEmpty()) {
                Text(
                    text = connectionStatus,
                    style = MaterialTheme.typography.labelSmall,
                    color = if (connectionStatus.startsWith("Connected"))
                        Color(0xFF4CAF50) else MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f))
                        .padding(horizontal = 16.dp, vertical = 4.dp),
                    textAlign = TextAlign.Start
                )
            }

            val sortedSessions = remember(sessions, sessionHistories) {
                sessions.values.sortedWith(
                    compareBy<SessionInfo> { it.status == "closed" }
                        .thenByDescending {
                            val msgs = sessionHistories[it.sessionId]?.messages
                            if (!msgs.isNullOrEmpty()) msgs.last().timestamp else (it.createdAt)
                        }
                )
            }

            if (sortedSessions.isEmpty() && preparingSessions.isEmpty()) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "No sessions yet.\nTap + to start one.",
                        style = MaterialTheme.typography.bodyLarge,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        textAlign = TextAlign.Center
                    )
                }
            } else {
                LazyColumn(modifier = Modifier.fillMaxSize()) {
                    // Preparing sessions at top
                    items(preparingSessions, key = { "preparing_${it.tempId}" }) { preparing ->
                        PreparingSessionItem(preparing = preparing)
                        HorizontalDivider(color = MaterialTheme.colorScheme.surfaceVariant)
                    }
                    items(sortedSessions, key = { it.sessionId }) { session ->
                        val preview = computePreview(sessionHistories[session.sessionId]?.messages)
                        SwipeableSessionItem(
                            session = session,
                            onDelete = { viewModel.deleteSession(session.sessionId) }
                        ) {
                            SessionItem(
                                session = session,
                                isUnread = unreadSessions.contains(session.sessionId),
                                isJustCreated = justCreatedSessions.contains(session.sessionId),
                                preview = preview,
                                onClick = { viewModel.navigateToSession(session.sessionId) },
                                onClose = { sessionToClose = session.sessionId },
                                onReopen = { viewModel.reopenSession(session.sessionId) },
                                onDelete = { viewModel.deleteSession(session.sessionId) }
                            )
                        }
                        HorizontalDivider(color = MaterialTheme.colorScheme.surfaceVariant)
                    }
                }
            }
        }
    }

    // Agent picker dialog
    if (showProjectPicker) {
        ProjectPickerDialog(
            projects = agents,
            onProjectSelected = { agentName ->
                showProjectPicker = false
                viewModel.createSession(agentName)
            },
            onDismiss = { showProjectPicker = false }
        )
    }

    // Confirm close session dialog
    sessionToClose?.let { sid ->
        AlertDialog(
            onDismissRequest = { sessionToClose = null },
            title = { Text("Close Session") },
            text = {
                val session = sessions[sid]
                Text(
                    text = "Close session \"${session?.project ?: sid}\"?",
                    textAlign = TextAlign.Start
                )
            },
            confirmButton = {
                TextButton(onClick = {
                    viewModel.closeSession(sid)
                    sessionToClose = null
                }) {
                    Text("Close", color = MaterialTheme.colorScheme.error)
                }
            },
            dismissButton = {
                TextButton(onClick = { sessionToClose = null }) {
                    Text("Cancel")
                }
            }
        )
    }
}

@Composable
private fun SwipeableSessionItem(
    session: SessionInfo,
    onDelete: () -> Unit,
    content: @Composable () -> Unit
) {
    if (session.status != "closed") {
        content()
        return
    }

    val screenWidthDp = LocalConfiguration.current.screenWidthDp.dp
    val screenWidthPx = with(LocalDensity.current) { screenWidthDp.toPx() }
    val threshold = screenWidthPx * 0.5f
    val isRtl = LocalLayoutDirection.current == LayoutDirection.Rtl

    val offsetX = remember { Animatable(0f) }
    var dismissed by remember { mutableStateOf(false) }
    val coroutineScope = rememberCoroutineScope()

    if (dismissed) return

    val absOffset = abs(offsetX.value)
    val bgColor = if (absOffset >= threshold) Color(0xFFD32F2F) else Color(0xFF4CAF50)

    Box(
        modifier = Modifier
            .fillMaxWidth()
            .pointerInput(Unit) {
                detectHorizontalDragGestures(
                    onDragEnd = {
                        if (abs(offsetX.value) >= threshold) {
                            dismissed = true
                            onDelete()
                        } else {
                            coroutineScope.launch {
                                offsetX.animateTo(0f, animationSpec = spring())
                            }
                        }
                    },
                    onDragCancel = {
                        coroutineScope.launch {
                            offsetX.animateTo(0f, animationSpec = spring())
                        }
                    },
                    onHorizontalDrag = { change, dragAmount ->
                        change.consume()
                        coroutineScope.launch {
                            val adjustedDrag = if (isRtl) -dragAmount else dragAmount
                            offsetX.snapTo(offsetX.value + adjustedDrag)
                        }
                    }
                )
            }
    ) {
        // Background layer
        Box(
            modifier = Modifier
                .matchParentSize()
                .background(bgColor),
            contentAlignment = if (offsetX.value > 0) Alignment.CenterStart else Alignment.CenterEnd
        ) {
            Icon(
                Icons.Filled.Delete,
                contentDescription = "Delete session",
                tint = Color.White,
                modifier = Modifier.padding(horizontal = 20.dp)
            )
        }
        // Foreground: the session item, translated
        Box(modifier = Modifier.offset { IntOffset(offsetX.value.roundToInt(), 0) }) {
            content()
        }
    }
}

@Composable
private fun PreparingSessionItem(preparing: PreparingSession) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(MaterialTheme.colorScheme.background)
            .padding(horizontal = 16.dp, vertical = 14.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        CircularProgressIndicator(
            modifier = Modifier.size(10.dp),
            strokeWidth = 1.5.dp,
            color = Color(0xFF888888),
        )
        Column(
            modifier = Modifier.weight(1f),
            horizontalAlignment = Alignment.Start
        ) {
            Text(
                text = preparing.projectName,
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f),
                textAlign = TextAlign.Start
            )
            Text(
                text = "Preparing…",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.5f),
                textAlign = TextAlign.Start
            )
        }
    }
}

@Composable
private fun SessionItem(
    session: SessionInfo,
    isUnread: Boolean,
    isJustCreated: Boolean = false,
    preview: String = "",
    onClick: () -> Unit,
    onClose: () -> Unit,
    onReopen: () -> Unit = {},
    onDelete: () -> Unit = {}
) {
    val isClosing = session.status == "closing"
    val isReopening = session.status == "reopening"
    val bgColor = if (isUnread)
        MaterialTheme.colorScheme.surface.copy(alpha = 0.85f)
    else
        MaterialTheme.colorScheme.background

    // Glow animation for just-created sessions
    val glowAlpha = remember(session.sessionId) { Animatable(0f) }
    LaunchedEffect(isJustCreated) {
        if (isJustCreated) {
            glowAlpha.snapTo(1f)
            glowAlpha.animateTo(0f, animationSpec = tween(durationMillis = 2500))
        }
    }

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(bgColor)
            .clickable(enabled = !isClosing && !isReopening, onClick = onClick)
            .padding(horizontal = 16.dp, vertical = 14.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        // Status dot / closing spinner
        Box(
            modifier = Modifier.size(20.dp),
            contentAlignment = Alignment.Center
        ) {
            if (isClosing || isReopening) {
                CircularProgressIndicator(
                    modifier = Modifier.size(10.dp),
                    strokeWidth = 1.5.dp,
                    color = if (isReopening) Color(0xFF2196F3) else Color(0xFF888888),
                )
            } else {
                val dotColor = when {
                    isJustCreated -> Color(0xFF00FF88)
                    isUnread -> Color(0xFFF44336)
                    session.status == "active" -> Color(0xFF4CAF50)
                    else -> Color(0xFF555555)
                }
                // Glow ring
                if (glowAlpha.value > 0f) {
                    Box(
                        modifier = Modifier
                            .requiredSize(20.dp)
                            .clip(CircleShape)
                            .background(Color(0xFF00FF88).copy(alpha = glowAlpha.value * 0.45f))
                    )
                }
                Box(
                    modifier = Modifier
                        .size(10.dp)
                        .clip(CircleShape)
                        .background(dotColor)
                )
            }
        }

        // Session info
        Column(
            modifier = Modifier.weight(1f),
            horizontalAlignment = Alignment.Start
        ) {
            Text(
                text = session.project,
                style = MaterialTheme.typography.bodyLarge.copy(
                    fontWeight = if (isUnread) FontWeight.Bold else FontWeight.Normal
                ),
                color = if (isClosing) MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f)
                        else if (isUnread) Color.White
                        else MaterialTheme.colorScheme.onSurface,
                textAlign = TextAlign.Start
            )
            if (session.branch.isNotEmpty()) {
                Text(
                    text = session.branch,
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    textAlign = TextAlign.Start
                )
            }
            if (preview.isNotEmpty()) {
                Text(
                    text = preview,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f),
                    maxLines = 1,
                    textAlign = TextAlign.Start
                )
            }
            val timeText = remember(session.createdAt) {
                formatTimestamp(session.createdAt)
            }
            Text(
                text = if (isClosing) "Closing…"
                       else if (isReopening) "Reopening…"
                       else "${if (isJustCreated) "created" else session.status} · $timeText",
                style = MaterialTheme.typography.labelSmall,
                color = if (isJustCreated) Color(0xFF00FF88).copy(alpha = 0.8f)
                        else MaterialTheme.colorScheme.onSurfaceVariant,
                textAlign = TextAlign.Start
            )
        }

        // Close button (only for active sessions)
        if (session.status == "active") {
            IconButton(
                onClick = onClose,
                modifier = Modifier.size(32.dp)
            ) {
                Icon(
                    Icons.Filled.Close,
                    contentDescription = "Close session",
                    modifier = Modifier.size(18.dp),
                    tint = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }

        // Reopen + Delete buttons (only for closed sessions)
        if (session.status == "closed") {
            IconButton(
                onClick = onReopen,
                modifier = Modifier.size(32.dp)
            ) {
                Icon(
                    Icons.Filled.Refresh,
                    contentDescription = "Reopen session",
                    modifier = Modifier.size(18.dp),
                    tint = Color(0xFF2196F3)
                )
            }
            IconButton(
                onClick = onDelete,
                modifier = Modifier.size(32.dp)
            ) {
                Icon(
                    Icons.Filled.Delete,
                    contentDescription = "Delete session",
                    modifier = Modifier.size(18.dp),
                    tint = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}

@Composable
private fun ProjectPickerDialog(
    projects: List<ProjectInfo>,
    onProjectSelected: (String) -> Unit,
    onDismiss: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Choose a Project") },
        text = {
            if (projects.isEmpty()) {
                Text(
                    text = "No projects available",
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    textAlign = TextAlign.Start
                )
            } else {
                LazyColumn {
                    items(projects) { project ->
                        Surface(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable { onProjectSelected(project.name) }
                                .padding(vertical = 4.dp),
                            shape = RoundedCornerShape(8.dp),
                            color = MaterialTheme.colorScheme.surfaceVariant
                        ) {
                            Column(
                                modifier = Modifier.padding(12.dp),
                                horizontalAlignment = Alignment.Start
                            ) {
                                Text(
                                    text = project.name,
                                    style = MaterialTheme.typography.bodyLarge.copy(
                                        fontWeight = FontWeight.SemiBold
                                    ),
                                    textAlign = TextAlign.Start
                                )
                                if (project.description.isNotEmpty()) {
                                    Text(
                                        text = project.description,
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                                        textAlign = TextAlign.Start
                                    )
                                }
                            }
                        }
                    }
                }
            }
        },
        confirmButton = {},
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Cancel") }
        }
    )
}

private fun computePreview(messages: List<HistoryMessage>?): String {
    if (messages.isNullOrEmpty()) return ""
    val teamCompletionRegex = Regex("^Team .+ completed with exit code \\d+")
    val lastMsg = messages.lastOrNull { !teamCompletionRegex.matches(it.content) } ?: return ""
    var text = lastMsg.content
    val summaryMatch = Regex("^## Team\\n[\\s\\S]*?\\n## Summary\\n([\\s\\S]*)").find(text)
    if (summaryMatch != null) text = summaryMatch.groupValues[1].trim()
    return if (text.length > 60) text.take(60) + "\u2026" else text
}

private fun formatTimestamp(ts: String): String {
    if (ts.isEmpty()) return ""
    return try {
        val fmt = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.US)
        val date = fmt.parse(ts.take(19)) ?: return ts
        SimpleDateFormat("MMM d, HH:mm", Locale.getDefault()).format(date)
    } catch (e: Exception) {
        ts.take(16)
    }
}
