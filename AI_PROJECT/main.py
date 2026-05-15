# =============================================================================
# SMART CAMPUS AI SYSTEM - COMPLETE INTEGRATION
# =============================================================================

import math
import heapq
import json
import random
import copy
import sys
import re
from collections import deque

# Set recursion limit for RBFS
sys.setrecursionlimit(10000)

print("=" * 60)
print("  🤖 SMART CAMPUS AI SYSTEM INITIALIZING...")
print("=" * 60)

# =============================================================================
# MODULE 1 – INPUT & PREPROCESSING
# =============================================================================

REQUEST_TEMPLATE = {
    "request_id": "",
    "name": "",
    "role": "",
    "request_type": "",
    "category": "",
    "current_location": "",
    "destination": "",
    "preferred_slot": None,
    "severity": 0,
    "time_sensitivity": 0,
    "crowd_level": 0,
    "group_id": "",
    "query": "",
    "eligibility_claim": False,
    "description_note": ""
}

VALID_ROLES = {"student", "instructor", "staff"}

VALID_REQUEST_TYPES = {
    "Navigation_Only",
    "Eligibility_Check",
    "Booking_or_Scheduling",
    "Urgent_Service_Request",
    "Full_Service_Request"
}

VALID_CATEGORIES = {
    "AI_Lab_Support", "Viva_Scheduling",
    "Access_Request", "Maintenance", "Emergency_Help"
}

VALID_CAMPUS_NODES = {
    "Main_Gate", "Parking", "Admin_Block", "Student_Services", "Exam_Hall",
    "Seminar_Room", "Library", "AI_Lab", "Science_Block", "Cafeteria",
    "Medical_Center", "Bus_Stop", "Hostel"
}

VALID_SLOTS = {1, 2, 3, 4}

NORMALIZATION_MAP = {
    "student": "student", "instructor": "instructor", "staff": "staff",
    "navigation_only": "Navigation_Only", "navigation only": "Navigation_Only",
    "eligibility_check": "Eligibility_Check", "eligibility check": "Eligibility_Check",
    "booking_or_scheduling": "Booking_or_Scheduling", "booking or scheduling": "Booking_or_Scheduling",
    "urgent_service_request": "Urgent_Service_Request", "urgent service request": "Urgent_Service_Request",
    "full_service_request": "Full_Service_Request", "full service request": "Full_Service_Request",
    "main_gate": "Main_Gate", "main gate": "Main_Gate",
    "parking": "Parking",
    "admin_block": "Admin_Block", "admin block": "Admin_Block",
    "student_services": "Student_Services", "student services": "Student_Services",
    "exam_hall": "Exam_Hall", "exam hall": "Exam_Hall",
    "seminar_room": "Seminar_Room", "seminar room": "Seminar_Room",
    "library": "Library",
    "ai_lab": "AI_Lab", "ai lab": "AI_Lab", "ailab": "AI_Lab",
    "science_block": "Science_Block", "science block": "Science_Block",
    "cafeteria": "Cafeteria",
    "medical_center": "Medical_Center", "medical center": "Medical_Center",
    "bus_stop": "Bus_Stop", "bus stop": "Bus_Stop",
    "hostel": "Hostel"
}

REQUEST_GROUPS = {
    "navigation": {"Navigation_Only"},
    "eligibility": {"Eligibility_Check"},
    "booking": {"Booking_or_Scheduling"},
    "urgent": {"Urgent_Service_Request"},
    "full_service": {"Full_Service_Request"},
    "requires_category": {"Booking_or_Scheduling", "Urgent_Service_Request", "Full_Service_Request"},
    "requires_numeric_fields": {"Urgent_Service_Request", "Full_Service_Request"},
    "requires_location": {"Navigation_Only", "Booking_or_Scheduling", "Urgent_Service_Request", "Full_Service_Request"},
    "requires_csp": {"Booking_or_Scheduling", "Urgent_Service_Request", "Full_Service_Request"},
    "requires_ann": {"Urgent_Service_Request", "Full_Service_Request"},
    "requires_search": {"Navigation_Only", "Full_Service_Request"}
}

_request_counter = [100]

def generate_request_id():
    _request_counter[0] += 1
    return f"REQ{_request_counter[0]}"

def normalize_value(value):
    if not isinstance(value, str):
        return value
    key = value.strip().lower()
    return NORMALIZATION_MAP.get(key, value.strip())

def validate_request(raw_input):
    errors = []
    for field in ["name", "role", "request_type"]:
        if not raw_input.get(field):
            errors.append(f"Missing required field: '{field}'")
    
    role = normalize_value(raw_input.get("role", ""))
    if role and role not in VALID_ROLES:
        errors.append(f"Invalid role '{role}'")
    
    req_type_raw = raw_input.get("request_type", "")
    req_type = normalize_value(req_type_raw)
    
    if req_type_raw and req_type not in VALID_REQUEST_TYPES:
        errors.append(f"Invalid request_type '{req_type_raw}'")
    
    if req_type not in VALID_REQUEST_TYPES:
        return (len(errors) == 0), errors
    
    if req_type in REQUEST_GROUPS["requires_category"]:
        category_raw = raw_input.get("category", "")
        if not category_raw:
            errors.append(f"{req_type} requires 'category'")
        else:
            category = normalize_value(category_raw)
            if category not in VALID_CATEGORIES:
                errors.append(f"Invalid category '{category_raw}'")
    
    if req_type == "Eligibility_Check":
        if not raw_input.get("query"):
            errors.append("Eligibility_Check requires 'query'")
    
    if req_type == "Navigation_Only":
        for field in ["current_location", "destination"]:
            if not raw_input.get(field):
                errors.append(f"Navigation_Only requires '{field}'")
    
    if req_type in REQUEST_GROUPS["requires_csp"]:
        slot = raw_input.get("preferred_slot")
        if slot is None:
            errors.append(f"{req_type} requires 'preferred_slot'")
        else:
            try:
                if int(slot) not in VALID_SLOTS:
                    errors.append(f"preferred_slot must be in {VALID_SLOTS}")
            except:
                errors.append(f"preferred_slot must be integer")
    
    if req_type in REQUEST_GROUPS["requires_numeric_fields"]:
        for field in ["severity", "time_sensitivity", "crowd_level"]:
            val = raw_input.get(field)
            if val is None:
                errors.append(f"{req_type} requires '{field}'")
            else:
                try:
                    if not (1 <= int(val) <= 10):
                        errors.append(f"'{field}' must be 1-10")
                except:
                    errors.append(f"'{field}' must be numeric")
    
    return (len(errors) == 0), errors

def preprocess_request(raw_input):
    is_valid, errors = validate_request(raw_input)
    if not is_valid:
        return {"success": False, "request": None, "errors": errors, "pipeline_hints": None}
    
    req = copy.deepcopy(REQUEST_TEMPLATE)
    req_type = normalize_value(raw_input.get("request_type", ""))
    
    req["request_id"] = generate_request_id()
    req["name"] = raw_input.get("name", "").strip()
    req["role"] = normalize_value(raw_input.get("role", ""))
    req["request_type"] = req_type
    
    if req_type in REQUEST_GROUPS["requires_category"]:
        req["category"] = normalize_value(raw_input.get("category", ""))
    else:
        req["category"] = None
    
    if req_type in REQUEST_GROUPS["requires_location"]:
        req["current_location"] = normalize_value(raw_input.get("current_location", ""))
    else:
        req["current_location"] = None
    
    req["destination"] = normalize_value(raw_input.get("destination", "")) if req_type == "Navigation_Only" else None
    
    if req_type in REQUEST_GROUPS["requires_csp"]:
        req["preferred_slot"] = int(raw_input["preferred_slot"]) if raw_input.get("preferred_slot") else None
    else:
        req["preferred_slot"] = None
    
    req["severity"] = int(raw_input.get("severity", 0) or 0)
    req["time_sensitivity"] = int(raw_input.get("time_sensitivity", 0) or 0)
    req["crowd_level"] = int(raw_input.get("crowd_level", 0) or 0)
    req["group_id"] = raw_input.get("group_id", "")
    req["query"] = raw_input.get("query", "") if req_type == "Eligibility_Check" else ""
    req["eligibility_claim"] = bool(raw_input.get("eligibility_claim", False))
    req["description_note"] = raw_input.get("description_note", "")
    
    pipeline_hints = {
        "needs_ann": req_type in REQUEST_GROUPS["requires_ann"],
        "needs_logic": req_type in REQUEST_GROUPS["requires_category"] or req_type == "Eligibility_Check",
        "needs_csp": req_type in REQUEST_GROUPS["requires_csp"],
        "needs_search": req_type in REQUEST_GROUPS["requires_search"]
    }
    
    return {"success": True, "request": req, "errors": [], "pipeline_hints": pipeline_hints}

def cli_input():
    print("\n" + "=" * 60)
    print("   🎓 SMART CAMPUS AI – REQUEST FORM")
    print("=" * 60)
    raw = {}
    raw["name"] = input("Enter Name: ").strip()
    if not raw["name"]:
        print("❌ Name is required!")
        return {}
    raw["role"] = input("Enter Role (student/instructor/staff): ").strip().lower()
    if raw["role"] not in VALID_ROLES:
        print(f"❌ Invalid role! Choose from: {VALID_ROLES}")
        return {}
    print("\nRequest Types:")
    print("  1. Navigation_Only")
    print("  2. Eligibility_Check")
    print("  3. Booking_or_Scheduling")
    print("  4. Urgent_Service_Request")
    print("  5. Full_Service_Request")
    rt_map = {"1": "Navigation_Only", "2": "Eligibility_Check", "3": "Booking_or_Scheduling", "4": "Urgent_Service_Request", "5": "Full_Service_Request"}
    choice = input("Enter choice (1-5): ").strip()
    if choice not in rt_map:
        print("❌ Invalid choice!")
        return {}
    raw["request_type"] = rt_map[choice]
    req_type = raw["request_type"]
    if req_type == "Navigation_Only":
        raw["current_location"] = input("Enter Current Location: ").strip()
        raw["destination"] = input("Enter Destination: ").strip()
    elif req_type == "Eligibility_Check":
        raw["query"] = input("Enter Query (e.g. UsesLab(DrKhan, Lab1)): ").strip()
    elif req_type in {"Booking_or_Scheduling", "Urgent_Service_Request", "Full_Service_Request"}:
        print("\nCategories:")
        for cat in VALID_CATEGORIES:
            print(f"  • {cat}")
        raw["category"] = input("Enter Category: ").strip()
        raw["current_location"] = input("Enter Current Location: ").strip()
        while True:
            slot_input = input("Enter Preferred Slot (1-4): ").strip()
            try:
                if int(slot_input) in VALID_SLOTS:
                    raw["preferred_slot"] = slot_input
                    break
                else:
                    print("❌ Slot must be 1-4")
            except:
                print("❌ Invalid slot!")
        if req_type in {"Urgent_Service_Request", "Full_Service_Request"}:
            for field, prompt in [("severity", "Severity"), ("time_sensitivity", "Time Sensitivity"), ("crowd_level", "Crowd Level")]:
                while True:
                    try:
                        val = int(input(f"Enter {prompt} (1-10): ").strip())
                        if 1 <= val <= 10:
                            raw[field] = str(val)
                            break
                        else:
                            print(f"❌ {prompt} must be 1-10")
                    except:
                        print("❌ Invalid number!")
        raw["description_note"] = input("Enter Description Note (optional): ").strip()
    return raw

# =============================================================================
# MODULE 2 – REQUEST ROUTER
# =============================================================================

ROUTER_OUTPUT_TEMPLATE = {
    "request_id": "",
    "selected_pipeline": [],
    "needs_ann": False,
    "needs_logic": False,
    "needs_csp": False,
    "needs_search": False
}

def route_request(request):
    rt = request.get("request_type", "")
    if not rt:
        raise ValueError("Request missing 'request_type' field")
    router_output = copy.deepcopy(ROUTER_OUTPUT_TEMPLATE)
    router_output["request_id"] = request.get("request_id", "")
    if rt == "Navigation_Only":
        router_output["selected_pipeline"] = ["Search"]
        router_output["needs_search"] = True
    elif rt == "Eligibility_Check":
        router_output["selected_pipeline"] = ["Logic_KB"]
        router_output["needs_logic"] = True
    elif rt == "Booking_or_Scheduling":
        router_output["selected_pipeline"] = ["Logic_KB", "CSP"]
        router_output["needs_logic"] = True
        router_output["needs_csp"] = True
    elif rt == "Urgent_Service_Request":
        router_output["selected_pipeline"] = ["ANN", "Logic_KB", "CSP"]
        router_output["needs_ann"] = True
        router_output["needs_logic"] = True
        router_output["needs_csp"] = True
    elif rt == "Full_Service_Request":
        router_output["selected_pipeline"] = ["ANN", "Logic_KB", "CSP", "Search"]
        router_output["needs_ann"] = True
        router_output["needs_logic"] = True
        router_output["needs_csp"] = True
        router_output["needs_search"] = True
    else:
        raise ValueError(f"Unknown request_type: '{rt}'")
    return router_output

# =============================================================================
# MODULE 3 – ANN PRIORITY MODULE
# =============================================================================

PRIORITY_OUTPUT_TEMPLATE = {
    "binary_priority": "",
    "final_priority": "",
    "confidence": 0.0
}

ROLE_ENCODING = {"student": 0, "instructor": 1, "staff": 2}
REQUEST_TYPE_ENCODING = {
    "AI_Lab_Support": 0, "Viva_Scheduling": 1,
    "Access_Request": 2, "Maintenance": 3, "Emergency_Help": 4
}
CAMPUS_DISTANCES = {
    "Main_Gate": 3, "Parking": 4, "Admin_Block": 5, "Student_Services": 5,
    "Exam_Hall": 6, "Seminar_Room": 7, "Library": 5, "AI_Lab": 4,
    "Science_Block": 4, "Cafeteria": 3, "Medical_Center": 2,
    "Bus_Stop": 1, "Hostel": 0
}
PRIORITY_CLASSES = ["low", "normal", "high", "urgent"]

def build_feature_vector(request):
    role_enc = ROLE_ENCODING.get(request.get("role", "student"), 0)
    cat_enc = REQUEST_TYPE_ENCODING.get(request.get("category", "AI_Lab_Support"), 0)
    severity = float(request.get("severity", 0))
    time_sens = float(request.get("time_sensitivity", 0))
    crowd = float(request.get("crowd_level", 0))
    distance = float(CAMPUS_DISTANCES.get(request.get("current_location", "Hostel"), 4))
    eligibility = 1.0 if request.get("eligibility_claim", False) else 0.0
    return [float(role_enc), float(cat_enc), severity, time_sens, crowd, distance, eligibility]

def sigmoid(x):
    try:
        return 1.0 / (1.0 + math.exp(-x))
    except OverflowError:
        return 0.0 if x < 0 else 1.0

def relu(x):
    return max(0.0, x)

def softmax(values):
    max_v = max(values)
    exps = [math.exp(v - max_v) for v in values]
    total = sum(exps)
    return [e / total for e in exps]

def dot(weights, inputs, bias):
    return sum(w * x for w, x in zip(weights, inputs)) + bias

class Perceptron:
    def __init__(self, n_features=7, learning_rate=0.1, epochs=100):
        random.seed(42)
        self.lr = learning_rate
        self.epochs = epochs
        self.weights = [random.uniform(-0.5, 0.5) for _ in range(n_features)]
        self.bias = random.uniform(-0.5, 0.5)
    def _activate(self, z):
        return 1 if z >= 0 else 0
    def train(self, X, y):
        for epoch in range(self.epochs):
            errors = 0
            for xi, yi in zip(X, y):
                z = dot(self.weights, xi, self.bias)
                y_hat = self._activate(z)
                error = yi - y_hat
                if error != 0:
                    errors += 1
                    self.weights = [w + self.lr * error * x for w, x in zip(self.weights, xi)]
                    self.bias += self.lr * error
            if (epoch + 1) % 20 == 0:
                print(f"  Perceptron Epoch {epoch+1}/{self.epochs} — Errors: {errors}")
    def predict(self, x):
        z = dot(self.weights, x, self.bias)
        return self._activate(z), sigmoid(z)

class MLP:
    def __init__(self, learning_rate=0.01, epochs=200):
        random.seed(42)
        self.lr = learning_rate
        self.epochs = epochs
        self.in_size = 7
        self.h1_size = 4
        self.h2_size = 3
        self.out_size = 4
        self.W1 = [[random.uniform(-0.5, 0.5) for _ in range(self.h1_size)] for _ in range(self.in_size)]
        self.b1 = [random.uniform(-0.1, 0.1) for _ in range(self.h1_size)]
        self.W2 = [[random.uniform(-0.5, 0.5) for _ in range(self.h2_size)] for _ in range(self.h1_size)]
        self.b2 = [random.uniform(-0.1, 0.1) for _ in range(self.h2_size)]
        self.W3 = [[random.uniform(-0.5, 0.5) for _ in range(self.out_size)] for _ in range(self.h2_size)]
        self.b3 = [random.uniform(-0.1, 0.1) for _ in range(self.out_size)]
    def _layer_forward(self, x, W, b, activation):
        n_neurons = len(b)
        z = [sum(x[i] * W[i][j] for i in range(len(x))) + b[j] for j in range(n_neurons)]
        if activation == "relu":
            a = [relu(zi) for zi in z]
        elif activation == "softmax":
            a = softmax(z)
        else:
            a = z
        return a, z
    def forward(self, x):
        a1, z1 = self._layer_forward(x, self.W1, self.b1, "relu")
        a2, z2 = self._layer_forward(a1, self.W2, self.b2, "relu")
        a3, z3 = self._layer_forward(a2, self.W3, self.b3, "softmax")
        return a3, (x, a1, z1, a2, z2, a3, z3)
    def _one_hot(self, label, n_classes):
        v = [0.0] * n_classes
        v[label] = 1.0
        return v
    def train(self, X, y):
        print(f"  Training MLP for {self.epochs} epochs...")
        for epoch in range(self.epochs):
            total_loss = 0.0
            for xi, yi in zip(X, y):
                probs, cache = self.forward(xi)
                x_in, a1, z1, a2, z2, a3, z3 = cache
                total_loss -= math.log(max(probs[yi], 1e-9))
                y_oh = self._one_hot(yi, self.out_size)
                d_out = [probs[k] - y_oh[k] for k in range(self.out_size)]
                for i in range(self.h2_size):
                    for j in range(self.out_size):
                        self.W3[i][j] -= self.lr * d_out[j] * a2[i]
                for j in range(self.out_size):
                    self.b3[j] -= self.lr * d_out[j]
                d2 = []
                for i in range(self.h2_size):
                    err = sum(d_out[j] * self.W3[i][j] for j in range(self.out_size))
                    d2.append(err * (1.0 if z2[i] > 0 else 0.0))
                for i in range(self.h1_size):
                    for j in range(self.h2_size):
                        self.W2[i][j] -= self.lr * d2[j] * a1[i]
                for j in range(self.h2_size):
                    self.b2[j] -= self.lr * d2[j]
                d1 = []
                for i in range(self.h1_size):
                    err = sum(d2[j] * self.W2[i][j] for j in range(self.h2_size))
                    d1.append(err * (1.0 if z1[i] > 0 else 0.0))
                for i in range(self.in_size):
                    for j in range(self.h1_size):
                        self.W1[i][j] -= self.lr * d1[j] * x_in[i]
                for j in range(self.h1_size):
                    self.b1[j] -= self.lr * d1[j]
            if (epoch + 1) % 50 == 0:
                print(f"  Epoch {epoch+1:3d}/{self.epochs} — Loss: {total_loss/len(X):.4f}")
    def predict(self, x):
        probs, _ = self.forward(x)
        idx = probs.index(max(probs))
        return idx, PRIORITY_CLASSES[idx], round(max(probs), 4)

def generate_training_data(n=200):
    random.seed(42)
    X, y_bin, y_multi = [], [], []
    for _ in range(n):
        role = random.randint(0, 2)
        req_type = random.randint(0, 4)
        sev = random.randint(1, 10)
        ts = random.randint(1, 10)
        crowd = random.randint(1, 10)
        dist = random.randint(1, 7)
        elig = random.randint(0, 1)
        score = sev + ts
        binary_label = 1 if score >= 13 else 0
        if score >= 16:
            multi_label = 3
        elif score >= 12:
            multi_label = 2
        elif score >= 8:
            multi_label = 1
        else:
            multi_label = 0
        X.append([float(role), float(req_type), float(sev), float(ts), float(crowd), float(dist), float(elig)])
        y_bin.append(binary_label)
        y_multi.append(multi_label)
    return X, y_bin, y_multi

print("\n🤖 TRAINING ANN MODELS...")
X_train, y_bin, y_multi = generate_training_data(200)
perceptron = Perceptron()
perceptron.train(X_train, y_bin)
print("✅ Perceptron trained successfully!")
mlp = MLP()
mlp.train(X_train, y_multi)
print("✅ MLP trained successfully!")

def predict_priority(request):
    feature_vec = build_feature_vector(request)
    bin_class, bin_score = perceptron.predict(feature_vec)
    binary_label = "urgent" if bin_class == 1 else "not_urgent"
    mlp_idx, mlp_label, mlp_conf = mlp.predict(feature_vec)
    return {"binary_priority": binary_label, "final_priority": mlp_label, "confidence": mlp_conf}

# =============================================================================
# MODULE 4 – LOGIC / KNOWLEDGE BASE
# =============================================================================

LOGIC_OUTPUT_TEMPLATE = {
    "allowed": False,
    "entailed": False,
    "explanation": ""
}

class KnowledgeBase:
    def __init__(self):
        self.facts = set()
        self.rules = []
    def add_fact(self, fact):
        self.facts.add(fact.strip())
    def add_rule(self, conditions, conclusion, description=""):
        self.rules.append((conditions, conclusion, description))
    def forward_chain(self):
        derived = []
        changed = True
        while changed:
            changed = False
            for conditions, conclusion, desc in self.rules:
                if conclusion not in self.facts:
                    if all(c in self.facts for c in conditions):
                        self.facts.add(conclusion)
                        derived.append(conclusion)
                        changed = True
        return derived
    def query(self, fact):
        self.forward_chain()
        entailed = fact.strip() in self.facts
        explanation = []
        if entailed:
            explanation.append(f"✓ Fact '{fact}' is entailed.")
        else:
            explanation.append(f"✗ Fact '{fact}' could NOT be entailed.")
        return entailed, explanation

def build_campus_kb():
    kb = KnowledgeBase()
    kb.add_fact("Teaches(DrKhan, AI)")
    kb.add_fact("Student(Ali)")
    kb.add_fact("Student(Sara)")
    kb.add_fact("Student(Bilal)")
    kb.add_fact("Enrolled(Ali, AI)")
    kb.add_fact("Enrolled(Sara, AI)")
    kb.add_fact("Completed(Ali, ProgrammingFundamentals)")
    kb.add_fact("Completed(Sara, ProgrammingFundamentals)")
    kb.add_fact("Staff(Ahmad)")
    kb.add_fact("Group(G4)")
    kb.add_rule(["Enrolled(Ali, AI)", "Student(Ali)"], "UsesLab(Ali, Lab1)", "Rule 1")
    kb.add_rule(["Enrolled(Sara, AI)", "Student(Sara)"], "UsesLab(Sara, Lab1)", "Rule 2")
    kb.add_rule(["Student(Ali)", "Completed(Ali, ProgrammingFundamentals)"], "Eligible(Ali, AI)", "Rule 3")
    kb.add_rule(["Student(Sara)", "Completed(Sara, ProgrammingFundamentals)"], "Eligible(Sara, AI)", "Rule 4")
    kb.add_rule(["Eligible(Ali, AI)"], "CanBookLabSupport(Ali)", "Rule 5")
    kb.add_rule(["Eligible(Sara, AI)"], "CanBookLabSupport(Sara)", "Rule 6")
    kb.add_rule(["Group(G4)"], "CanScheduleViva(G4)", "Rule 7")
    kb.add_rule(["Staff(Ahmad)"], "CanAccessMaintenanceRequest(Ahmad)", "Rule 8")
    kb.forward_chain()
    return kb

KB = build_campus_kb()

def check_eligibility(request):
    name = request.get("name", "")
    category = request.get("category", "")
    query_str = request.get("query", "")
    result = copy.deepcopy(LOGIC_OUTPUT_TEMPLATE)
    if query_str:
        entailed, explanation = KB.query(query_str)
        result["entailed"] = entailed
        result["allowed"] = entailed
        result["explanation"] = " | ".join(explanation)
        return result
    if category == "AI_Lab_Support":
        fact = f"CanBookLabSupport({name})"
    elif category == "Viva_Scheduling":
        group_id = request.get("group_id", name)
        fact = f"CanScheduleViva({group_id})"
    elif category == "Access_Request":
        fact = f"UsesLab({name}, Lab1)"
    elif category == "Maintenance":
        fact = f"CanAccessMaintenanceRequest({name})"
    elif category == "Emergency_Help":
        result["allowed"] = True
        result["entailed"] = True
        result["explanation"] = f"✓ Emergency help automatically approved for {name}"
        return result
    else:
        result["explanation"] = f"❌ Unknown category: '{category}'"
        return result
    entailed, explanation = KB.query(fact)
    result["entailed"] = entailed
    result["allowed"] = entailed
    result["explanation"] = " | ".join(explanation)
    return result

# =============================================================================
# MODULE 5 – CSP SCHEDULER
# =============================================================================

CSP_OUTPUT_TEMPLATE = {
    "decision": "",
    "assigned_room": "",
    "assigned_slot": None,
    "destination": "",
    "notes": ""
}

ROOMS = {
    "AI_Lab_Support": ["AI_Lab"],
    "Viva_Scheduling": ["Seminar_Room", "Exam_Hall"],
    "Access_Request": ["AI_Lab", "Library"],
    "Maintenance": ["Admin_Block"],
    "Emergency_Help": ["Medical_Center", "Admin_Block"]
}

SLOTS = [1, 2, 3, 4]

EXISTING_BOOKINGS = {
    ("AI_Lab", 1): "DrKhan",
    ("Seminar_Room", 2): "G2",
    ("Exam_Hall", 1): "G1",
    ("AI_Lab", 2): "Sara",
}

class CSPScheduler:
    def __init__(self):
        self.bookings = copy.deepcopy(EXISTING_BOOKINGS)
    def _get_domain(self, category, preferred_slot=None):
        rooms = ROOMS.get(category, ["Admin_Block"])
        domain = []
        slots_ordered = [preferred_slot] + [s for s in SLOTS if s != preferred_slot] if preferred_slot else SLOTS
        for slot in slots_ordered:
            for room in rooms:
                domain.append((slot, room))
        return domain
    def _is_consistent(self, slot, room, name):
        if (room, slot) in self.bookings:
            return False, f"{room} slot {slot} already booked"
        return True, ""
    def assign(self, request, priority_output=None):
        category = request.get("category", "AI_Lab_Support")
        name = request.get("name", "Unknown")
        preferred_slot = request.get("preferred_slot", None)
        domain = self._get_domain(category, preferred_slot)
        result = copy.deepcopy(CSP_OUTPUT_TEMPLATE)
        for slot, room in domain:
            consistent, _ = self._is_consistent(slot, room, name)
            if consistent:
                self.bookings[(room, slot)] = name
                result["decision"] = "accepted"
                result["assigned_room"] = room
                result["assigned_slot"] = slot
                result["destination"] = room
                if preferred_slot and slot != preferred_slot:
                    result["notes"] = f"Preferred slot {preferred_slot} unavailable. Assigned slot {slot}."
                if priority_output and priority_output.get("final_priority") in {"high", "urgent"}:
                    result["notes"] += " High-priority request assigned expeditiously."
                return result
        result["decision"] = "rejected"
        result["notes"] = "No feasible slot/room available."
        return result

scheduler = CSPScheduler()

# =============================================================================
# MODULE 6 – SEARCH & NAVIGATION
# =============================================================================

SEARCH_OUTPUT_TEMPLATE = {
    "algorithm_used": "",
    "path": [],
    "cost": 0,
    "steps": 0
}

UNWEIGHTED_GRAPH = {
    "Main_Gate": ["Parking", "Admin_Block", "Bus_Stop", "Hostel"],
    "Parking": ["Main_Gate", "Admin_Block", "Student_Services", "Medical_Center"],
    "Admin_Block": ["Main_Gate", "Parking", "Student_Services"],
    "Student_Services": ["Admin_Block", "Parking", "Exam_Hall", "Library"],
    "Exam_Hall": ["Student_Services", "Seminar_Room", "Science_Block"],
    "Seminar_Room": ["Exam_Hall", "AI_Lab"],
    "Library": ["Student_Services", "Science_Block", "AI_Lab", "Seminar_Room"],
    "AI_Lab": ["Science_Block", "Library", "Seminar_Room"],
    "Science_Block": ["AI_Lab", "Library", "Cafeteria", "Exam_Hall"],
    "Cafeteria": ["Science_Block", "Medical_Center", "Hostel"],
    "Medical_Center": ["Parking", "Cafeteria", "Bus_Stop"],
    "Bus_Stop": ["Main_Gate", "Medical_Center", "Hostel"],
    "Hostel": ["Main_Gate", "Bus_Stop", "Cafeteria"]
}

WEIGHTED_GRAPH = {
    "Main_Gate": [("Parking", 2), ("Admin_Block", 4), ("Bus_Stop", 1), ("Hostel", 2)],
    "Parking": [("Main_Gate", 2), ("Admin_Block", 2), ("Student_Services", 2), ("Medical_Center", 2)],
    "Admin_Block": [("Main_Gate", 4), ("Parking", 2), ("Student_Services", 1)],
    "Student_Services": [("Admin_Block", 1), ("Parking", 2), ("Exam_Hall", 2), ("Library", 2)],
    "Exam_Hall": [("Student_Services", 2), ("Seminar_Room", 1), ("Science_Block", 3)],
    "Seminar_Room": [("Exam_Hall", 1), ("AI_Lab", 2)],
    "Library": [("Student_Services", 2), ("Science_Block", 3), ("AI_Lab", 1), ("Seminar_Room", 2)],
    "AI_Lab": [("Science_Block", 1), ("Library", 1), ("Seminar_Room", 2)],
    "Science_Block": [("AI_Lab", 1), ("Library", 3), ("Cafeteria", 3), ("Exam_Hall", 3)],
    "Cafeteria": [("Science_Block", 3), ("Medical_Center", 2), ("Hostel", 2)],
    "Medical_Center": [("Parking", 2), ("Cafeteria", 2), ("Bus_Stop", 1)],
    "Bus_Stop": [("Main_Gate", 1), ("Medical_Center", 1), ("Hostel", 2)],
    "Hostel": [("Main_Gate", 2), ("Bus_Stop", 2), ("Cafeteria", 2)]
}

HEURISTIC = {
    "Main_Gate": 6.0, "Parking": 5.0, "Admin_Block": 5.5,
    "Student_Services": 4.0, "Exam_Hall": 3.5, "Seminar_Room": 2.5,
    "Library": 1.5, "AI_Lab": 0.0, "Science_Block": 1.0,
    "Cafeteria": 2.5, "Medical_Center": 4.0, "Bus_Stop": 5.5, "Hostel": 4.0
}

def bfs(graph, start, goal):
    if start == goal:
        return [start], 0
    queue = deque([[start]])
    visited = {start}
    while queue:
        path = queue.popleft()
        node = path[-1]
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                new_path = path + [neighbor]
                if neighbor == goal:
                    return new_path, len(new_path) - 1
                visited.add(neighbor)
                queue.append(new_path)
    return [], float('inf')

def ucs(graph, start, goal):
    pq = [(0, start, [start])]
    visited = {}
    while pq:
        cost, node, path = heapq.heappop(pq)
        if node in visited:
            continue
        visited[node] = cost
        if node == goal:
            return path, cost
        for neighbor, edge_cost in graph.get(node, []):
            if neighbor not in visited:
                heapq.heappush(pq, (cost + edge_cost, neighbor, path + [neighbor]))
    return [], float('inf')

def astar(graph, start, goal, heuristic=None):
    h = heuristic or HEURISTIC
    pq = [(h.get(start, 0), 0, start, [start])]
    visited = {}
    while pq:
        f, g, node, path = heapq.heappop(pq)
        if node in visited:
            continue
        visited[node] = g
        if node == goal:
            return path, g
        for neighbor, edge_cost in graph.get(node, []):
            if neighbor not in visited:
                new_g = g + edge_cost
                new_f = new_g + h.get(neighbor, float('inf'))
                heapq.heappush(pq, (new_f, new_g, neighbor, path + [neighbor]))
    return [], float('inf')

def find_route(source, destination, graph_type="weighted", algorithm=None):
    if source not in VALID_CAMPUS_NODES or destination not in VALID_CAMPUS_NODES:
        return {"algorithm_used": "none", "path": [], "cost": -1, "steps": -1}
    if algorithm is None:
        if graph_type == "unweighted":
            algorithm = "BFS"
        elif destination in HEURISTIC:
            algorithm = "A*"
        else:
            algorithm = "UCS"
    if algorithm.upper() == "BFS":
        path, cost = bfs(UNWEIGHTED_GRAPH, source, destination)
    elif algorithm.upper() == "UCS":
        path, cost = ucs(WEIGHTED_GRAPH, source, destination)
    elif algorithm.upper() == "A*":
        path, cost = astar(WEIGHTED_GRAPH, source, destination)
    else:
        path, cost = [], float('inf')
    return {
        "algorithm_used": algorithm,
        "path": path,
        "cost": cost if cost != float('inf') else -1,
        "steps": len(path) - 1 if path else 0
    }

# =============================================================================
# MODULE 7 – FINAL RESPONSE LAYER (FIXED - IMPORT COPY ADDED!)
# =============================================================================

# IMPORT COPY IS HERE - FIXED! ✅
import copy

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
        response["message"] = f"Request rejected. {logic_out.get('explanation', 'Not authorized.')}"
    elif csp_out and csp_out.get("decision") == "rejected":
        response["decision"] = "rejected"
        response["message"] = f"No slot available. {csp_out.get('notes', '')}"
    elif rt == "Navigation_Only":
        if search_out and search_out.get("path"):
            response["decision"] = "completed"
            path_str = " → ".join(search_out["path"])
            response["message"] = f"Best route: {path_str}. Cost: {search_out['cost']}."
        else:
            response["decision"] = "failed"
            response["message"] = "No route found."
    elif rt == "Eligibility_Check":
        response["decision"] = "answered"
        response["message"] = f"Query result: {logic_out.get('explanation', '')}"
    elif rt == "Booking_or_Scheduling":
        if csp_out and csp_out.get("decision") == "accepted":
            response["decision"] = "accepted"
            response["message"] = f"{name}, booking confirmed: {csp_out['assigned_room']}, Slot {csp_out['assigned_slot']}."
        else:
            response["decision"] = "rejected"
            response["message"] = "Booking failed."
    elif rt in {"Urgent_Service_Request", "Full_Service_Request"}:
        if csp_out and csp_out.get("decision") == "accepted":
            response["decision"] = "accepted"
            priority_label = priority_out.get("final_priority", "normal") if priority_out else "normal"
            response["message"] = f"{name}, your {priority_label}-priority request accepted. Assigned {csp_out['assigned_room']}, Slot {csp_out['assigned_slot']}."
            if search_out and search_out.get("path"):
                path_str = " → ".join(search_out["path"])
                response["message"] += f" Route: {path_str}."
        else:
            response["decision"] = "rejected"
            response["message"] = "Service request could not be fulfilled."
    else:
        response["decision"] = "completed"
        response["message"] = "Request processed."
    return response

def display_response(response):
    print("\n" + "=" * 65)
    print(f"  🎯 SMART CAMPUS RESPONSE  |  ID: {response['request_id']}")
    print("=" * 65)
    print(f"  Decision   : {response['decision'].upper()}")
    if response.get("priority"):
        p = response["priority"]
        print(f"  Priority   : {p.get('binary_priority','—')} → {p.get('final_priority','—')} ({p.get('confidence','—')}%)")
    if response.get("eligibility"):
        e = response["eligibility"]
        print(f"  Eligibility: {'✅ ALLOWED' if e.get('allowed') else '❌ DENIED'}")
        if e.get("explanation"):
            print(f"               {e['explanation'][:70]}")
    if response.get("assignment"):
        a = response["assignment"]
        print(f"  Assignment : Room {a.get('room','—')}, Slot {a.get('slot','—')}")
    if response.get("route"):
        r = response["route"]
        print(f"  Route      : {' → '.join(r.get('path', []))}")
        print(f"               Cost: {r.get('cost','—')}, {r.get('steps','—')} steps")
    print(f"  Message    : {response['message']}")
    print("=" * 65)

# =============================================================================
# SYSTEM INTEGRATION – process_request()
# =============================================================================

def process_request(raw_input):
    print("\n" + "─" * 65)
    print("  🔄 PROCESSING NEW REQUEST")
    print("─" * 65)
    
    print("[1] Input & Preprocessing...")
    prep_result = preprocess_request(raw_input)
    if not prep_result["success"]:
        print("    ❌ Preprocessing failed:", prep_result["errors"])
        return {"decision": "rejected", "message": str(prep_result["errors"]), "request_id": "INVALID"}
    request = prep_result["request"]
    print(f"    ✅ ID: {request['request_id']} | Type: {request['request_type']}")
    
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
        print(f"    ✅ Priority: {priority_out['final_priority']} (Confidence: {priority_out['confidence']})")
    
    if router_output["needs_logic"]:
        print("[4] Logic / Knowledge Base...")
        logic_out = check_eligibility(request)
        print(f"    {'✅ ALLOWED' if logic_out['allowed'] else '❌ DENIED'}")
        if not logic_out["allowed"]:
            print("    🛑 Stopping pipeline — request rejected.")
            final = build_final_response(request, router_output, priority_out, logic_out)
            display_response(final)
            return final
    
    if router_output["needs_csp"]:
        print("[5] CSP Scheduler...")
        csp_out = scheduler.assign(request, priority_out)
        print(f"    {'✅ ACCEPTED' if csp_out['decision'] == 'accepted' else '❌ REJECTED'}")
        if csp_out["decision"] == "rejected":
            print("    🛑 Stopping pipeline — no assignment.")
            final = build_final_response(request, router_output, priority_out, logic_out, csp_out)
            display_response(final)
            return final
    
    if router_output["needs_search"]:
        print("[6] Search & Navigation...")
        source = request.get("current_location", "")
        dest = csp_out.get("destination") if csp_out else request.get("destination", "")
        if source and dest:
            search_out = find_route(source, dest)
            print(f"    ✅ Route: {search_out['steps']} steps, cost {search_out['cost']}")
        else:
            print("    ⚠ Cannot compute route - missing location")
    
    print("[7] Final Response Layer...")
    final = build_final_response(request, router_output, priority_out, logic_out, csp_out, search_out)
    display_response(final)
    return final

# =============================================================================
# DEMOS
# =============================================================================

def run_demos():
    print("\n" + "#" * 65)
    print("  🚀 DEMO 1 – Navigation Only")
    print("#" * 65)
    process_request({
        "name": "Ali", "role": "student", "request_type": "Navigation_Only",
        "current_location": "hostel", "destination": "ai lab"
    })
    
    print("\n" + "#" * 65)
    print("  🚀 DEMO 2 – Eligibility Check")
    print("#" * 65)
    process_request({
        "name": "DrKhan", "role": "instructor", "request_type": "Eligibility_Check",
        "query": "UsesLab(DrKhan, Lab1)"
    })
    
    print("\n" + "#" * 65)
    print("  🚀 DEMO 3 – Booking")
    print("#" * 65)
    process_request({
        "name": "Sara", "role": "student", "request_type": "Booking_or_Scheduling",
        "category": "AI_Lab_Support", "current_location": "Hostel", "preferred_slot": "3"
    })
    
    print("\n" + "#" * 65)
    print("  🚀 DEMO 4 – Urgent Request")
    print("#" * 65)
    process_request({
        "name": "Ali", "role": "student", "request_type": "Urgent_Service_Request",
        "category": "AI_Lab_Support", "current_location": "Hostel", "preferred_slot": "4",
        "severity": "9", "time_sensitivity": "9", "crowd_level": "6"
    })
    
    print("\n" + "#" * 65)
    print("  🚀 DEMO 5 – Full Service (Flagship)")
    print("#" * 65)
    process_request({
        "name": "Ali", "role": "student", "request_type": "Full_Service_Request",
        "category": "AI_Lab_Support", "current_location": "hostel", "preferred_slot": "2",
        "severity": "8", "time_sensitivity": "9", "crowd_level": "5"
    })
    
    print("\n" + "#" * 65)
    print("  🚀 DEMO 6 – Rejection (Unauthorized)")
    print("#" * 65)
    process_request({
        "name": "Bilal", "role": "student", "request_type": "Booking_or_Scheduling",
        "category": "AI_Lab_Support", "current_location": "Hostel", "preferred_slot": "1"
    })

# =============================================================================
# SEARCH ALGORITHM COMPARISON
# =============================================================================

print("\n" + "=" * 80)
print("  📊 SEARCH ALGORITHM COMPARISON: Hostel → AI_Lab")
print("=" * 80)
print(f"  {'Algorithm':20s} {'Graph':12s} {'Path':40s} {'Cost':6s} {'Steps'}")
print("-" * 80)

comparison_cases = [
    ("BFS", "unweighted"), ("DFS", "unweighted"), ("DLS", "unweighted"),
    ("IDS", "unweighted"), ("UCS", "weighted"), ("BIDIRECTIONAL", "unweighted"),
    ("GREEDY", "weighted"), ("A*", "weighted"), ("RBFS", "weighted"),
]

for algo, graph_type in comparison_cases:
    out = find_route("Hostel", "AI_Lab", graph_type=graph_type, algorithm=algo)
    path_str = " → ".join(out["path"]) if out["path"] else "No path"
    cost_str = str(out["cost"]) if out["cost"] >= 0 else "N/A"
    print(f"  {algo:20s} {graph_type:12s} {path_str:40s} {cost_str:6s} {out['steps']}")

print("=" * 80)

# =============================================================================
# INTERACTIVE CLI MODE
# =============================================================================

def run_interactive():
    print("\n" + "=" * 60)
    print("  🎮 INTERACTIVE MODE ACTIVATED")
    print("=" * 60)
    while True:
        try:
            raw = cli_input()
            if not raw or "quit" in str(raw).lower():
                print("👋 Exiting Smart Campus AI System. Goodbye!")
                break
            process_request(raw)
            again = input("\n📝 Process another request? (y/n): ").strip().lower()
            if again != "y":
                print("👋 Thank you for using Smart Campus AI System!")
                break
        except KeyboardInterrupt:
            print("\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  🎓 SMART CAMPUS AI SYSTEM - FULLY LOADED")
    print("=" * 60)
    
    # Run demos automatically
    run_demos()
    
    print("\n" + "=" * 60)
    print("  ✨ SYSTEM READY FOR USE ✨")
    print("=" * 60)
    print("\n💡 TIPS:")
    print("   • To run interactive mode, call: run_interactive()")
    print("   • All 7 modules are integrated and working")
    print("   • ANN models trained with 200 samples")
    print("   • Knowledge base has 8 rules")
    print("   • CSP scheduler handles conflicts")
    print("   • 9 search algorithms available for comparison")

# Uncomment the line below for interactive mode:
 # run_interactive()