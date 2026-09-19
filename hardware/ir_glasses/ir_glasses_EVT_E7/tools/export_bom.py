"""Export detailed and grouped BOMs using reviewed catalog metadata."""

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def export_bom():
    catalog = json.loads(
        (ROOT / "review/bom_catalog.json").read_text(encoding="utf-8")
    )
    with (ROOT / "BOM.csv").open(encoding="utf-8-sig") as source:
        rows = list(csv.DictReader(source))
    groups = defaultdict(list)
    for row in rows:
        item = catalog[row["LCSC"]]
        assert row["MPN"] == item["MPN"], row["Reference"]
        row["Parameters"] = item["Parameters"]
        row["Catalog_URL"] = item["Source"]
        groups[(row["MPN"], row["LCSC"], row["Footprint"])].append(row)
    with (ROOT / "BOM.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as target:
        writer = csv.DictWriter(target, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (ROOT / "BOM_采购汇总.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as target:
        writer = csv.writer(target)
        writer.writerow(
            [
                "位号",
                "单板数量",
                "简要参数",
                "封装",
                "制造商",
                "型号",
                "立创商城编码",
                "商品链接",
            ]
        )
        for (_, code, footprint), group in sorted(groups.items()):
            row = group[0]
            refs = sorted(
                (r["Reference"] for r in group),
                key=lambda r: (
                    re.sub(r"\d", "", r),
                    int(re.search(r"\d+", r)[0]),
                ),
            )
            writer.writerow(
                [
                    ", ".join(refs),
                    sum(int(r["Quantity"]) for r in group),
                    row["Parameters"],
                    footprint,
                    row["Manufacturer"],
                    row["MPN"],
                    code,
                    row["Catalog_URL"],
                ]
            )


if __name__ == "__main__":
    export_bom()
