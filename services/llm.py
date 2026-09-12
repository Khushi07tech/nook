import os
import sys
from flask import flash

from config import client

def call_llm(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            messages = [{"role": "user", "content": prompt}],
            model="openai/gpt-oss-20b"
        )    
        return response.choices[0].message.content.strip()
    except Exception as e:
        flash(f"{e}", "error")
        return None

