package com.klodtalk.app.network

object MsgType {
    const val PROJECTS = "projects"
    const val SESSIONS = "sessions"
    const val SESSION_PREPARING = "session_preparing"
    const val SESSION_CREATED = "session_created"
    const val SESSION_CLOSING = "session_closing"
    const val SESSION_CLOSED = "session_closed"
    const val SESSION_DELETED = "session_deleted"
    const val SESSION_REOPENING = "session_reopening"
    const val SESSION_REOPENED = "session_reopened"
    const val NEW_MESSAGE = "new_message"
    const val HISTORY = "history"
    const val READ_ACK = "read_ack"
    const val RESPONSE = "response"
    const val REVIEW = "review"
    const val ACK = "ack"
    const val ERROR = "error"
    const val PROGRESS = "progress"
    const val SESSION_WORKING = "session_working"
    const val SESSION_USER_ADDED = "session_user_added"
    const val SESSION_USER_REMOVED = "session_user_removed"
}
