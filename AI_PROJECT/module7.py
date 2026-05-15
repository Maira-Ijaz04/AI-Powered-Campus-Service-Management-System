
# =============================================================================
# MODULE 7 – FINAL RESPONSE LAYER
# =============================================================================

FINAL_RESPONSE_TEMPLATE = {
    "request_id": "",
    "decision": "",
    "priority": {},
    "eligibility": {},
    "assignment": {},
    "route": {},
    "message": ""
}

def build_final_response(request, router_output, priority_out=None, logic_out=None, csp_out=None, search_out=None):
    response = copy.deepcopy(FINAL_RESPONSE_TEMPLATE)
    response["request_id"] = request.get("request_id", "")
    if priority_out:
        response["priority"] = priority_out
    if logic_out:
        response["eligibility"] = {
            "allowed": logic_out.get("allowed", False),
            "entailed": logic_out.get("entailed", False),
            "explanation": logic_out.get("explanation", "")
        }
    if csp_out and csp_out.get("decision") == "accepted":
        response["assignment"] = {
            "room": csp_out.get("assigned_room", ""),
            "slot": csp_out.get("assigned_slot", None),
            "notes": csp_out.get("notes", "")
        }
    if search_out and search_out.get("path"):
        response["route"] = {
            "algorithm": search_out.get("algorithm_used", ""),
            "path": search_out.get("path", []),
            "cost": search_out.get("cost", 0),
            "steps": search_out.get("steps", 0)
        }
    rt = request.get("request_type", "")
    name = request.get("name", "User")
    if logic_out and not logic_out.get("allowed", True):
        response["decision"] = "rejected"
        response["message"] = (f"Your request has been rejected. Reason: {logic_out.get('explanation', 'Not authorized.')}")
    elif csp_out and csp_out.get("decision") == "rejected":
        response["decision"] = "rejected"
        response["message"] = (f"No available slot or room could be assigned. {csp_out.get('notes', '')}")
    elif rt == "Navigation_Only":
        if search_out and search_out.get("path"):
            response["decision"] = "completed"
            path_str = " → ".join(search_out["path"])
            response["message"] = f"Best route: {path_str}. Total cost: {search_out['cost']}."
        else:
            response["decision"] = "failed"
            response["message"] = "No valid route found between the specified locations."
    elif rt == "Eligibility_Check":
        if logic_out and logic_out.get("allowed"):
            response["decision"] = "answered"
            response["message"] = f"Eligibility query answered: {logic_out.get('explanation', '')}"
        else:
            response["decision"] = "answered"
            response["message"] = f"Query result: Not entailed. {logic_out.get('explanation', '')}"
    elif rt == "Booking_or_Scheduling":
        if csp_out and csp_out.get("decision") == "accepted":
            response["decision"] = "accepted"
            room = csp_out["assigned_room"]
            slot = csp_out["assigned_slot"]
            response["message"] = (f"{name}, your booking is confirmed. Room: {room}, Slot: {slot}.")
            if search_out and search_out.get("path"):
                path_str = " → ".join(search_out["path"])
                response["message"] += f" Route: {path_str}."
        else:
            response["decision"] = "rejected"
            response["message"] = "Booking could not be completed."
    elif rt in {"Urgent_Service_Request", "Full_Service_Request"}:
        if csp_out and csp_out.get("decision") == "accepted":
            response["decision"] = "accepted"
            room = csp_out["assigned_room"]
            slot = csp_out["assigned_slot"]
            priority_label = priority_out.get("final_priority", "normal") if priority_out else "normal"
            response["message"] = (f"{name}, your {priority_label}-priority request has been accepted. You are assigned {room} in slot {slot}.")
            if search_out and search_out.get("path"):
                path_str = " → ".join(search_out["path"])
                response["message"] += f" Please follow the recommended route: {path_str}."
        else:
            response["decision"] = "rejected"
            response["message"] = "Service request could not be fulfilled."
    else:
        response["decision"] = "completed"
        response["message"] = "Request processed successfully."
    return response

def display_response(response):
    print("\n" + "=" * 65)
    print(f"  SMART CAMPUS RESPONSE  |  Request ID: {response['request_id']}")
    print("=" * 65)
    print(f"  Decision   : {response['decision'].upper()}")
    if response.get("priority"):
        p = response["priority"]
        print(f"  Priority   : Binary={p.get('binary_priority','—')}  Final={p.get('final_priority','—')}  Confidence={p.get('confidence','—')}")
    if response.get("eligibility"):
        e = response["eligibility"]
        print(f"  Eligibility: Allowed={e.get('allowed','—')}")
        if e.get("explanation"):
            print(f"               {e['explanation'][:70]}")
    if response.get("assignment"):
        a = response["assignment"]
        print(f"  Assignment : Room={a.get('room','—')}  Slot={a.get('slot','—')}")
        if a.get("notes"):
            print(f"               {a['notes'][:70]}")
    if response.get("route"):
        r = response["route"]
        path_str = " → ".join(r.get("path", []))
        print(f"  Route      : [{r.get('algorithm','—')}] {path_str}")
        print(f"               Cost={r.get('cost','—')}  Steps={r.get('steps','—')}")
    print(f"  Message    : {response['message']}")
    print("=" * 65)

# =============================================================================
# SYSTEM INTEGRATION – process_request()
# =============================================================================

def process_request(raw_input):
    print("\n" + "─" * 65)
    print("  PROCESSING NEW REQUEST")
    print("─" * 65)
    print("[1] Input & Preprocessing...")
    prep_result = preprocess_request(raw_input)
    if not prep_result["success"]:
        print("    ❌ Preprocessing failed:", prep_result["errors"])
        return {"decision": "rejected", "message": str(prep_result["errors"]), "request_id": "INVALID"}
    request = prep_result["request"]
    print(f"    ✅ Request ID: {request['request_id']} | Type: {request['request_type']}")
    print("[2] Request Router...")
    router_output = route_request(request)
    print(f"    ✅ Pipeline: {router_output['selected_pipeline']}")
    priority_out = None
    logic_out = None
    csp_out = None
    search_out = None
    if router_output["needs_ann"]:
        print("[3] ANN Priority Module...")
        priority_out = predict_priority(request)
        print(f"    ✅ Binary={priority_out['binary_priority']} | Final={priority_out['final_priority']} | Confidence={priority_out['confidence']}")
    if router_output["needs_logic"]:
        print("[4] Logic / Knowledge Base...")
        logic_out = check_eligibility(request)
        status = "✅ ALLOWED" if logic_out["allowed"] else "❌ DENIED"
        print(f"    {status}")
        if not logic_out["allowed"]:
            print("    Stopping pipeline — request rejected at Logic/KB.")
            final = build_final_response(request, router_output, priority_out, logic_out)
            display_response(final)
            return final
    if router_output["needs_csp"]:
        print("[5] CSP Scheduler...")
        csp_out = scheduler.assign(request, priority_out)
        print(f"    {'✅' if csp_out['decision']=='accepted' else '❌'} Decision: {csp_out['decision']} | Room: {csp_out['assigned_room']} | Slot: {csp_out['assigned_slot']}")
        if csp_out["decision"] == "rejected":
            print("    Stopping pipeline — no feasible assignment.")
            final = build_final_response(request, router_output, priority_out, logic_out, csp_out)
            display_response(final)
            return final
    needs_search = router_output["needs_search"]
    if not needs_search and csp_out and csp_out.get("destination") and request.get("current_location"):
        needs_search = True
    if needs_search:
        print("[6] Search & Navigation...")
        source = request.get("current_location", "")
        destination = (csp_out["destination"] if csp_out and csp_out.get("destination") else request.get("destination", ""))
        if source and destination:
            search_out = find_route(source, destination, graph_type="weighted")
            path_str = " → ".join(search_out["path"]) if search_out["path"] else "No path"
            print(f"    ✅ [{search_out['algorithm_used']}] {path_str} (Cost={search_out['cost']})")
        else:
            print("    ⚠ Source or destination missing — skipping Search.")
    print("[7] Final Response Layer...")
    final = build_final_response(request, router_output, priority_out, logic_out, csp_out, search_out)
    display_response(final)
    return final

print("✅ Full System Integration loaded.")

# =============================================================================
# DEMOS
# =============================================================================

print("\n" + "#" * 65)
print("  DEMO 1 – Navigation Only")
print("#" * 65)

nav_request = {
    "name": "Ali",
    "role": "student",
    "request_type": "Navigation_Only",
    "current_location": "hostel",
    "destination": "ai lab"
}
process_request(nav_request)

print("\n" + "#" * 65)
print("  DEMO 2 – Eligibility Check (DrKhan uses Lab1?)")
print("#" * 65)

elig_request = {
    "name": "DrKhan",
    "role": "instructor",
    "request_type": "Eligibility_Check",
    "query": "UsesLab(DrKhan, Lab1)"
}
process_request(elig_request)

print("\n" + "#" * 65)
print("  DEMO 3 – Booking or Scheduling")
print("#" * 65)

booking_request = {
    "name": "Sara",
    "role": "student",
    "request_type": "Booking_or_Scheduling",
    "category": "AI_Lab_Support",
    "current_location": "Hostel",
    "preferred_slot": "3"
}
process_request(booking_request)

print("\n" + "#" * 65)
print("  DEMO 4 – Urgent Service Request")
print("#" * 65)

urgent_request = {
    "name": "Ali",
    "role": "student",
    "request_type": "Urgent_Service_Request",
    "category": "AI_Lab_Support",
    "current_location": "Hostel",
    "preferred_slot": "4",
    "severity": "9",
    "time_sensitivity": "9",
    "crowd_level": "6",
    "description_note": "Critical issue with lab equipment."
}
process_request(urgent_request)

print("\n" + "#" * 65)
print("  DEMO 5 – Full Service Request (Flagship Demo)")
print("#" * 65)

full_request = {
    "name": "Ali",
    "role": "student",
    "request_type": "Full_Service_Request",
    "category": "AI_Lab_Support",
    "current_location": "hostel",
    "preferred_slot": "2",
    "severity": "8",
    "time_sensitivity": "9",
    "crowd_level": "5",
    "description_note": "Need urgent help before practical evaluation."
}
process_request(full_request)

print("\n" + "#" * 65)
print("  DEMO 6 – Rejection: Unauthorized User")
print("#" * 65)

rejected_request = {
    "name": "Bilal",
    "role": "student",
    "request_type": "Booking_or_Scheduling",
    "category": "AI_Lab_Support",
    "current_location": "Hostel",
    "preferred_slot": "1"
}
process_request(rejected_request)

# =============================================================================
# ACADEMIC COMPARISON – All Search Algorithms
# =============================================================================

print("\n" + "=" * 80)
print("  SEARCH ALGORITHM COMPARISON: Hostel → AI_Lab")
print("=" * 80)
print(f"  {'Algorithm':20s} {'Graph':12s} {'Path':35s} {'Cost':6s} {'Steps'}")
print("-" * 80)

comparison_cases = [
    ("BFS",          "unweighted"),
    ("DFS",          "unweighted"),
    ("DLS",          "unweighted"),
    ("IDS",          "unweighted"),
    ("UCS",          "weighted"),
    ("BIDIRECTIONAL","unweighted"),
    ("GREEDY",       "weighted"),
    ("A*",           "weighted"),
    ("RBFS",         "weighted"),
]

for algo, graph_type in comparison_cases:
    out = find_route("Hostel", "AI_Lab", graph_type=graph_type, algorithm=algo)
    path_str = " → ".join(out["path"]) if out["path"] else "No path"
    cost_str = str(out["cost"]) if out["cost"] >= 0 else "N/A"
    print(f"  {algo:20s} {graph_type:12s} {path_str:35s} {cost_str:6s} {out['steps']}")

print("=" * 80)

# =============================================================================
# INTERACTIVE CLI MODE (Uncomment to use)
# =============================================================================

def run_interactive():
    while True:
        try:
            raw = cli_input()
            if "quit" in str(raw).lower():
                print("Exiting Smart Campus AI System.")
                break
            process_request(raw)
            again = input("\nProcess another request? (y/n): ").strip().lower()
            if again != "y":
                print("Thank you for using Smart Campus AI System.")
                break
        except KeyboardInterrupt:
            print("\nInterrupted. Exiting.")
            break
        except Exception as e:
            print(f"\nError: {e}. Please try again.")

# Uncomment the line below to launch interactive mode instead of demos:
# run_interactive()

print("\n✅ All modules loaded successfully!")
print("💡 Tip: Uncomment 'run_interactive()' at the bottom to use the interactive CLI mode.")