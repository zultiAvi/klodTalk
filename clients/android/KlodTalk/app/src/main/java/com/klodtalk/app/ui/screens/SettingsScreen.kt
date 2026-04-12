package com.klodtalk.app.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import com.klodtalk.app.viewmodel.MainViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    viewModel: MainViewModel,
    onConnected: () -> Unit
) {
    var ip by remember { mutableStateOf(viewModel.serverIp) }
    var port by remember { mutableStateOf(viewModel.serverPort) }
    var protocol by remember { mutableStateOf(viewModel.serverProtocol) }
    var name by remember { mutableStateOf(viewModel.clientName) }
    var password by remember { mutableStateOf(viewModel.clientPassword) }
    var passwordVisible by remember { mutableStateOf(false) }
    var protoExpanded by remember { mutableStateOf(false) }

    val connectionStatus by viewModel.connectionStatus.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("KlodTalk Settings") },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer
                )
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(24.dp)
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            OutlinedTextField(
                value = ip,
                onValueChange = { ip = it },
                label = { Text("Server IP") },
                placeholder = { Text("192.168.1.100") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Uri)
            )

            OutlinedTextField(
                value = port,
                onValueChange = { port = it },
                label = { Text("Port") },
                placeholder = { Text("9000") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number)
            )

            ExposedDropdownMenuBox(
                expanded = protoExpanded,
                onExpandedChange = { protoExpanded = it }
            ) {
                OutlinedTextField(
                    value = if (protocol == "ws") "ws:// (no SSL)" else "wss:// (SSL)",
                    onValueChange = {},
                    readOnly = true,
                    label = { Text("Protocol") },
                    trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = protoExpanded) },
                    modifier = Modifier
                        .fillMaxWidth()
                        .menuAnchor()
                )
                ExposedDropdownMenu(
                    expanded = protoExpanded,
                    onDismissRequest = { protoExpanded = false }
                ) {
                    DropdownMenuItem(
                        text = { Text("ws:// (no SSL)") },
                        onClick = { protocol = "ws"; protoExpanded = false }
                    )
                    DropdownMenuItem(
                        text = { Text("wss:// (SSL)") },
                        onClick = { protocol = "wss"; protoExpanded = false }
                    )
                }
            }

            if (protocol == "wss") {
                Card(
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.tertiaryContainer
                    ),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Text(
                            text = "WSS Certificate Setup",
                            style = MaterialTheme.typography.titleSmall,
                            color = MaterialTheme.colorScheme.onTertiaryContainer
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = "WSS requires installing the server's CA certificate on this device:\n" +
                                "1. Get server.crt from your server admin (via email, USB, or cloud share)\n" +
                                "2. Go to Android Settings → Security → Install a certificate → CA certificate\n" +
                                "3. Select the server.crt file and confirm\n\n" +
                                "This is a one-time setup. On a trusted home network, ws:// works fine without any certificate.",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onTertiaryContainer
                        )
                    }
                }
            }

            OutlinedTextField(
                value = name,
                onValueChange = { name = it },
                label = { Text("Device Name") },
                placeholder = { Text("My Phone") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth()
            )

            OutlinedTextField(
                value = password,
                onValueChange = { password = it },
                label = { Text("Password") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
                visualTransformation = if (passwordVisible) VisualTransformation.None
                    else PasswordVisualTransformation(),
                trailingIcon = {
                    IconButton(onClick = { passwordVisible = !passwordVisible }) {
                        Icon(
                            imageVector = if (passwordVisible) Icons.Filled.Visibility
                                else Icons.Filled.VisibilityOff,
                            contentDescription = if (passwordVisible) "Hide password"
                                else "Show password"
                        )
                    }
                }
            )

            Spacer(modifier = Modifier.height(16.dp))

            Button(
                onClick = {
                    viewModel.saveSettings(ip, port, protocol, name, password)
                    viewModel.connect()
                    onConnected()
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(56.dp),
                enabled = ip.isNotBlank() && port.isNotBlank() && name.isNotBlank()
            ) {
                Text("Connect", style = MaterialTheme.typography.titleMedium)
            }

            if (connectionStatus.isNotEmpty()) {
                Text(
                    text = connectionStatus,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}
