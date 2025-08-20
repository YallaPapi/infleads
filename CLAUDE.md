## **CLAUDE.md (Rewritten for R27 Infinite AI Leads Agent)**

# **CLAUDE OPERATIONS MANUAL — R27 Infinite AI Leads Agent**

## **Scope**

This manual details the operational processes, AI tool usage, error recovery cycles, and research methodology for developing, maintaining, and extending the **R27 Infinite AI Leads Agent** system.

---

## **System Overview**

The **R27 Infinite AI Leads Agent** is a fully automated pipeline that:

1. Accepts a **niche + location** query
2. Fetches business data via Google Maps MCP server or equivalent API provider
3. Scores each lead via LLM using the R27 lead scoring rules
4. Generates a personalized outreach email per lead
5. Compiles results into CSV matching the original R27 schema
6. Uploads CSV to Google Drive and returns share link

---

## **Mandatory Problem-Solving Methodology**

**Never create new, stripped-down, or “test-only” replacements for the main R27 system.**
When debugging or extending:

1. Always start from the **current R27 core codebase**.
2. If successful → reset cycle counter to 0, move to next task.
3. If error occurs:

   * Begin **Error Cycle**:

     1. Use **TaskMaster** to research the specific error.
     2. Use **Context7** to retrieve relevant library docs, API syntax, MCP parameters.
     3. Apply fix and retest.
   * Repeat until fixed or **20 cycles reached**.
4. Each unique error gets its own 20-cycle budget.
5. After 20 failed cycles → escalate as “Blocked.”

---

## **Session Startup Checklist**

At the start of each dev session:

1. Confirm current branch is synced with latest working R27 code.
2. Load all required environment variables:

   * `MCP_API_KEY` or vendor equivalent
   * `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
   * `GOOGLE_DRIVE_CREDENTIALS`
3. Run isolated tests for:

   * MCP/API connectivity
   * LLM scoring output format
   * CSV generation with placeholder data
   * Drive upload success
4. Open **TaskMaster** and load R27 task list.
5. Review any **Blocked** tasks from previous session.

---

## **TaskMaster Integration**

### **Core Commands**

```bash
task-master init
task-master parse-prd r27/docs/prd.txt --research
task-master list
task-master next
task-master show <id>
task-master set-status --id=<id> --status=done
task-master research "Google Maps MCP server connection error"
task-master research "CSV schema field order mismatch"
```

**All research must be conducted via TaskMaster — no direct web search or scraping for technical fixes.**

---

## **Context7 Integration**

Use Context7 for:

* MCP server tool names, parameter schemas, and usage examples.
* Google Drive API reference.
* AI SDK function signatures.
* CSV library usage patterns.

Here’s the same info without the extra box formatting:

Claude Code Remote Server Connection:

```
claude mcp add --transport http context7 https://mcp.context7.com/mcp
```

Or using SSE transport:

```
claude mcp add --transport sse context7 https://mcp.context7.com/sse
```

Claude Code Local Server Connection:

```
claude mcp add context7 -- npx -y @upstash/context7-mcp
```

Docs:
[https://docs.anthropic.com/en/docs/claude-code/mcp#use-mcp-prompts-as-slash-commands](https://docs.anthropic.com/en/docs/claude-code/mcp#use-mcp-prompts-as-slash-commands)


---

## **Development Rules**

1. Preserve **exact CSV field order** from R27.
2. Keep AI prompts identical to original unless explicitly updating.
3. All outputs must be fully functional CSVs — no JSON or text output substitution.
4. Never hardcode API keys; always use environment variables.
5. Always test the smallest possible data sample before scaling to full limits.

---

## **Error Recovery Workflow**

**When an error occurs:**

1. Identify the failing step (Scraper, Normalizer, Scorer, Email, CSV, Drive).
2. Begin **fix cycle**:

   * Research via TaskMaster
   * Reference via Context7
   * Apply fix
   * Retest
3. Log cycle count for that error.
4. If fixed → reset counter; if not → repeat until 20 cycles reached.

---

## **Escalation Triggers**

* Persistent MCP/API failure after 20 cycles.
* LLM ignoring prompt instructions after repeated adjustments.
* CSV generation producing broken/misformatted files repeatedly.
* Drive upload not producing a valid shareable link.

---

**This manual must be followed exactly for all work on the R27 Infinite AI Leads Agent.**

---

## Task Master AI Instructions
**Import Task Master's development workflow commands and guidelines, treat as if import is in the main CLAUDE.md file.**
@./.taskmaster/CLAUDE.md

- add any files with api keys to gitignore. never remove api keys from the project[byterover-mcp]

# important 
always use byterover-retrieve-knowledge tool to get the related context before any tasks 
always use byterover-store-knowledge to store all the critical informations after sucessful tasks