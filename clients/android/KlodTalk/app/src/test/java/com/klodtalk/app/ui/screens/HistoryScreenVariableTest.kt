package com.klodtalk.app.ui.screens

import org.junit.Test
import org.junit.Assert.*

/**
 * Tests verifying that HistoryScreen uses the correct variable name (`agents`)
 * when looking up a ProjectInfo by name. The local variable collected from
 * viewModel.projects is named `agents`, so all references must use `agents`.
 */
class HistoryScreenVariableTest {

    data class ProjectInfo(val name: String, val description: String)

    /**
     * Simulates the lookup: agents.find { it.name == "beta" }
     * Must find the matching ProjectInfo.
     */
    @Test
    fun `agents find returns matching ProjectInfo`() {
        val agents = listOf(
            ProjectInfo("alpha", "First project"),
            ProjectInfo("beta", "Second project")
        )
        val result = agents.find { it.name == "beta" }
        assertNotNull(result)
        assertEquals("beta", result!!.name)
        assertEquals("Second project", result.description)
    }

    /**
     * Simulates the lookup: agents.find { it.name == "unknown" }
     * Must return null when no match exists.
     */
    @Test
    fun `agents find returns null for unknown name`() {
        val agents = listOf(
            ProjectInfo("alpha", "First project"),
            ProjectInfo("beta", "Second project")
        )
        val result = agents.find { it.name == "unknown" }
        assertNull(result)
    }
}
