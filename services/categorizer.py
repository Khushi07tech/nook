import json
from flask import flash
from services.llm import call_llm

def categorize_idea(content: str) -> dict:
    # TODO: Build a prompt string using `content` asking for a category (e.g. Project, Thought, Task, Learning, Personal, General) and 1-3 tags
    # TODO: Explicitly instruct the model to return raw JSON only (no markdown, backticks, or extra text)
    prompt = f"""
                Analyze the following raw idea: "{content}"

                Task 1: Assign exactly ONE primary category.
                Determine the core intent/theme of the entry based on these priorities. Remember to categorize based only on the PRIMARY subject even if secondary subjects are present:
                - "Personal / Life": Entries primarily about personal experiences, daily updates, family, health, mood, or lifestyle
                - "Project": Entries explicitly about building, coding, designing, or technical planning for a specific software/hardware product or tool.
                - "Academic": Study notes, coursework, exams, or educational topics.
                - "Task / Todo": Actionable items or errands to execute.
                - "Thought / Reflection": Deep observations, philosophies, or shower thoughts.
                - "Yap / Crisis": My random hyped up yap over work, life, or anything.
                - "General": Use only as a last resort if no other category fits.

                Task 2: Generate 2 to 3 specific tags.
                - Use concise, lowercase terms.
                - Focus on specific sub-topics, tools, people, or underlying concepts rather than broad generic words (e.g., prefer "guest-visit", "schedule-delay", "time-management" over broad tags like "life" or "stuff").

                Output Rules:
                Return ONLY a valid, raw JSON object with no markdown formatting, backticks, or extra text.

                Example format: {{\"category\": \"Life\", \"tags\": [\"guest-visit\", \"schedule-delay\", \"time-management\"]}}
            """

    # TODO: Call `call_llm(prompt)` and store the raw text response in a variable
    raw_response = call_llm(prompt)

    if raw_response:
        try:    
            response = raw_response.strip().replace("```json", "").replace("```", "")
            response = json.loads(response)
            return response 
        except Exception as e:
            flash(f"{e}", "error")
            return None
    else:
        return None
        