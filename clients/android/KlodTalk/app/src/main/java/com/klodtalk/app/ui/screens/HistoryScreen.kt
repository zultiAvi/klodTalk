package com.klodtalk.app.ui.screens

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.background
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.VolumeUp
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.ContentCopy
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.TextFieldValue
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.klodtalk.app.network.HistoryMessage
import com.klodtalk.app.network.SendMode
import com.klodtalk.app.network.TeamInfo
import com.klodtalk.app.viewmodel.AppState
import com.klodtalk.app.viewmodel.MainViewModel
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

// Role-based bubble colors
private val COLOR_USER     = Color(0xFFA5D6A7)  // light green
private val COLOR_AGENT    = Color(0xFFBBDEFB)  // light blue
private val COLOR_REVIEW   = Color(0xFFE1BEE7)  // light purple
private val COLOR_PROGRESS = Color(0xFF1A1A1A)  // near-black
private val COLOR_SYSTEM   = Color(0xFF424242)  // dark gray
private val COLOR_PLANNER  = Color(0xFFF8BBD9)  // pink
private val COLOR_CODER    = Color(0xFF80DEEA)  // light teal
private val COLOR_IDEA        = Color(0xFFFFE0B2)  // light orange
private val COLOR_IDEA_REVIEW = Color(0xFFE1BEE7)  // light purple
private val COLOR_FINAL_PLAN    = Color(0xFFF8BBD9)  // pink (like planner)
private val COLOR_IDEA_HISTORY  = Color(0xFF80DEEA)  // light teal (like coder)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HistoryScreen(viewModel: MainViewModel) {
    val currentSessionId by viewModel.currentSessionId.collectAsState()
    val sessions by viewModel.sessions.collectAsState()
    val sessionHistories by viewModel.sessionHistories.collectAsState()
    val appState by viewModel.appState.collectAsState()
    val transcribedText by viewModel.transcribedText.collectAsState()
    val connectionStatus by viewModel.connectionStatus.collectAsState()
    val lastServerMessage by viewModel.lastServerMessage.collectAsState()

    val agents by viewModel.projects.collectAsState()
    val selectedTeamMap by viewModel.selectedTeam.collectAsState()
    val workingSessions by viewModel.workingSessions.collectAsState()

    val session = currentSessionId?.let { sessions[it] }
    val history = currentSessionId?.let { sessionHistories[it] }
    val messages = history?.messages ?: emptyList()
    val isActive = session?.status == "active"

    val projectInfo = agents.find { it.name == session?.project }
    val availableTeams = projectInfo?.availableTeams ?: emptyList()
    val defaultTeam = projectInfo?.team ?: ""
    val currentTeam = currentSessionId?.let { selectedTeamMap[it] } ?: defaultTeam

    var showCloseDialog by remember { mutableStateOf(false) }
    var showStopDialog by remember { mutableStateOf(false) }

    BackHandler(enabled = true) {
        viewModel.goToSessions()
    }

    val listState = rememberLazyListState()

    // Auto-scroll to bottom when messages change
    LaunchedEffect(messages.size) {
        if (messages.isNotEmpty()) {
            listState.animateScrollToItem(messages.size - 1)
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column(horizontalAlignment = Alignment.Start) {
                        Text(
                            text = session?.project ?: "History",
                            style = MaterialTheme.typography.titleMedium,
                            textAlign = TextAlign.Start
                        )
                        if (session != null) {
                            Row(
                                horizontalArrangement = Arrangement.spacedBy(8.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                if (session.branch.isNotEmpty()) {
                                    Text(
                                        text = session.branch,
                                        style = MaterialTheme.typography.labelSmall,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                                        textAlign = TextAlign.Start
                                    )
                                }
                                Text(
                                    text = if (isActive) "● Active" else "○ Closed",
                                    style = MaterialTheme.typography.labelSmall,
                                    color = if (isActive) Color(0xFF4CAF50) else MaterialTheme.colorScheme.onSurfaceVariant,
                                    textAlign = TextAlign.Start
                                )
                            }
                            val createdStr = remember(session.createdAt) {
                                formatHeaderDateTime(session.createdAt)
                            }
                            val lastMsg = messages.lastOrNull { it.role == "user" } ?: messages.lastOrNull()
                            val modifiedStr = remember(lastMsg?.timestamp) {
                                formatHeaderDateTime(lastMsg?.timestamp ?: "")
                            }
                            if (createdStr.isNotEmpty()) {
                                Text(
                                    text = buildString {
                                        append("Created: $createdStr")
                                        if (modifiedStr.isNotEmpty()) append("  ·  Modified: $modifiedStr")
                                    },
                                    style = MaterialTheme.typography.labelSmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f),
                                    textAlign = TextAlign.Start
                                )
                            }
                        }
                    }
                },
                navigationIcon = {
                    IconButton(onClick = { viewModel.goToSessions() }) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    if (isActive) {
                        IconButton(onClick = { showCloseDialog = true }) {
                            Icon(
                                imageVector = Icons.Filled.Close,
                                contentDescription = "Close session",
                                tint = MaterialTheme.colorScheme.error
                            )
                        }
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer
                )
            )
        }
    ) { padding ->
        if (showCloseDialog && currentSessionId != null) {
            AlertDialog(
                onDismissRequest = { showCloseDialog = false },
                title = { Text("Close Session") },
                text = { Text("Close this session?", textAlign = TextAlign.Start) },
                confirmButton = {
                    TextButton(onClick = {
                        viewModel.closeSession(currentSessionId!!)
                        showCloseDialog = false
                        viewModel.goToSessions()
                    }) {
                        Text("Close", color = MaterialTheme.colorScheme.error)
                    }
                },
                dismissButton = {
                    TextButton(onClick = { showCloseDialog = false }) { Text("Cancel") }
                }
            )
        }

        if (showStopDialog) {
            AlertDialog(
                onDismissRequest = { showStopDialog = false },
                title = { Text("Stop Process") },
                text = { Text("Are you sure you want to stop?", textAlign = TextAlign.Start) },
                confirmButton = {
                    TextButton(onClick = {
                        viewModel.sendStop()
                        showStopDialog = false
                    }) {
                        Text("Stop", color = MaterialTheme.colorScheme.error)
                    }
                },
                dismissButton = {
                    TextButton(onClick = { showStopDialog = false }) { Text("Cancel") }
                }
            )
        }

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            // Status/info bar
            val statusMsg = lastServerMessage.ifEmpty { connectionStatus }
            if (statusMsg.isNotEmpty()) {
                Text(
                    text = statusMsg,
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f))
                        .padding(horizontal = 16.dp, vertical = 3.dp),
                    textAlign = TextAlign.Start
                )
            }

            // Session users bar
            if (session != null && session.users.isNotEmpty() && !session.system) {
                SessionUsersBar(
                    users = session.users,
                    ownerName = session.userName ?: "",
                    currentUser = viewModel.getCurrentUserName(),
                    isOwner = viewModel.isSessionOwner(currentSessionId ?: ""),
                    onAddUser = { viewModel.addUserToSession(currentSessionId ?: "", it) },
                    onRemoveUser = { viewModel.removeUserFromSession(currentSessionId ?: "", it) },
                )
            }

            // Messages list
            if (messages.isEmpty()) {
                Box(
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxWidth(),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "No messages yet.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            } else {
                LazyColumn(
                    state = listState,
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxWidth(),
                    contentPadding = PaddingValues(vertical = 8.dp)
                ) {
                    items(messages.size, key = { i -> "${messages[i].timestamp}_${messages[i].role}_$i" }) { i ->
                        val msg = messages[i]
                        MessageBubble(
                            message = msg,
                            onHear = { viewModel.hearMessage(msg.content) }
                        )
                    }
                }
            }

            // Input area (only for active sessions)
            if (isActive) {
                val isWorking = currentSessionId != null && workingSessions.contains(currentSessionId)
                InputArea(
                    appState = appState,
                    text = transcribedText,
                    onTextChange = { viewModel.updateText(it) },
                    onMicClick = {
                        if (appState == AppState.LISTENING) viewModel.stopListening()
                        else if (appState == AppState.IDLE || appState == AppState.REVIEW) viewModel.startListening()
                    },
                    onConfirm = { viewModel.sendWithMode(SendMode.CONFIRM) },
                    onExecute = { viewModel.sendWithMode(SendMode.EXECUTE) },
                    availableTeams = availableTeams,
                    selectedTeam = currentTeam,
                    onTeamSelected = { team ->
                        currentSessionId?.let { viewModel.selectTeam(it, team) }
                    },
                    isWorking = isWorking,
                    onStop = { showStopDialog = true },
                    onBtw = { viewModel.sendBtw() },
                )
            } else if (session != null) {
                Text(
                    text = "This session is closed.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    textAlign = TextAlign.Start
                )
            }
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun SessionUsersBar(
    users: List<String>,
    ownerName: String,
    currentUser: String,
    isOwner: Boolean,
    onAddUser: (String) -> Unit,
    onRemoveUser: (String) -> Unit,
) {
    var addText by remember { mutableStateOf("") }

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f))
            .padding(horizontal = 12.dp, vertical = 6.dp),
        verticalArrangement = Arrangement.spacedBy(6.dp)
    ) {
        FlowRow(
            horizontalArrangement = Arrangement.spacedBy(6.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            users.forEach { user ->
                val isThisOwner = user == ownerName
                val chipColor = if (isThisOwner)
                    MaterialTheme.colorScheme.primary.copy(alpha = 0.15f)
                else
                    MaterialTheme.colorScheme.surfaceVariant

                Surface(
                    shape = RoundedCornerShape(16.dp),
                    color = chipColor,
                    border = if (isThisOwner) BorderStroke(1.dp, Color(0xFF4CAF50)) else null,
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(4.dp)
                    ) {
                        Text(
                            text = user,
                            style = MaterialTheme.typography.labelMedium,
                            color = MaterialTheme.colorScheme.onSurface
                        )
                        if (isThisOwner) {
                            Text(
                                text = "(owner)",
                                style = MaterialTheme.typography.labelSmall,
                                color = Color(0xFF4CAF50)
                            )
                        }
                        if ((isOwner && !isThisOwner) || (!isOwner && user == currentUser)) {
                            IconButton(
                                onClick = { onRemoveUser(user) },
                                modifier = Modifier.size(18.dp)
                            ) {
                                Icon(
                                    Icons.Filled.Close,
                                    contentDescription = "Remove $user",
                                    modifier = Modifier.size(14.dp),
                                    tint = MaterialTheme.colorScheme.error
                                )
                            }
                        }
                    }
                }
            }
        }

        if (isOwner) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                OutlinedTextField(
                    value = addText,
                    onValueChange = { addText = it },
                    modifier = Modifier.weight(1f).height(44.dp),
                    singleLine = true,
                    placeholder = { Text("Type username...", style = MaterialTheme.typography.labelSmall) },
                    textStyle = MaterialTheme.typography.labelSmall,
                    keyboardOptions = KeyboardOptions(imeAction = ImeAction.Done),
                    keyboardActions = KeyboardActions(
                        onDone = {
                            val t = addText.trim()
                            if (t.isNotEmpty()) {
                                onAddUser(t)
                                addText = ""
                            }
                        }
                    ),
                )
                Button(
                    onClick = {
                        val t = addText.trim()
                        if (t.isNotEmpty()) {
                            onAddUser(t)
                            addText = ""
                        }
                    },
                    modifier = Modifier.height(36.dp),
                    contentPadding = PaddingValues(horizontal = 16.dp),
                ) {
                    Text("Add", style = MaterialTheme.typography.labelMedium)
                }
            }
        }
    }
}

@Composable
private fun MessageBubble(
    message: HistoryMessage,
    onHear: () -> Unit
) {
    val clipboardManager = LocalClipboardManager.current
    val role = message.role.lowercase()
    val isWide = role == "progress" || role == "system"

    val bgColor = when (role) {
        "user"     -> COLOR_USER
        "agent"    -> COLOR_AGENT
        "review"   -> COLOR_REVIEW
        "progress" -> COLOR_PROGRESS
        "system"   -> COLOR_SYSTEM
        "planner"  -> COLOR_PLANNER
        "coder"    -> COLOR_CODER
        "idea"        -> COLOR_IDEA
        "idea_review" -> COLOR_IDEA_REVIEW
        "final_plan"    -> COLOR_FINAL_PLAN
        "idea_history"  -> COLOR_IDEA_HISTORY
        else       -> COLOR_SYSTEM
    }

    val TEAM_ROLES = setOf("planner", "coder", "review", "idea", "idea_review", "final_plan", "idea_history")
    val isTeamRole = role in TEAM_ROLES

    val roleLabel = when (role) {
        "user"     -> "You"
        "agent"    -> "Agent"
        "review"   -> "Reviewer"
        "progress" -> "Progress"
        "system"   -> "System"
        "planner"  -> "Planner"
        "coder"    -> "Coder"
        "idea"        -> "Idea"
        "idea_review" -> "Idea Reviewer"
        "final_plan"    -> "Final Plan"
        "idea_history"  -> "Idea History"
        else       -> role.replaceFirstChar { it.uppercase() }
    }

    val teamSuffix = if (role == "agent" && message.team.isNotEmpty()) " [${message.team}]" else ""
    val displayLabel = if (isTeamRole && message.model.isNotEmpty()) {
        "$roleLabel (${message.model})$teamSuffix"
    } else {
        "$roleLabel$teamSuffix"
    }

    // For light-colored bubbles use dark text; for dark bubbles keep light text
    val isDarkBubble = role == "progress" || role == "system"
    val contentColor = if (isDarkBubble) Color.White else Color(0xFF1A1A1A)

    val roleLabelColor = when (role) {
        "user"     -> Color(0xFF2E7D32)  // dark green
        "agent"    -> Color(0xFF1565C0)  // dark blue
        "review"   -> Color(0xFF6A1B9A)  // dark purple
        "progress" -> Color(0xFF90CAF9)  // light (dark bg)
        "system"   -> Color(0xFFAAAAAA)  // gray (dark bg)
        "planner"  -> Color(0xFFAD1457)  // dark pink
        "coder"    -> Color(0xFF00838F)  // dark teal
        "idea"        -> Color(0xFFE65100)  // dark orange
        "idea_review" -> Color(0xFF7B1FA2)  // dark purple
        "final_plan"    -> Color(0xFFAD1457)  // dark pink (like planner)
        "idea_history"  -> Color(0xFF00838F)  // dark teal (like coder)
        else       -> Color(0xFF666666)
    }

    // Indentation mirrors web: user=0, progress/system=small, planner=mid, agent/coder=large, review=largest
    val startPadding = when (role) {
        "user"     -> 0.dp
        "progress" -> 16.dp
        "system"   -> 16.dp
        "planner"  -> 24.dp
        "agent"    -> 32.dp
        "coder"    -> 32.dp
        "review"   -> 40.dp
        "idea"        -> 24.dp
        "idea_review" -> 40.dp
        "final_plan"    -> 24.dp
        "idea_history"  -> 32.dp
        else       -> 16.dp
    }

    val timeText = remember(message.timestamp, isTeamRole) {
        formatMessageTimeForRole(message.timestamp, isTeamRole)
    }

    CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Ltr) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(start = startPadding, end = 8.dp, top = 3.dp, bottom = 3.dp),
            horizontalArrangement = Arrangement.Start
        ) {
            Column(
                modifier = Modifier
                    .then(if (isWide) Modifier.fillMaxWidth() else Modifier.widthIn(max = 300.dp))
                    .background(bgColor, shape = RoundedCornerShape(12.dp))
                    .padding(horizontal = 12.dp, vertical = 8.dp),
                horizontalAlignment = Alignment.Start
            ) {
                // Role label
                Text(
                    text = displayLabel,
                    style = MaterialTheme.typography.labelSmall.copy(
                        fontWeight = FontWeight.Bold
                    ),
                    color = roleLabelColor,
                    textAlign = TextAlign.Start
                )

                Spacer(modifier = Modifier.height(4.dp))

                // Message content
                SelectionContainer {
                    Text(
                        text = message.content,
                        style = if (isWide)
                            MaterialTheme.typography.bodySmall.copy(fontSize = 12.sp)
                        else
                            MaterialTheme.typography.bodyMedium,
                        color = contentColor,
                        textAlign = TextAlign.Start,
                        modifier = Modifier.fillMaxWidth()
                    )
                }

                // Timestamp + hear button row
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = timeText,
                        style = MaterialTheme.typography.labelSmall,
                        color = contentColor.copy(alpha = 0.6f),
                        textAlign = TextAlign.Start
                    )
                    if (role == "agent" || role == "review" || role == "planner" || role == "coder" || role == "idea" || role == "idea_review" || role == "final_plan" || role == "idea_history") {
                        Row {
                            IconButton(
                                onClick = { clipboardManager.setText(AnnotatedString(message.content)) },
                                modifier = Modifier.size(28.dp)
                            ) {
                                Icon(
                                    Icons.Filled.ContentCopy,
                                    contentDescription = "Copy message",
                                    modifier = Modifier.size(16.dp),
                                    tint = Color(0xFF1976D2)
                                )
                            }
                            IconButton(
                                onClick = onHear,
                                modifier = Modifier.size(28.dp)
                            ) {
                                Icon(
                                    Icons.AutoMirrored.Filled.VolumeUp,
                                    contentDescription = "Hear message",
                                    modifier = Modifier.size(16.dp),
                                    tint = Color(0xFF1976D2)
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun InputArea(
    appState: AppState,
    text: String,
    onTextChange: (String) -> Unit,
    onMicClick: () -> Unit,
    onConfirm: () -> Unit,
    onExecute: () -> Unit,
    availableTeams: List<TeamInfo> = emptyList(),
    selectedTeam: String = "",
    onTeamSelected: (String) -> Unit = {},
    isWorking: Boolean = false,
    onStop: () -> Unit = {},
    onBtw: () -> Unit = {},
) {
    val isListening = appState == AppState.LISTENING
    val isProcessing = appState == AppState.PROCESSING || appState == AppState.ADD_PROCESSING
    val isEnabled = !isProcessing

    var textFieldValue by remember { mutableStateOf(TextFieldValue(text)) }
    var teamDropdownExpanded by remember { mutableStateOf(false) }

    LaunchedEffect(text) {
        if (text != textFieldValue.text) {
            textFieldValue = TextFieldValue(text)
        }
    }

    Surface(
        tonalElevation = 4.dp,
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(
            modifier = Modifier
                .padding(12.dp)
                .imePadding(),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Team dropdown (above text field, full width, thin)
            if (availableTeams.isNotEmpty()) {
                ExposedDropdownMenuBox(
                    expanded = teamDropdownExpanded,
                    onExpandedChange = { teamDropdownExpanded = it },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    OutlinedTextField(
                        value = selectedTeam.ifEmpty { "Team" },
                        onValueChange = {},
                        readOnly = true,
                        singleLine = true,
                        textStyle = MaterialTheme.typography.labelSmall,
                        modifier = Modifier
                            .menuAnchor()
                            .height(36.dp)
                            .fillMaxWidth(),
                        trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = teamDropdownExpanded) },
                        colors = ExposedDropdownMenuDefaults.outlinedTextFieldColors(),
                    )
                    ExposedDropdownMenu(
                        expanded = teamDropdownExpanded,
                        onDismissRequest = { teamDropdownExpanded = false }
                    ) {
                        availableTeams.forEach { team ->
                            DropdownMenuItem(
                                text = { Text(team.name, style = MaterialTheme.typography.labelSmall) },
                                onClick = {
                                    onTeamSelected(team.name)
                                    teamDropdownExpanded = false
                                }
                            )
                        }
                    }
                }
            }

            // Text field (LTR forced)
            CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Ltr) {
                OutlinedTextField(
                    value = textFieldValue,
                    onValueChange = {
                        textFieldValue = it
                        onTextChange(it.text)
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(min = 60.dp),
                    enabled = isEnabled && !isListening,
                    placeholder = {
                        Text(
                            if (isListening) "Listening…" else "Type or tap mic…",
                            textAlign = TextAlign.Start
                        )
                    },
                    textStyle = MaterialTheme.typography.bodyMedium.copy(textAlign = TextAlign.Start),
                    shape = RoundedCornerShape(10.dp),
                    maxLines = 5,
                    keyboardOptions = KeyboardOptions(autoCorrect = true)
                )
            }

            // Button row
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Mic button
                IconButton(
                    onClick = onMicClick,
                    enabled = isEnabled,
                    modifier = Modifier
                        .size(48.dp)
                        .background(
                            if (isListening) Color(0xFFF44336) else MaterialTheme.colorScheme.surfaceVariant,
                            shape = RoundedCornerShape(8.dp)
                        )
                ) {
                    if (isListening) {
                        Icon(
                            Icons.Filled.Stop,
                            contentDescription = "Stop listening",
                            tint = Color.White
                        )
                    } else if (isProcessing) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(24.dp),
                            strokeWidth = 2.dp
                        )
                    } else {
                        Icon(
                            Icons.Filled.Mic,
                            contentDescription = "Start listening",
                            tint = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }

                if (isWorking) {
                    // Stop button (replaces Read Back position)
                    Button(
                        onClick = onStop,
                        modifier = Modifier.height(48.dp),
                        enabled = true,
                        colors = ButtonDefaults.buttonColors(
                            containerColor = Color(0xFFC62828)
                        )
                    ) {
                        Text("Stop", style = MaterialTheme.typography.labelLarge)
                    }

                    // BTW button (replaces Start Working position)
                    Button(
                        onClick = onBtw,
                        modifier = Modifier
                            .weight(1f)
                            .height(48.dp),
                        enabled = text.isNotBlank(),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = Color(0xFF1565C0)
                        )
                    ) {
                        Text("BTW", style = MaterialTheme.typography.labelLarge)
                    }
                } else {
                    // Confirm button
                    Button(
                        onClick = onConfirm,
                        modifier = Modifier.height(48.dp),
                        enabled = isEnabled && text.isNotBlank(),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = Color(0xFF1565C0)
                        )
                    ) {
                        Text("Confirm", style = MaterialTheme.typography.labelLarge)
                    }

                    // Execute button
                    Button(
                        onClick = onExecute,
                        modifier = Modifier
                            .weight(1f)
                            .height(48.dp),
                        enabled = isEnabled && text.isNotBlank(),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = Color(0xFF388E3C)
                        )
                    ) {
                        Text("Execute", style = MaterialTheme.typography.labelLarge)
                    }
                }
            }
        }
    }
}

private fun formatMessageTimeForRole(ts: String, isTeamRole: Boolean): String {
    if (ts.isEmpty()) return ""
    return try {
        val fmt = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.US)
        val date: Date = fmt.parse(ts.take(19)) ?: return ts
        if (isTeamRole) {
            SimpleDateFormat("HH:mm:ss", Locale.getDefault()).format(date)
        } else {
            val now = System.currentTimeMillis()
            val isToday = now - date.time < 24 * 60 * 60 * 1000
            if (isToday) SimpleDateFormat("HH:mm", Locale.getDefault()).format(date)
            else SimpleDateFormat("MMM d, HH:mm", Locale.getDefault()).format(date)
        }
    } catch (e: Exception) {
        ts.take(16)
    }
}

private fun formatHeaderDateTime(ts: String): String {
    if (ts.isEmpty()) return ""
    return try {
        val fmt = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.US)
        val date = fmt.parse(ts.take(19)) ?: return ts
        SimpleDateFormat("MMM d, HH:mm", Locale.getDefault()).format(date)
    } catch (e: Exception) { "" }
}
