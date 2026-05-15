# AI-Powered-Campus-Service-Management-System
A modular, pipeline-based AI system for intelligent campus service management — built as an Artificial Intelligence semester project. It integrates **Search Algorithms**, **Logic/Knowledge Base**, **Constraint Satisfaction (CSP)**, and **Artificial Neural Networks (ANN)** into a unified CLI application.
##  Project Overview

Students, instructors, and staff can submit structured service requests through a CLI form. The system intelligently routes each request through the appropriate AI modules and returns a final response — including priority prediction, eligibility verification, room/slot assignment, and route guidance.

##  AI Modules

| Module | Technology | Purpose |
|---|---|---|
| Preprocessing | Rule-based validation + normalization | Cleans and structures raw CLI input |
| Request Router | Conditional pipeline logic | Selects which modules to run |
| ANN | Perceptron + MLP (from scratch) | Predicts request urgency and priority |
| Logic / KB | Forward chaining inference engine | Checks eligibility and rules |
| CSP Scheduler | Constraint satisfaction with backtracking | Assigns rooms and slots conflict-free |
| Search | BFS, UCS, A* + 6 more algorithms | Finds optimal campus routes |
| Final Response | Response aggregator | Combines all module outputs |

---

##  Request Types & Pipelines

| Request Type | Pipeline |
|---|---|
| `Navigation_Only` | Search |
| `Eligibility_Check` | Logic/KB |
| `Booking_or_Scheduling` | Logic/KB → CSP → (Search optional) |
| `Urgent_Service_Request` | ANN → Logic/KB → CSP → (Search optional) |
| `Full_Service_Request` | ANN → Logic/KB → CSP → Search |

---

##  How to Run

### Requirements
- Python 3.7+
- No external libraries required — everything is built from scratch using Python standard library only

### Run the system
```bash
python main.py
```

The system will:
1. Train ANN models (Perceptron + MLP) on startup
2. Run 6 automatic demo requests
3. Print the search algorithm comparison table
4. Launch interactive CLI mode

### Interactive mode
```
Enter Name: Ali
Enter Role (student/instructor/staff): student

Request Types:
  1. Navigation_Only
  2. Eligibility_Check
  3. Booking_or_Scheduling
  4. Urgent_Service_Request
  5. Full_Service_Request
Enter choice (1-5): 5
```

---

##  Campus Map (Nodes)

```
Main_Gate  →  Parking  →  Admin_Block  →  Student_Services
Exam_Hall  →  Seminar_Room  →  Library  →  AI_Lab
Science_Block  →  Cafeteria  →  Medical_Center  →  Bus_Stop  →  Hostel
```

Both **unweighted** and **weighted** graph representations are included.

---

##  Search Algorithms Included

| Algorithm | Graph Type | Role |
|---|---|---|
| BFS | Unweighted | ✅ Final operational (unweighted) |
| A* | Weighted | ✅ Final operational (weighted) |
| UCS | Weighted | ✅ Fallback operational |
| DFS | Unweighted | Academic comparison |
| DLS | Unweighted | Academic comparison |
| IDS | Unweighted | Academic comparison |
| Bidirectional BFS | Unweighted | Academic comparison |
| Greedy Best-First | Weighted | Academic comparison |
| RBFS | Weighted | Academic comparison |

---

##  ANN Architecture

### Perceptron (Binary Classifier)
- Input: 7-feature vector
- Output: `urgent` / `not_urgent`
- Used for: baseline comparison

### MLP (Multiclass Classifier)
- Architecture: 7 → 4 → 3 → 4
- Activation: ReLU (hidden), Softmax (output)
- Output classes: `low`, `normal`, `high`, `urgent`
- Used for: actual scheduling decisions

### Feature Vector
```
[Role, RequestType, Severity, TimeSensitivity, CrowdLevel, Distance, Eligibility]
```

---

##  Knowledge Base (Facts & Rules)

**Facts included:**
- `Teaches(DrKhan, AI)`
- `Student(Ali)`, `Student(Sara)`, `Student(Bilal)`
- `Enrolled(Ali, AI)`, `Enrolled(Sara, AI)`
- `Completed(Ali, ProgrammingFundamentals)`
- `Staff(Ahmad)`, `Group(G4)`

**Rules (Forward Chaining):**
- `Enrolled(X, AI) ∧ Student(X)` → `UsesLab(X, Lab1)`
- `Student(X) ∧ Completed(X, PF)` → `Eligible(X, AI)`
- `Eligible(X, AI)` → `CanBookLabSupport(X)`
- `Group(G4)` → `CanScheduleViva(G4)`
- `Staff(Ahmad)` → `CanAccessMaintenanceRequest(Ahmad)`

---

##  Valid Eligibility Queries

```
CanBookLabSupport(Ali)       ✅
CanBookLabSupport(Sara)      ✅
UsesLab(Ali, Lab1)           ✅
Eligible(Ali, AI)            ✅
CanScheduleViva(G4)          ✅
CanAccessMaintenanceRequest(Ahmad)  ✅
CanBookLabSupport(Bilal)     ❌
UsesLab(DrKhan, Lab1)        ❌
```

---

##  Sample Output — Full Service Request

```
=================================================================
   SMART CAMPUS RESPONSE  |  ID: REQ205
=================================================================
  Decision   : ACCEPTED
  Priority   : urgent → high (0.87)
  Eligibility: ✅ ALLOWED
  Assignment : Room AI_Lab, Slot 3
  Route      : Hostel → Cafeteria → Science_Block → AI_Lab
               Cost: 6, 3 steps
  Message    : Ali, your high-priority request accepted.
               Assigned AI_Lab, Slot 3. Route: Hostel → ...
=================================================================


### Module breakdown inside `main.py`

Module 1  –  Input & Preprocessing
Module 2  –  Request Router
Module 3  –  ANN Priority Module (Perceptron + MLP)
Module 4  –  Logic / Knowledge Base
Module 5  –  CSP Scheduler
Module 6  –  Search & Navigation
Module 7  –  Final Response Layer

##  Course

Artificial Intelligence — Semester Project  
This project was built for academic purposes.
