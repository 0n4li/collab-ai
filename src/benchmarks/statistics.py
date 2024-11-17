def update_summary(summary, subject, results):
    """
    Generate summary statistics for model predictions and save to file.
    Creates both subject-specific and overall summaries.
    
    Args:
        summary (dict): Dictionary containing summary data
        subject (str): Subject identifier
        results (dict): Dictionary of prediction results
        
    Raises:
        ValueError: If input parameters are invalid
        KeyError: If required keys are missing in results
    """
    if not isinstance(summary, dict):
        raise ValueError("Summary must be a dictionary")
    if not isinstance(subject, str) or not subject:
        raise ValueError("Subject must be a non-empty string")
    if not isinstance(results, dict):
        raise ValueError("Results must be a dictionary")
        
    # Initialize statistics dictionaries with deep copies
    stats = {"corr": 0, "na": 0, "wrong": 0, "total": 0, "acc": 0.0}
    model_stats = {
        "final": dict(stats),
        "init": dict(stats)
    }
    model1 = {k: dict(v) for k, v in model_stats.items()}
    model2 = {k: dict(v) for k, v in model_stats.items()}
    agreement = {
        "final": {"agree": 0, "disagree": 0},
        "init": {"agree": 0, "disagree": 0}
    }
    
    # Process results for current subject
    for result_id, result in results.items():
        if not isinstance(result, dict):
            print(f"Skipping invalid result for {result_id}")
            continue
            
        # Process final predictions
        if result.get("pred") is not None:
            pred1, pred2 = result["pred"]
            answer = result.get("answer")
            
            # Only count agreement when both predictions are valid
            if pred1 is not None and pred2 is not None:
                if pred1 == pred2:
                    agreement["final"]["agree"] += 1
                else:
                    agreement["final"]["disagree"] += 1
            
            # Update correctness counters
            if pred1 == answer and pred2 == answer:
                stats["corr"] += 1
            elif pred1 is None or pred2 is None:
                stats["na"] += 1
            else:
                stats["wrong"] += 1
                
            # Update model-specific stats
            update_model_stats(model1["final"], pred1, answer)
            update_model_stats(model2["final"], pred2, answer)
        
        # Process initial predictions similarly
        if result.get("init_pred") is not None:
            init_pred1, init_pred2 = result["init_pred"]
            answer = result.get("answer")
            
            if init_pred1 is not None and init_pred2 is not None:
                if init_pred1 == init_pred2:
                    agreement["init"]["agree"] += 1
                else:
                    agreement["init"]["disagree"] += 1
            
            update_model_stats(model1["init"], init_pred1, answer)
            update_model_stats(model2["init"], init_pred2, answer)
    
    # Calculate accuracies
    stats["total"] = stats["corr"] + stats["na"] + stats["wrong"]
    stats["acc"] = calculate_accuracy(stats["corr"], stats["total"])
    
    for model in [model1, model2]:
        for phase in ["final", "init"]:
            phase_stats = model[phase]
            phase_stats["total"] = phase_stats["corr"] + phase_stats["na"] + phase_stats["wrong"]
            phase_stats["acc"] = calculate_accuracy(phase_stats["corr"], phase_stats["total"])
    
    # Create subject summary
    subject_summary = {
        **stats,
        "agreement": agreement,
        "model1": model1,
        "model2": model2
    }
    
    # Update summary with new subject data
    summary[subject] = subject_summary
    
    # Calculate overall statistics
    calculate_overall_statistics(summary)
    

def update_model_stats(stats, pred, answer):
    """Helper function to update model statistics."""
    if pred == answer:
        stats["corr"] += 1
    elif pred is None:
        stats["na"] += 1
    else:
        stats["wrong"] += 1

def calculate_accuracy(correct, total):
    """Helper function to calculate accuracy."""
    return 0.0 if total == 0 else correct / total

def calculate_overall_statistics(summary):
    """Calculate overall statistics across all subjects."""
    overall = {
        "corr": 0, "na": 0, "wrong": 0, "total": 0, "acc": 0.0,
        "model1": {"final": dict(), "init": dict()},
        "model2": {"final": dict(), "init": dict()},
        "agreement": {"final": {"agree": 0, "disagree": 0}, 
                     "init": {"agree": 0, "disagree": 0}}
    }
    
    for subj, stats in summary.items():
        if subj == "overall":
            continue
            
        overall["corr"] += stats["corr"]
        overall["na"] += stats["na"]
        overall["wrong"] += stats["wrong"]
        
        for model_key in ["model1", "model2"]:
            for phase in ["final", "init"]:
                for stat_key in ["corr", "na", "wrong"]:
                    overall[model_key][phase][stat_key] = (
                        overall[model_key][phase].get(stat_key, 0) +
                        stats[model_key][phase][stat_key]
                    )
        
        for phase in ["final", "init"]:
            overall["agreement"][phase]["agree"] += stats["agreement"][phase]["agree"]
            overall["agreement"][phase]["disagree"] += stats["agreement"][phase]["disagree"]
    
    # Calculate overall accuracies
    overall["total"] = overall["corr"] + overall["na"] + overall["wrong"]
    overall["acc"] = calculate_accuracy(overall["corr"], overall["total"])
    
    for model_key in ["model1", "model2"]:
        for phase in ["final", "init"]:
            phase_stats = overall[model_key][phase]
            phase_stats["total"] = (
                phase_stats.get("corr", 0) + 
                phase_stats.get("na", 0) + 
                phase_stats.get("wrong", 0)
            )
            phase_stats["acc"] = calculate_accuracy(
                phase_stats.get("corr", 0), 
                phase_stats["total"]
            )
    
    summary["overall"] = overall