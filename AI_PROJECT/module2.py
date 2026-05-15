import copy

ROUTER_OUTPUT_TEMPLATE = {
    "request_id": "",
    "selected_pipeline": [],
    "needs_ann": False,
    "needs_logic": False,
    "needs_csp": False,
    "needs_search": False
}

def route_request(request):
    """
    Determines the execution pipeline based on request_type.
    
    Args:
        request (dict): Preprocessed request object with 'request_type' field
        
    Returns:
        dict: Router output with pipeline flags and selected modules
        
    Raises:
        ValueError: If request_type is unknown or missing
    """
    # FIX 1: Handle missing request_type gracefully
    rt = request.get("request_type", "")
    
    if not rt:
        raise ValueError("Request missing 'request_type' field")
    
    router_output = copy.deepcopy(ROUTER_OUTPUT_TEMPLATE)
    router_output["request_id"] = request.get("request_id", "")
    
    # FIX 2: Use dictionary mapping for cleaner code (optional improvement)
    # But your if-elif structure is perfectly fine and readable
    
    if rt == "Navigation_Only":
        router_output["selected_pipeline"] = ["Search"]
        router_output["needs_search"] = True
        
    elif rt == "Eligibility_Check":
        router_output["selected_pipeline"] = ["Logic_KB"]
        router_output["needs_logic"] = True
        
    elif rt == "Booking_or_Scheduling":
        router_output["selected_pipeline"] = ["Logic_KB", "CSP", "Search (optional)"]
        router_output["needs_logic"] = True
        router_output["needs_csp"] = True
        router_output["needs_search"] = False  # Explicit is good
        
    elif rt == "Urgent_Service_Request":
        router_output["selected_pipeline"] = ["ANN", "Logic_KB", "CSP", "Search (optional)"]
        router_output["needs_ann"] = True
        router_output["needs_logic"] = True
        router_output["needs_csp"] = True
        router_output["needs_search"] = False
        
    elif rt == "Full_Service_Request":
        router_output["selected_pipeline"] = ["ANN", "Logic_KB", "CSP", "Search"]
        router_output["needs_ann"] = True
        router_output["needs_logic"] = True
        router_output["needs_csp"] = True
        router_output["needs_search"] = True
        
    else:
        raise ValueError(f"Unknown request_type: '{rt}'. Valid types: "
                        f"Navigation_Only, Eligibility_Check, Booking_or_Scheduling, "
                        f"Urgent_Service_Request, Full_Service_Request")
    
    return router_output


# =============================================================================
# ALTERNATIVE: Cleaner implementation using mapping (For FYP bonus points)
# =============================================================================

def route_request_v2(request):
    """
    Alternative implementation using configuration dictionary.
    More maintainable and shows design pattern knowledge.
    """
    rt = request.get("request_type", "")
    
    if not rt:
        raise ValueError("Request missing 'request_type' field")
    
    # Pipeline configuration per request type
    PIPELINE_CONFIG = {
        "Navigation_Only": {
            "selected_pipeline": ["Search"],
            "needs_ann": False,
            "needs_logic": False,
            "needs_csp": False,
            "needs_search": True
        },
        "Eligibility_Check": {
            "selected_pipeline": ["Logic_KB"],
            "needs_ann": False,
            "needs_logic": True,
            "needs_csp": False,
            "needs_search": False
        },
        "Booking_or_Scheduling": {
            "selected_pipeline": ["Logic_KB", "CSP", "Search (optional)"],
            "needs_ann": False,
            "needs_logic": True,
            "needs_csp": True,
            "needs_search": False
        },
        "Urgent_Service_Request": {
            "selected_pipeline": ["ANN", "Logic_KB", "CSP", "Search (optional)"],
            "needs_ann": True,
            "needs_logic": True,
            "needs_csp": True,
            "needs_search": False
        },
        "Full_Service_Request": {
            "selected_pipeline": ["ANN", "Logic_KB", "CSP", "Search"],
            "needs_ann": True,
            "needs_logic": True,
            "needs_csp": True,
            "needs_search": True
        }
    }
    
    if rt not in PIPELINE_CONFIG:
        raise ValueError(f"Unknown request_type: '{rt}'")
    
    router_output = copy.deepcopy(ROUTER_OUTPUT_TEMPLATE)
    router_output["request_id"] = request.get("request_id", "")
    router_output.update(PIPELINE_CONFIG[rt])
    
    return router_output


# =============================================================================
# TESTING MODULE 2
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTING MODULE 2 - REQUEST ROUTER")
    print("="*60)
    
    test_cases = [
        ("REQ001", "Navigation_Only"),
        ("REQ002", "Eligibility_Check"),
        ("REQ003", "Booking_or_Scheduling"),
        ("REQ004", "Urgent_Service_Request"),
        ("REQ005", "Full_Service_Request"),
    ]
    
    tests_passed = 0
    
    for req_id, req_type in test_cases:
        try:
            request = {"request_id": req_id, "request_type": req_type}
            result = route_request(request)
            
            print(f"\n✅ Testing: {req_type}")
            print(f"   Pipeline: {result['selected_pipeline']}")
            print(f"   Flags: ANN={result['needs_ann']}, Logic={result['needs_logic']}, "
                  f"CSP={result['needs_csp']}, Search={result['needs_search']}")
            
            # Verify correct flags based on request type
            if req_type == "Navigation_Only":
                assert result["needs_search"] == True
                assert result["needs_ann"] == False
                assert result["needs_logic"] == False
                assert result["needs_csp"] == False
                
            elif req_type == "Eligibility_Check":
                assert result["needs_logic"] == True
                assert result["needs_ann"] == False
                assert result["needs_csp"] == False
                assert result["needs_search"] == False
                
            elif req_type == "Booking_or_Scheduling":
                assert result["needs_logic"] == True
                assert result["needs_csp"] == True
                assert result["needs_ann"] == False
                
            elif req_type == "Urgent_Service_Request":
                assert result["needs_ann"] == True
                assert result["needs_logic"] == True
                assert result["needs_csp"] == True
                
            elif req_type == "Full_Service_Request":
                assert result["needs_ann"] == True
                assert result["needs_logic"] == True
                assert result["needs_csp"] == True
                assert result["needs_search"] == True
            
            tests_passed += 1
            
        except Exception as e:
            print(f"❌ Failed: {req_type} - {e}")
    
    # Test error handling
    print("\n✅ TEST: Unknown request type")
    try:
        bad_request = {"request_id": "REQ999", "request_type": "Invalid_Type"}
        result = route_request(bad_request)
        print("❌ Failed - Should have raised ValueError")
    except ValueError as e:
        print(f"✅ Passed - Correctly rejected: {e}")
        tests_passed += 1
    
    # Test missing request_type
    print("\n✅ TEST: Missing request_type")
    try:
        bad_request = {"request_id": "REQ999"}
        result = route_request(bad_request)
        print("❌ Failed - Should have raised error")
    except ValueError as e:
        print(f"✅ Passed - Correctly handled: {e}")
        tests_passed += 1
    
    print("\n" + "="*60)
    print(f"📊 TEST SUMMARY: {tests_passed}/7 tests passed")
    print("="*60)
    
    if tests_passed == 7:
        print("\n🎉 MODULE 2 IS FULLY FUNCTIONAL!")
        print("\n✅ Module 2 correctly:")
        print("   ✓ Routes all 5 request types")
        print("   ✓ Sets appropriate pipeline flags")
        print("   ✓ Handles errors gracefully")
        print("   ✓ Has no unwanted dependencies")