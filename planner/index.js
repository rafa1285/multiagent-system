// Planner Agent
//
// Purpose: Receives a high-level task description from n8n via HTTP and
// breaks it down into a structured plan (list of sub-tasks) that the
// other agents (developer, reviewer, deployer) will execute in sequence.
//
// Responsibilities:
//   - Parse the incoming task payload
//   - Produce an ordered execution plan
//   - Return the plan as a structured response to n8n
