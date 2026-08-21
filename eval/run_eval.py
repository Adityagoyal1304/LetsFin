import csv
import time
import uuid
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from graph import build_graph
from langgraph.types import Command
from llm_config import get_critic_llm

def judge_answer(question, expected, actual):
    critic = get_critic_llm()
    prompt = f"""
    You are an impartial judge. Compare the expected answer to the actual answer for the given question.
    Question: {question}
    Expected: {expected}
    Actual: {actual}
    
    Does the actual answer contain the expected information and is it factually consistent?
    Return ONLY 'CORRECT' or 'INCORRECT'.
    """
    response = critic.invoke(prompt)
    return "CORRECT" in response.content.upper()

def main():
    graph = build_graph()
    results = []
    
    with open("eval/questions.csv", "r") as f:
        reader = csv.DictReader(f)
        questions = list(reader)
        
    total_latency = 0
    correct_count = 0
    rejection_count = 0
    
    print(f"Starting evaluation of {len(questions)} questions...\n")
    
    for row in questions:
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        
        initial_state = {
            "ticker": row["ticker"],
            "question": row["question"],
            "messages": [{"role": "user", "content": row["question"]}],
            "evidence": [],
            "visited": [],
            "valuation": None,
            "draft": None,
            "critique": None,
            "revision_count": 0,
            "approved": False,
        }
        
        start_time = time.time()
        
        # Phase 1: Run to interrupt
        try:
            for _ in graph.stream(initial_state, config, stream_mode="updates"):
                pass
        except Exception as e:
            if "interrupt" not in type(e).__name__.lower():
                raise
                
        # Phase 2: Resume (approve)
        try:
            for _ in graph.stream(Command(resume="approve"), config, stream_mode="updates"):
                pass
        except Exception as e:
            if "interrupt" not in type(e).__name__.lower():
                raise
                
        end_time = time.time()
        latency = end_time - start_time
        
        snap = graph.get_state(config)
        state_values = snap.values
        
        memo = state_values.get("draft", "")
        revision_count = state_values.get("revision_count", 0)
        
        is_correct = judge_answer(row["question"], row["expected_answer"], memo)
        
        if is_correct:
            correct_count += 1
        if revision_count > 0:
            rejection_count += 1
            
        total_latency += latency
        
        results.append({
            "id": row["id"],
            "ticker": row["ticker"],
            "question": row["question"],
            "expected": row["expected_answer"],
            "correct": is_correct,
            "rejected_first_draft": revision_count > 0,
            "latency": latency
        })
        
        print(f"[{row['id']}] {row['ticker']} - Correct: {is_correct} | Revisions: {revision_count} | Latency: {latency:.1f}s")
        
    # Write results
    with open("eval/results.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "ticker", "question", "expected", "correct", "rejected_first_draft", "latency"])
        writer.writeheader()
        writer.writerows(results)
        
    num_questions = len(questions)
    print("\n" + "="*40)
    print("EVALUATION SUMMARY")
    print("="*40)
    print(f"Accuracy:                   {correct_count / num_questions * 100:.1f}%")
    print(f"First-draft rejection rate: {rejection_count / num_questions * 100:.1f}%")
    print(f"Mean latency:               {total_latency / num_questions:.1f}s")
    print("\nReminder: Check LangSmith for cost-per-run metrics!")
    print("="*40)

if __name__ == "__main__":
    main()
