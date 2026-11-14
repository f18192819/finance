from .technical import technical_features
from .structure import structure_features
from .zones import zone_features


def compute_features(bars, parameters):
    frame = technical_features(bars, parameters)
    frame, pivots = structure_features(frame, parameters)
    internal_parameters = dict(parameters, pivot_left=parameters.get("internal_left", 2), pivot_right=parameters.get("internal_right", 2))
    internal, _ = structure_features(frame, internal_parameters)
    frame["internal_event"] = internal["structure_event"]
    frame["internal_direction"] = internal["structure_direction"]
    frame, zones = zone_features(frame, parameters)
    return frame, pivots, zones
