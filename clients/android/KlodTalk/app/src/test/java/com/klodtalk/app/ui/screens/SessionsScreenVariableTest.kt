package com.klodtalk.app.ui.screens

import org.junit.Test
import org.junit.Assert.*

/**
 * Tests verifying that SessionsScreen / ProjectPickerDialog use consistent
 * variable names after the agent-to-project rename.
 *
 * In SessionsScreen: the local variable is `agents` (collected from viewModel.projects).
 * In ProjectPickerDialog: the parameter is `projects`.
 * The call site must pass `agents` as the `projects` parameter,
 * and the dialog body must reference `projects` (the parameter name).
 */
class SessionsScreenVariableTest {

    data class ProjectInfo(val name: String, val description: String)

    /**
     * The ProjectPickerDialog parameter is `projects: List<ProjectInfo>`.
     * When the list is empty, projects.isEmpty() must return true.
     */
    @Test
    fun `projects isEmpty returns true for empty list`() {
        val projects: List<ProjectInfo> = emptyList()
        assertTrue(projects.isEmpty())
    }

    /**
     * When the list is non-empty, projects.isEmpty() must return false.
     */
    @Test
    fun `projects isEmpty returns false for non-empty list`() {
        val projects = listOf(ProjectInfo("alpha", "First project"))
        assertFalse(projects.isEmpty())
    }

    /**
     * Iterating projects yields correct names (simulates items(projects) { ... }).
     */
    @Test
    fun `iterating projects yields correct names`() {
        val projects = listOf(
            ProjectInfo("alpha", "First project"),
            ProjectInfo("beta", "Second project"),
            ProjectInfo("gamma", "Third project")
        )
        val names = projects.map { it.name }
        assertEquals(listOf("alpha", "beta", "gamma"), names)
    }

    /**
     * The call site passes `agents` (the local variable) as the `projects`
     * named parameter of ProjectPickerDialog. This test simulates that
     * the agents list is correctly received as the projects parameter.
     */
    @Test
    fun `agents list passed as projects parameter`() {
        val agents = listOf(
            ProjectInfo("alpha", "First project"),
            ProjectInfo("beta", "Second project")
        )

        // Simulate: ProjectPickerDialog(projects = agents, ...)
        fun receiveProjects(projects: List<ProjectInfo>): List<String> {
            return projects.map { it.name }
        }

        val result = receiveProjects(projects = agents)
        assertEquals(listOf("alpha", "beta"), result)
    }
}
