"""Route SWCLK through the gap between the MCU and BOOT0 resistor."""

from pathlib import Path

import pcbnew as pcb

path = Path("hardware/ir_glasses/EVT_E/ir_glasses.kicad_pcb")
board = pcb.LoadBoard(str(path))
remove = {
    "186ec595-f2b9-425f-9644-fbb2fc1bb9ad",
    "2a9db434-e103-4dee-a13b-2a884fd261c3",
    "802a282c-324a-4c6e-bf6e-072b659e3a3b",
    "c0777acc-4830-49ff-8f07-8a9bf4935591",
    "d79ce4f0-f976-42da-aa51-aae6a4df24c4",
}
for track in list(board.GetTracks()):
    if track.m_Uuid.AsString() in remove:
        board.Remove(track)
points = [
    (114.1625, 60.25),
    (115.1, 60.25),
    (115.23, 60.38),
    (115.23, 60.9643),
    (115.8, 61.51),
]
for a, b in zip(points, points[1:]):
    track = pcb.PCB_TRACK(board)
    track.SetStart(pcb.VECTOR2I(*[pcb.FromMM(v) for v in a]))
    track.SetEnd(pcb.VECTOR2I(*[pcb.FromMM(v) for v in b]))
    track.SetWidth(pcb.FromMM(0.15))
    track.SetLayer(pcb.F_Cu)
    track.SetNet(board.FindNet("SWCLK_BOOT0"))
    board.Add(track)
pcb.SaveBoard(str(path), board)
