"""Check reference-layer routes against the analogue circuit projection."""

import json
from pathlib import Path
from shapely.geometry import LineString, Point, Polygon

ROOT = Path(__file__).resolve().parents[1]


def is_analog(net):
    return net.startswith(
        ("/PD_IN", "/TIA", "/ADC", "/DRIVE", "/VREF")
    ) or net in {
        "VREF_1V65",
        "3V3_A",
        "/MUX_A",
        "/MUX_B",
        "/IREF",
        "/OV_SENSE",
        "/INPUT_ILIM",
        "/ILIM_SET",
        "/PULSE_RC",
        "/PULSE_C",
    }


def copper(item):
    if item["kind"] == "pad":
        return Polygon(item["coords"])
    if item["kind"] == "via":
        return Point(item["a"]).buffer(item["width"] / 2)
    return LineString([item["a"], item["b"]]).buffer(item["width"] / 2)


def check_reference():
    rows = json.loads((ROOT / "review/route_geometry.json").read_text())
    reference = [
        r
        for r in rows
        if r["kind"] == "track" and r["layers"] == [1] and r["net"] != "GND"
    ]
    analog = [(r, copper(r)) for r in rows if is_analog(r["net"])]
    violations = []
    nearest = None
    for item in reference:
        shape = copper(item)
        if is_analog(item["net"]):
            violations.append(
                {"uuid": item["uuid"], "reason": "Analog on In1"}
            )
        for other, area in analog:
            gap = shape.distance(area)
            if nearest is None or gap < nearest["copper_gap_mm"]:
                nearest = dict(
                    copper_gap_mm=gap,
                    reference_net=item["net"],
                    analog_net=other["net"],
                )
            if gap < 0.3 - 1e-6:
                violations.append(
                    dict(
                        reference_uuid=item["uuid"],
                        analog_uuid=other["uuid"],
                        gap_mm=gap,
                    )
                )
    return dict(
        signal_segments_on_in1=len(reference),
        required_projected_copper_gap_mm=0.3,
        ground_zone_clearance_mm=0.2,
        nearest=nearest,
        violations=violations,
    )


if __name__ == "__main__":
    result = check_reference()
    print(json.dumps(result, indent=2))
    assert not result["violations"]
