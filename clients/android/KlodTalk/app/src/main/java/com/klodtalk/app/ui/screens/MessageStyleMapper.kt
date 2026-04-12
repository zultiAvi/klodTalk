package com.klodtalk.app.ui.screens

import android.util.Log
import androidx.compose.ui.graphics.Color
import com.klodtalk.app.network.MsgType

// TODO: move reviewOrange to theme when dark-mode support is added (current value is light-mode only)
private val reviewOrange = Color(0xFFE65100)

private const val REVIEW_BG_ALPHA = 0.06f
private const val REVIEW_BORDER_ALPHA = 0.25f

/**
 * Resolved display style for a message card.
 *
 * [containerColor] — null means use the surface default from MaterialTheme.
 * [borderColor]    — null means no border.
 * [accentLabelColor] — non-null means show [agentLabel] in this color above the message.
 * [agentLabel]     — non-null only when [accentLabelColor] is non-null (i.e. for REVIEW messages).
 */
internal data class IncomingStyle(
    val containerColor: Color?,
    val borderColor: Color?,
    val accentLabelColor: Color?,
    val agentLabel: String?
)

internal fun styleForMessage(msgType: String, projectName: String): IncomingStyle = when (msgType) {
    MsgType.REVIEW -> IncomingStyle(
        containerColor = reviewOrange.copy(alpha = REVIEW_BG_ALPHA),
        borderColor = reviewOrange.copy(alpha = REVIEW_BORDER_ALPHA),
        accentLabelColor = reviewOrange,
        agentLabel = "$projectName (review)"
    )
    MsgType.RESPONSE -> IncomingStyle(null, null, null, null)
    else -> {
        // Unknown type: displayed with default style rather than silently dropped.
        Log.w("MessageStyleMapper", "Unknown msgType '$msgType' — displayed with default style")
        IncomingStyle(null, null, null, null)
    }
}
