import copy

stats = {"corr": 0, "idk": 0, "na": 0, "wrong": 0, "total": 0, "acc": 0.0}
agreement_stats = { "agree": 0, "disagree": 0, "total": 0, "pct": 0.0 }

def _calculate_accuracy(correct, total):
    """Helper function to calculate accuracy."""
    return 0.0 if total == 0 else correct / total

def _update_prediction_totals(stats_dict):
    stats_dict["total"] = stats_dict["corr"] + stats_dict["idk"] + stats_dict["na"] + stats_dict["wrong"]
    stats_dict["acc"] = _calculate_accuracy(stats_dict["corr"], stats_dict["total"])


def _update_prediction_stats(stats_dict, answer, pred1, pred2=None):
    if pred2 == None:
        pred2 = pred1
    if pred1 == answer and pred2 == answer:
        stats_dict["corr"] += 1
    elif pred1 == "IDK" or pred2 == "IDK":
        stats_dict["idk"] += 1
    elif pred1 == "NA" or pred2 == "NA":
        stats_dict["na"] += 1
    else:
        stats_dict["wrong"] += 1
    _update_prediction_totals(stats_dict)
    
    
def _add_prediction_stats(overall_dict, stats_dict):
    overall_dict["corr"] += stats_dict.get("corr", 0)
    overall_dict["idk"] += stats_dict.get("idk", 0)
    overall_dict["na"] += stats_dict.get("na", 0)
    overall_dict["wrong"] += stats_dict.get("wrong", 0)
    _update_prediction_totals(overall_dict)
    
    
def _update_agreement_totals(agreement_dict):
    agreement_dict["total"] = agreement_dict["agree"] + agreement_dict["disagree"]
    agreement_dict["pct"] = agreement_dict["agree"] / agreement_dict["total"]


def _update_agreement_stats(agreement_dict, agreement):
    if agreement:
        agreement_dict["agree"] += 1
    else:
        agreement_dict["disagree"] += 1
    _update_agreement_totals(agreement_dict)
    

def _add_agreement_stats(overall_agreement_dict, subject_agreement_dict):
    overall_agreement_dict["agree"] += subject_agreement_dict.get("agree", 0)
    overall_agreement_dict["disagree"] += subject_agreement_dict.get("disagree", 0)
    _update_agreement_totals(overall_agreement_dict)
    

def _build_stats():
    global stats, agreement_stats
    stats_dict = copy.deepcopy(stats)
    model_stats = {
        "final": copy.deepcopy(stats),
        "init": copy.deepcopy(stats)
    }
    model1_stats = copy.deepcopy(model_stats)
    model2_stats = copy.deepcopy(model_stats)
    agreement = {
        "final": copy.deepcopy(agreement_stats),
        "init": copy.deepcopy(agreement_stats)
    }
    stats_dict["agreement"] = agreement
    stats_dict["model1"] = model1_stats
    stats_dict["model2"] = model2_stats
    return stats_dict


def calculate_subject_statistics(results):
    subject_stats = _build_stats()
    model1_stats = subject_stats["model1"]
    model2_stats = subject_stats["model2"]
    agreement = subject_stats["agreement"]
    
    for _, result in results.items():
        pred_tuple = result.get("pred")
        if pred_tuple is not None:
            pred1, pred2 = pred_tuple
            answer = result.get("answer")
            _update_prediction_stats(subject_stats, answer, pred1, pred2)
            _update_prediction_stats(model1_stats["final"], answer, pred1)
            _update_prediction_stats(model2_stats["final"], answer, pred2)
            _update_agreement_stats(agreement["final"], pred1 == pred2)
        
        init_pred_tuple = result.get("init_pred")
        if init_pred_tuple is not None:
            init_pred1, init_pred2 = init_pred_tuple
            answer = result.get("answer")
            _update_prediction_stats(model1_stats["init"], answer, init_pred1)
            _update_prediction_stats(model2_stats["init"], answer, init_pred2)
            _update_agreement_stats(agreement["init"], init_pred1 == init_pred2)

    return subject_stats

def calculate_all_statistics(summary):
    overall_stats = _build_stats()
    model1_stats = overall_stats["model1"]
    model2_stats = overall_stats["model2"]
    agreement = overall_stats["agreement"]
    
    for subject, subject_stats in summary.items():
        if subject == "overall":
            continue
        
        _add_prediction_stats(overall_stats, subject_stats)
        for phase in ["final", "init"]:
            _add_prediction_stats(model1_stats[phase], subject_stats["model1"][phase])
            _add_prediction_stats(model2_stats[phase], subject_stats["model2"][phase])
            _add_agreement_stats(agreement[phase], subject_stats["agreement"][phase])
    
    return overall_stats