import json
from typing import List, Dict

ACTION_PRIORITY = {
    "block": 4,
    "escalate": 3,
    "sanitize": 2,
    "allow": 1
}

SANITIZED_MESSAGE = (
    "This response cannot be shown. Please consult a qualified professional."
)


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_action(actions: List[str]) -> str:
    return max(actions, key=lambda a: ACTION_PRIORITY.get(a, 0))


def evaluate_input(item: Dict, policies: List[Dict], default_action: str) -> Dict:
    matched_policies = []
    candidate_actions = []
    reasons = []

    for policy in policies:
        if policy.get("risk") != item.get("risk"):
            continue

        matched_policies.append(policy["id"])

        if item.get("confidence", 0) < policy.get("min_confidence", 0):
            candidate_actions.append("block")
            reasons.append(
                f"{policy['id']}: confidence {item['confidence']} < {policy['min_confidence']}"
            )
        else:
            candidate_actions.extend(policy.get("allowed_actions", []))
            reasons.append(
                f"{policy['id']}: confidence threshold satisfied"
            )

    if not candidate_actions:
        final_action = default_action
        reason = "no applicable policy matched"
    else:
        final_action = resolve_action(candidate_actions)
        reason = "; ".join(reasons)

    if final_action == "allow":
        final_output = item["output"]
    elif final_action == "sanitize":
        final_output = SANITIZED_MESSAGE
    elif final_action == "escalate":
        final_output = "Sent for human review"
    else:
        final_output = "Output blocked"

    return {
        "id": item["id"],
        "decision": final_action,
        "applied_policies": matched_policies,
        "final_output": final_output,
        "reason": reason
    }


def main():
    inputs = load_json("inputs.json")
    policy_data = load_json("policies.json")

    policies = policy_data.get("policies", [])
    default_action = policy_data.get("default_action", "block")

    results = [
        evaluate_input(item, policies, default_action)
        for item in inputs
    ]

    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
