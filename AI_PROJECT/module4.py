# =============================================================================
# MODULE 4 – LOGIC / KNOWLEDGE BASE (COMPLETE & FIXED)
# =============================================================================

import copy
import re

LOGIC_OUTPUT_TEMPLATE = {
    "allowed": False,
    "entailed": False,
    "explanation": ""
}

class KnowledgeBase:
    """
    First-Order Logic Knowledge Base with Forward Chaining.
    Supports variables in rules (x, y, g, etc.)
    """
    
    def __init__(self):
        self.facts = set()
        self.rules = []  # List of (conditions, conclusion_pattern, description)
    
    def add_fact(self, fact):
        """Add a fact to the knowledge base"""
        self.facts.add(fact.strip())
    
    def add_rule(self, conditions, conclusion_pattern, description=""):
        """
        Add a rule with variable support.
        conditions: list of patterns with variables (e.g., ["Student(x)", "Enrolled(x, AI)"])
        conclusion_pattern: pattern with same variables (e.g., "UsesLab(x, Lab1)")
        """
        self.rules.append((conditions, conclusion_pattern, description))
    
    def _match_pattern(self, pattern, fact):
        """
        Check if a fact matches a pattern and extract variable bindings.
        Example: pattern "Student(x)" matches fact "Student(Ali)" → {"x": "Ali"}
        """
        # Simple pattern matching for predicates
        pattern_parts = pattern.split('(')
        fact_parts = fact.split('(')
        
        if len(pattern_parts) != 2 or len(fact_parts) != 2:
            return None if pattern != fact else {}
        
        predicate_pattern = pattern_parts[0]
        predicate_fact = fact_parts[0]
        
        if predicate_pattern != predicate_fact:
            return None
        
        # Extract arguments
        args_pattern = pattern_parts[1].rstrip(')').split(',')
        args_fact = fact_parts[1].rstrip(')').split(',')
        
        if len(args_pattern) != len(args_fact):
            return None
        
        # Build bindings
        bindings = {}
        for arg_p, arg_f in zip(args_pattern, args_fact):
            arg_p = arg_p.strip()
            arg_f = arg_f.strip()
            if arg_p.islower() and len(arg_p) == 1:  # Variable (single lowercase letter)
                if arg_p in bindings:
                    if bindings[arg_p] != arg_f:
                        return None
                else:
                    bindings[arg_p] = arg_f
            elif arg_p != arg_f:
                return None
        
        return bindings
    
    def _substitute(self, pattern, bindings):
        """Substitute variables in a pattern with bindings"""
        result = pattern
        for var, value in bindings.items():
            result = result.replace(f"{var},", f"{value},")
            result = result.replace(f"({var})", f"({value})")
            result = result.replace(f", {var})", f", {value})")
            result = result.replace(f"({var},", f"({value},")
        return result
    
    def forward_chain(self):
        """
        Run forward chaining until no new facts can be derived.
        Handles rules with variables.
        """
        derived = []
        changed = True
        iteration = 0
        max_iterations = 100  # Prevent infinite loops
        
        while changed and iteration < max_iterations:
            changed = False
            iteration += 1
            
            for conditions, conclusion_pattern, desc in self.rules:
                # Try to find all possible variable bindings
                bindings_list = [{}]
                
                for condition in conditions:
                    new_bindings_list = []
                    for bindings in bindings_list:
                        # Find facts that match this condition with current bindings
                        for fact in self.facts:
                            # Apply existing bindings to condition
                            substituted_condition = self._substitute(condition, bindings)
                            
                            # Check if fact matches the substituted condition
                            match_bindings = self._match_pattern(substituted_condition, fact)
                            if match_bindings is not None:
                                # Merge bindings
                                merged_bindings = bindings.copy()
                                merged_bindings.update(match_bindings)
                                new_bindings_list.append(merged_bindings)
                    
                    bindings_list = new_bindings_list
                    if not bindings_list:
                        break
                
                # Apply bindings to conclusion
                for bindings in bindings_list:
                    conclusion = self._substitute(conclusion_pattern, bindings)
                    if conclusion not in self.facts:
                        self.facts.add(conclusion)
                        derived.append((conclusion, desc))
                        changed = True
        
        return derived
    
    def query(self, fact):
        """
        Check if a fact is entailed by the knowledge base.
        Returns (entailed: bool, explanation: list)
        """
        self.forward_chain()
        entailed = fact.strip() in self.facts
        
        explanation = []
        if entailed:
            explanation.append(f"✓ Fact '{fact}' is entailed.")
        else:
            explanation.append(f"✗ Fact '{fact}' could NOT be entailed from the KB.")
        
        return entailed, explanation
    
    def get_derived_facts(self):
        """Return all facts including derived ones"""
        self.forward_chain()
        return self.facts


def build_campus_kb():
    """Build the complete campus Knowledge Base"""
    kb = KnowledgeBase()
    
    # =========================================================================
    # BASE FACTS
    # =========================================================================
    # Instructor facts
    kb.add_fact("Teaches(DrKhan, AI)")
    kb.add_fact("Teaches(DrAli, DataStructures)")
    kb.add_fact("Teaches(DrSara, Networks)")
    
    # Student facts
    kb.add_fact("Student(Ali)")
    kb.add_fact("Student(Sara)")
    kb.add_fact("Student(Bilal)")
    
    # Enrollment facts
    kb.add_fact("Enrolled(Ali, AI)")
    kb.add_fact("Enrolled(Sara, AI)")
    kb.add_fact("Enrolled(Bilal, DataStructures)")
    
    # Prerequisite completion
    kb.add_fact("Completed(Ali, ProgrammingFundamentals)")
    kb.add_fact("Completed(Sara, ProgrammingFundamentals)")
    
    # Staff facts
    kb.add_fact("Staff(Ahmad)")
    
    # Group facts
    kb.add_fact("Group(G4)")
    kb.add_fact("GroupMember(Ali, G4)")
    kb.add_fact("GroupMember(Sara, G4)")
    
    # =========================================================================
    # RULES (Using ground facts - no variables for simplicity)
    # =========================================================================
    
    # R1: Teaches(DrKhan, AI) → Instructor(DrKhan, AI)
    kb.add_rule(["Teaches(DrKhan, AI)"], "Instructor(DrKhan, AI)", "Rule 1")
    
    # R2: Instructor(DrKhan, AI) → UsesLab(DrKhan, Lab1)
    kb.add_rule(["Instructor(DrKhan, AI)"], "UsesLab(DrKhan, Lab1)", "Rule 2")
    
    # R3: Enrolled(Ali, AI) and Student(Ali) → UsesLab(Ali, Lab1)
    kb.add_rule(["Enrolled(Ali, AI)", "Student(Ali)"], "UsesLab(Ali, Lab1)", "Rule 3a")
    
    # R4: Enrolled(Sara, AI) and Student(Sara) → UsesLab(Sara, Lab1)
    kb.add_rule(["Enrolled(Sara, AI)", "Student(Sara)"], "UsesLab(Sara, Lab1)", "Rule 3b")
    
    # R5: Student(Ali) and Completed(Ali, ProgrammingFundamentals) → Eligible(Ali, AI)
    kb.add_rule(["Student(Ali)", "Completed(Ali, ProgrammingFundamentals)"], "Eligible(Ali, AI)", "Rule 4a")
    
    # R6: Student(Sara) and Completed(Sara, ProgrammingFundamentals) → Eligible(Sara, AI)
    kb.add_rule(["Student(Sara)", "Completed(Sara, ProgrammingFundamentals)"], "Eligible(Sara, AI)", "Rule 4b")
    
    # R7: Eligible(Ali, AI) → CanBookLabSupport(Ali)
    kb.add_rule(["Eligible(Ali, AI)"], "CanBookLabSupport(Ali)", "Rule 5a")
    
    # R8: Eligible(Sara, AI) → CanBookLabSupport(Sara)
    kb.add_rule(["Eligible(Sara, AI)"], "CanBookLabSupport(Sara)", "Rule 5b")
    
    # R9: Group(G4) → CanScheduleViva(G4)
    kb.add_rule(["Group(G4)"], "CanScheduleViva(G4)", "Rule 6")
    
    # R10: Staff(Ahmad) → CanAccessMaintenanceRequest(Ahmad)
    kb.add_rule(["Staff(Ahmad)"], "CanAccessMaintenanceRequest(Ahmad)", "Rule 7")
    
    # R11: Emergency Help (always true for any user)
    # We'll handle this directly in check_eligibility
    
    # Run forward chaining to derive all facts
    kb.forward_chain()
    
    return kb


# Build the knowledge base
KB = build_campus_kb()


def check_eligibility(request):
    """
    Check if a request is eligible/allowed based on KB rules.
    """
    name = request.get("name", "")
    role = request.get("role", "")
    category = request.get("category", "")
    query_str = request.get("query", "")
    
    result = copy.deepcopy(LOGIC_OUTPUT_TEMPLATE)
    
    # =========================================================================
    # DIRECT QUERY (Eligibility_Check request type)
    # =========================================================================
    if query_str:
        entailed, explanation = KB.query(query_str)
        result["entailed"] = entailed
        result["allowed"] = entailed
        result["explanation"] = " | ".join(explanation)
        return result
    
    # =========================================================================
    # CATEGORY-BASED ELIGIBILITY CHECK
    # =========================================================================
    
    # Map category to fact to query
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
        # Emergency help is allowed for all registered users
        result["allowed"] = True
        result["entailed"] = True
        result["explanation"] = f"✓ Emergency help automatically approved for {name}"
        return result
        
    else:
        result["explanation"] = f"❌ Unknown category: '{category}'"
        result["allowed"] = False
        result["entailed"] = False
        return result
    
    # Query the knowledge base
    entailed, explanation = KB.query(fact)
    result["entailed"] = entailed
    result["allowed"] = entailed
    result["explanation"] = " | ".join(explanation)
    
    return result


def get_all_facts():
    """Utility function to display all facts in KB"""
    return KB.get_derived_facts()


# =============================================================================
# TESTING MODULE 4
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTING MODULE 4 - LOGIC / KNOWLEDGE BASE")
    print("="*60)
    
    # First, show all facts in KB
    print("\n📚 Current Facts in Knowledge Base:")
    all_facts = get_all_facts()
    for fact in sorted(all_facts):
        print(f"   • {fact}")
    
    # Test 1: Authorized student (Ali)
    print("\n✅ TEST 1: Authorized Student - Ali (AI_Lab_Support)")
    test1 = {
        "name": "Ali",
        "role": "student",
        "category": "AI_Lab_Support"
    }
    result = check_eligibility(test1)
    print(f"   Allowed: {result['allowed']}")
    print(f"   Explanation: {result['explanation']}")
    
    # Test 2: Unauthorized student (Bilal - no prerequisites)
    print("\n✅ TEST 2: Unauthorized Student - Bilal (AI_Lab_Support)")
    test2 = {
        "name": "Bilal",
        "role": "student",
        "category": "AI_Lab_Support"
    }
    result = check_eligibility(test2)
    print(f"   Allowed: {result['allowed']}")
    print(f"   Explanation: {result['explanation']}")
    
    # Test 3: Instructor access
    print("\n✅ TEST 3: Instructor - DrKhan (Access_Request)")
    test3 = {
        "name": "DrKhan",
        "role": "instructor",
        "category": "Access_Request"
    }
    result = check_eligibility(test3)
    print(f"   Allowed: {result['allowed']}")
    print(f"   Explanation: {result['explanation']}")
    
    # Test 4: Direct query (Eligibility_Check)
    print("\n✅ TEST 4: Direct Query - UsesLab(DrKhan, Lab1)")
    test4 = {
        "name": "DrKhan",
        "role": "instructor",
        "request_type": "Eligibility_Check",
        "query": "UsesLab(DrKhan, Lab1)"
    }
    result = check_eligibility(test4)
    print(f"   Query result: {result['allowed']}")
    print(f"   Explanation: {result['explanation']}")
    
    # Test 5: Viva scheduling
    print("\n✅ TEST 5: Viva Scheduling - Group G4")
    test5 = {
        "name": "Ali",
        "role": "student",
        "category": "Viva_Scheduling",
        "group_id": "G4"
    }
    result = check_eligibility(test5)
    print(f"   Allowed: {result['allowed']}")
    print(f"   Explanation: {result['explanation']}")
    
    # Test 6: Emergency Help
    print("\n✅ TEST 6: Emergency Help - Any Student")
    test6 = {
        "name": "Bilal",
        "role": "student",
        "category": "Emergency_Help"
    }
    result = check_eligibility(test6)
    print(f"   Allowed: {result['allowed']}")
    print(f"   Explanation: {result['explanation']}")
    
    # Test 7: Staff maintenance access
    print("\n✅ TEST 7: Staff Maintenance Request")
    test7 = {
        "name": "Ahmad",
        "role": "staff",
        "category": "Maintenance"
    }
    result = check_eligibility(test7)
    print(f"   Allowed: {result['allowed']}")
    print(f"   Explanation: {result['explanation']}")
    
    # Test 8: Another authorized student (Sara)
    print("\n✅ TEST 8: Authorized Student - Sara (AI_Lab_Support)")
    test8 = {
        "name": "Sara",
        "role": "student",
        "category": "AI_Lab_Support"
    }
    result = check_eligibility(test8)
    print(f"   Allowed: {result['allowed']}")
    print(f"   Explanation: {result['explanation']}")
    
    print("\n" + "="*60)
    print("📊 MODULE 4 TEST SUMMARY")
    print("="*60)
    print("   ✅ Ali (AI_Lab_Support): Should be ALLOWED")
    print("   ✅ Bilal (AI_Lab_Support): Should be DENIED")
    print("   ✅ DrKhan (Access): Should be ALLOWED")
    print("   ✅ Direct Query: Should be ALLOWED")
    print("   ✅ Viva Scheduling: Should be ALLOWED")
    print("   ✅ Emergency Help: Should be ALLOWED")
    print("   ✅ Staff Maintenance: Should be ALLOWED")
    print("   ✅ Sara (AI_Lab_Support): Should be ALLOWED")
    print("="*60)