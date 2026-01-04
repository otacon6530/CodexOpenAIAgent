
from .api import OpenAIClient
from .history import ConversationHistory
from .config import load_config
from .skills import list_skills, save_skill, load_skill

import sys


def main():
    config = load_config()
    client = OpenAIClient(config)
    history = ConversationHistory()
    CHAIN_LIMIT = config.get("chain_limit", 25)
    debug_metrics = config.get("debug_metrics", False)
    print("llm-cli (type 'exit' to quit)")
    import time
    while True:
        try:
            user_input = input("You: ").strip()
            if user_input.lower() in ("exit", "quit"): break
            if not user_input: continue

            # Debug toggle command
            if user_input.lower() == '!debug':
                debug_metrics = not debug_metrics
                print(f"Debug metrics {'enabled' if debug_metrics else 'disabled'}.")
                continue
            # Skill commands
            if user_input.lower() == '!skills':
                skills = list_skills()
                if not skills:
                    print("No skills found.")
                else:
                    for s in skills:
                        print(f"- {s['name']}: {s.get('description','')}")
                continue
            if user_input.lower().startswith('!run '):
                skill_name = user_input[5:].strip()
                skill = load_skill(skill_name)
                if not skill:
                    print(f"Skill '{skill_name}' not found.")
                    continue
                print(f"Running skill: {skill['name']}")
                for i, step in enumerate(skill['steps']):
                    print(f"[Skill Step {i+1}] {step}")
                    history.add_user_message(f"Skill step: {step}")
                    step_response = ""
                    for chunk in client.stream_chat(history.get_messages()):
                        step_response += chunk
                    print(step_response.strip())
                    history.add_assistant_message(step_response)
                print("[Skill complete. Returning to user input.]")
                continue
            if user_input.lower().startswith('!save_skill '):
                # Usage: !save_skill name|description|step1;step2;step3
                try:
                    _, rest = user_input.split(' ', 1)
                    name, desc, steps = rest.split('|', 2)
                    steps_list = [s.strip() for s in steps.split(';') if s.strip()]
                    save_skill(name.strip(), desc.strip(), steps_list)
                    print(f"Skill '{name.strip()}' saved.")
                except Exception as e:
                    print(f"Failed to save skill: {e}")
                continue

            history.add_user_message(user_input)
            # Step 1: Ask LLM to plan
            plan_prompt = (
                "Given the user's request, break it down into a numbered list of concrete steps (tools or actions) to achieve the goal. "
                f"Only plan up to {CHAIN_LIMIT} steps. Respond with the plan as a numbered list."
            )
            history.add_user_message(plan_prompt)
            print("Assistant is thinking (planning)...", flush=True)
            t0 = time.time()
            plan_response = ""
            for chunk in client.stream_chat(history.get_messages()):
                plan_response += chunk
            t1 = time.time()
            print(plan_response.strip())
            history.add_assistant_message(plan_response)

            # Step 2: Parse plan steps
            import re
            steps = re.findall(r'\d+\.\s*(.*)', plan_response)
            if not steps:
                print("No plan steps found. Proceeding with normal chat.")
                continue
            # Step 3: Execute each step up to chain limit
            chain_steps = 0
            t_chain_start = time.time()
            for i, step in enumerate(steps[:CHAIN_LIMIT]):
                print(f"\n[Step {i+1}] {step}")
                # Feed step as a new user message to LLM to get tool call or answer
                history.add_user_message(f"Step: {step}")
                print("Assistant is thinking (executing step)...", flush=True)
                step_response = ""
                for chunk in client.stream_chat(history.get_messages()):
                    step_response += chunk
                print(step_response.strip())
                history.add_assistant_message(step_response)
                chain_steps += 1
            t_chain_end = time.time()
            if debug_metrics:
                print(f"[DEBUG] Planning time: {t1-t0:.2f}s | Chain steps: {chain_steps} | Chain time: {t_chain_end-t_chain_start:.2f}s")
            print("\n[Chain complete. Returning to user input.]")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

if __name__ == "__main__":
    main()
