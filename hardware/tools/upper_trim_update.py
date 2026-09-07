from pathlib import Path
p=Path('hardware/tools/upper_trim_probe.py'); s=p.read_text(); a=s.index('for ident in'); b=s.index(':\n',a); s=s[:a]+"for ident in ['3d7c7ae0-bb16-463a-9c9f-5aaa19026970','cce4010c-d627-4378-bfde-f2138a8a3382','740a7508-31a1-49bd-987b-ff933b8f3a43']"+s[b:]; p.write_text(s)
