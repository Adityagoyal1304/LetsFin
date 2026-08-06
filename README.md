# Equity Research Agent

A multi-agent equity research system built with LangGraph and LangChain. A graph of specialized nodes gathers live financial data via tools, drafts a research memo, runs a critic pass to reject any number that cannot be traced to a tool output, pauses for human approval via an interrupt, and streams the final report to a React UI through an Express/MongoDB API layer.
