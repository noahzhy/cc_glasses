"""Clear the new connector anchor and refill EVT E1 copper."""

import pcbnew

path = "hardware/ir_glasses/EVT_E1/ir_glasses.kicad_pcb"
board = pcbnew.LoadBoard(path)
track = next(t for t in board.GetTracks()
             if t.m_Uuid.AsString() == "3fd39efc-982f-4d7c-b685-5ed4e59bc1c0")
net = track.GetNetCode()
board.Remove(track)
points = [(165.5, 61.4473), (165.5, 60.8),
          (163.1665, 58.4665), (162.5192, 58.4665)]
for start, end in zip(points, points[1:]):
    segment = pcbnew.PCB_TRACK(board)
    segment.SetStart(pcbnew.VECTOR2I(*[pcbnew.FromMM(v) for v in start]))
    segment.SetEnd(pcbnew.VECTOR2I(*[pcbnew.FromMM(v) for v in end]))
    segment.SetWidth(pcbnew.FromMM(0.15))
    segment.SetLayer(pcbnew.F_Cu)
    segment.SetNetCode(net)
    board.Add(segment)
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(path, board)
