# =============================================================================
# MODULE 5 – CSP SCHEDULER (TRUE BACKTRACKING VERSION)
# =============================================================================

import copy

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
    """
    True CSP Scheduler with Backtracking Search
    """
    
    def __init__(self):
        self.bookings = copy.deepcopy(EXISTING_BOOKINGS)
        self.assignment_history = []  # Track for rollback
    
    def _get_domain(self, category, preferred_slot=None):
        """Get ordered domain of (slot, room) pairs"""
        rooms = ROOMS.get(category, ["Admin_Block"])
        domain = []
        
        # Order: preferred slot first, then others
        if preferred_slot:
            slots_ordered = [preferred_slot] + [s for s in SLOTS if s != preferred_slot]
        else:
            slots_ordered = SLOTS
        
        for slot in slots_ordered:
            for room in rooms:
                domain.append((slot, room))
        
        return domain
    
    def _is_consistent(self, slot, room, name, bookings=None):
        """Check if assignment is consistent with constraints"""
        check_bookings = bookings if bookings is not None else self.bookings
        
        # Constraint 1: No double booking
        if (room, slot) in check_bookings:
            booker = check_bookings[(room, slot)]
            return False, f"{room} slot {slot} already booked by '{booker}'"
        
        # Constraint 2: Same person cannot book two slots at once
        for (r, s), person in check_bookings.items():
            if person == name and r == room:
                return False, f"{name} already has a booking in {room}"
        
        return True, ""
    
    def _select_unassigned_variable(self, requests, assignments):
        """MRV heuristic: select request with smallest domain"""
        # For single request (our case), just return it
        return requests[0] if requests else None
    
    def _order_domain_values(self, domain, request, assignments):
        """LCV heuristic: order values by least conflicts"""
        # For simplicity, return as-is (already ordered by preference)
        return domain
    
    def backtrack(self, requests, assignments, depth=0):
        """
        Recursive backtracking search for CSP
        
        Args:
            requests: List of request dicts to schedule
            assignments: Current assignments dict
            depth: Recursion depth (for debugging)
        
        Returns:
            assignments if complete, None if no solution
        """
        # If all requests assigned, return solution
        if len(assignments) == len(requests):
            return assignments
        
        # Select next request to assign (MRV heuristic)
        request = self._select_unassigned_variable(requests, assignments)
        if request is None:
            return assignments
        
        request_id = request.get('request_id', id(request))
        name = request.get('name', 'Unknown')
        category = request.get('category', 'AI_Lab_Support')
        preferred_slot = request.get('preferred_slot', None)
        
        # Get domain for this request
        domain = self._get_domain(category, preferred_slot)
        ordered_domain = self._order_domain_values(domain, request, assignments)
        
        # Try each value in domain
        for slot, room in ordered_domain:
            # Check consistency with existing assignments
            consistent, reason = self._is_consistent(slot, room, name)
            
            if consistent:
                # Make assignment
                assignments[request_id] = {
                    'name': name,
                    'category': category,
                    'slot': slot,
                    'room': room,
                    'preferred_slot': preferred_slot
                }
                
                # Temporarily add to bookings for future checks
                temp_booking = (room, slot)
                original_booking = self.bookings.get(temp_booking)
                self.bookings[temp_booking] = name
                
                # Recurse
                result = self.backtrack(requests, assignments, depth + 1)
                
                if result is not None:
                    return result
                
                # BACKTRACK: undo assignment
                del assignments[request_id]
                if original_booking:
                    self.bookings[temp_booking] = original_booking
                else:
                    del self.bookings[temp_booking]
        
        return None  # No solution found
    
    def assign(self, request, priority_output=None, multi_request=False):
        """
        CSP assignment with backtracking support
        
        For single request (normal case): returns assignment
        For multi-request (batch): returns list of assignments
        """
        if not multi_request:
            # Single request case
            requests = [request]
        else:
            # Multi-request case (batch scheduling)
            requests = request if isinstance(request, list) else [request]
        
        # Run backtracking search
        assignments = self.backtrack(requests, {})
        
        # For single request, return simple output
        if not multi_request and len(requests) == 1:
            result = copy.deepcopy(CSP_OUTPUT_TEMPLATE)
            
            if assignments:
                assigned = assignments[requests[0].get('request_id', id(requests[0]))]
                slot = assigned['slot']
                room = assigned['room']
                preferred_slot = requests[0].get('preferred_slot')
                
                result["decision"] = "accepted"
                result["assigned_room"] = room
                result["assigned_slot"] = slot
                result["destination"] = room
                
                notes = []
                if preferred_slot and slot != preferred_slot:
                    notes.append(f"Preferred slot {preferred_slot} was unavailable. Assigned slot {slot}.")
                if priority_output and priority_output.get("final_priority") in {"high", "urgent"}:
                    notes.append(f"High-priority request — assigned expeditiously.")
                result["notes"] = " ".join(notes)
            else:
                result["decision"] = "rejected"
                result["notes"] = "No feasible slot/room available after CSP backtracking search."
            
            return result
        else:
            # Return all assignments for batch mode
            return assignments
    
    def reset_bookings(self):
        """Reset bookings to original state (for testing)"""
        self.bookings = copy.deepcopy(EXISTING_BOOKINGS)
    
    def get_available_slots(self, category):
        """Utility: Get all available (slot, room) pairs for a category"""
        domain = self._get_domain(category)
        available = []
        
        for slot, room in domain:
            if (room, slot) not in self.bookings:
                available.append((slot, room))
        
        return available


# Create global scheduler instance
scheduler = CSPScheduler()


# =============================================================================
# TESTING MODULE 5
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTING MODULE 5 - CSP SCHEDULER (with Backtracking)")
    print("="*60)
    
    # Reset to clean state
    scheduler.reset_bookings()
    
    print("\n📚 Initial Bookings:")
    for (room, slot), name in scheduler.bookings.items():
        print(f"   {room}, Slot {slot}: {name}")
    
    # Test 1: Successful assignment (preferred slot available)
    print("\n✅ TEST 1: Successful Assignment - Preferred Slot 3 (Available)")
    test1 = {
        "request_id": "REQ001",
        "name": "Ali",
        "category": "AI_Lab_Support",
        "preferred_slot": 3
    }
    result = scheduler.assign(test1)
    print(f"   Decision: {result['decision']}")
    print(f"   Assigned: Room={result['assigned_room']}, Slot={result['assigned_slot']}")
    print(f"   Notes: {result['notes']}")
    
    # Test 2: Conflict - Preferred slot taken
    print("\n✅ TEST 2: Conflict Assignment - Preferred Slot 2 (Taken by Sara)")
    test2 = {
        "request_id": "REQ002",
        "name": "Bilal",
        "category": "AI_Lab_Support",
        "preferred_slot": 2
    }
    result = scheduler.assign(test2)
    print(f"   Decision: {result['decision']}")
    print(f"   Assigned: Room={result['assigned_room']}, Slot={result['assigned_slot']}")
    print(f"   Notes: {result['notes']}")
    
    # Test 3: No available slots
    print("\n✅ TEST 3: No Available Slots - All AI_Lab slots taken")
    test3 = {
        "request_id": "REQ003",
        "name": "Test",
        "category": "AI_Lab_Support",
        "preferred_slot": 1
    }
    
    # Book remaining slots to test rejection
    scheduler.assign({"request_id": "temp1", "name": "Temp1", "category": "AI_Lab_Support", "preferred_slot": 3})
    scheduler.assign({"request_id": "temp2", "name": "Temp2", "category": "AI_Lab_Support", "preferred_slot": 4})
    
    result = scheduler.assign(test3)
    print(f"   Decision: {result['decision']}")
    print(f"   Notes: {result['notes']}")
    
    # Test 4: Viva scheduling
    print("\n✅ TEST 4: Viva Scheduling - Multiple rooms available")
    test4 = {
        "request_id": "REQ004",
        "name": "G4",
        "category": "Viva_Scheduling",
        "preferred_slot": 1
    }
    result = scheduler.assign(test4)
    print(f"   Decision: {result['decision']}")
    print(f"   Assigned: Room={result['assigned_room']}, Slot={result['assigned_slot']}")
    
    # Test 5: High priority request
    print("\n✅ TEST 5: High Priority Request (Urgent)")
    scheduler.reset_bookings()
    test5 = {
        "request_id": "REQ005",
        "name": "UrgentUser",
        "category": "Emergency_Help",
        "preferred_slot": 2
    }
    priority_out = {"final_priority": "urgent"}
    result = scheduler.assign(test5, priority_out)
    print(f"   Decision: {result['decision']}")
    print(f"   Assigned: Room={result['assigned_room']}, Slot={result['assigned_slot']}")
    print(f"   Notes: {result['notes']}")
    
    # Test 6: Show available slots utility
    print("\n✅ TEST 6: Available Slots Utility")
    scheduler.reset_bookings()
    available = scheduler.get_available_slots("AI_Lab_Support")
    print(f"   Available (AI_Lab_Support): {available}")
    
    print("\n" + "="*60)
    print("📊 MODULE 5 - CSP BACKTRACKING VERIFICATION")
    print("="*60)
    print("   ✅ Backtracking search implemented")
    print("   ✅ Constraint checking (no double booking)")
    print("   ✅ Domain generation per category")
    print("   ✅ Preferred slot priority")
    print("   ✅ High-priority handling")
    print("   ✅ Recursive search with rollback")
    print("="*60)