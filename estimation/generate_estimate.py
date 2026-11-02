#!/usr/bin/env python3
"""Render a Lightning Kite estimate JSON file as Markdown or an Excel workbook.

Usage: python3 generate_estimate.py <estimate.json> [output] [--format md|xlsx]

The format defaults to the output's suffix, or md, and the output defaults to the
input path with the format's suffix. An xlsx output needs openpyxl and uses live
formulas driven by the rate and multiplier on its Summary sheet. See SKILL.md in this directory for the JSON format.
"""
import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_RATE = 150
DEFAULT_MULTIPLIER = 4

# Optional top-level bullet lists, rendered in this order after the estimate tables
NOTE_LISTS = (
    ("assumptions", "Assumptions"),
    ("not_included", "Not Included"),
    ("challenges", "Challenges"),
    ("open_questions", "Open Questions"),
)

TOP_KEYS = {"title", "metadata", "rate", "hackathon_multiplier", "sections"} | {k for k, _ in NOTE_LISTS}
SECTION_KEYS = {"title", "description", "optional", "items", "groups"}
GROUP_KEYS = {"title", "summary_title", "description", "optional", "items"}
ITEM_KEYS = {"item", "hackathon_hours", "justification"}


class EstimateError(ValueError):
    pass


@dataclass
class Item:
    name: str
    hackathon_hours: float
    justification: str


@dataclass
class Group:
    title: str
    summary_title: str
    description: str
    optional: bool
    heading_optional: bool
    items: list
    implicit: bool

    @property
    def hackathon_hours(self):
        return sum(i.hackathon_hours for i in self.items)


@dataclass
class Section:
    title: str
    description: str
    optional: bool
    groups: list


# --- Parsing and validation


def check_keys(obj, allowed, where):
    if not isinstance(obj, dict):
        raise EstimateError(f"{where}: expected an object")
    unknown = set(obj) - allowed
    if unknown:
        raise EstimateError(f"{where}: unknown key(s) {', '.join(sorted(unknown))}")


def require_str(obj, key, where):
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        raise EstimateError(f"{where}: '{key}' must be a non-empty string")
    return value


def parse_items(raw, where):
    if not isinstance(raw, list) or not raw:
        raise EstimateError(f"{where}: 'items' must be a non-empty list")
    items = []
    for n, obj in enumerate(raw):
        at = f"{where} item {n + 1}"
        check_keys(obj, ITEM_KEYS, at)
        name = require_str(obj, "item", at)
        h = obj.get("hackathon_hours")
        if isinstance(h, bool) or not isinstance(h, (int, float)) or h < 0:
            raise EstimateError(f"{at} ({name}): 'hackathon_hours' must be a non-negative number")
        items.append(Item(name, h, obj.get("justification", "")))
    return items


def parse_section(obj, n):
    where = f"section {n + 1}"
    check_keys(obj, SECTION_KEYS, where)
    title = require_str(obj, "title", where)
    where = f"section '{title}'"
    optional = obj.get("optional", False)
    if ("items" in obj) == ("groups" in obj):
        raise EstimateError(f"{where}: needs exactly one of 'items' or 'groups'")

    if "items" in obj:
        # A section without groups is its own single, untitled group
        group = Group(title, title, "", optional, False, parse_items(obj["items"], where), implicit=True)
        return Section(title, obj.get("description", ""), optional, [group])

    if not isinstance(obj["groups"], list) or not obj["groups"]:
        raise EstimateError(f"{where}: 'groups' must be a non-empty list")
    groups = []
    for g in obj["groups"]:
        check_keys(g, GROUP_KEYS, where + " group")
        g_title = require_str(g, "title", where + " group")
        g_optional = g.get("optional", optional)
        groups.append(Group(
            title=g_title,
            summary_title=g.get("summary_title", f"{title} ({g_title})"),
            description=g.get("description", ""),
            optional=g_optional,
            # Only flag a group heading when it differs from its section's
            heading_optional=g_optional and not optional,
            items=parse_items(g.get("items"), f"{where} group '{g_title}'"),
            implicit=False,
        ))
    return Section(title, obj.get("description", ""), optional, groups)


class Estimate:
    def __init__(self, data):
        check_keys(data, TOP_KEYS, "estimate")
        self.title = require_str(data, "title", "estimate")
        self.metadata = [(m["label"], m["value"]) for m in data.get("metadata", [])]
        self.rate = data.get("rate", DEFAULT_RATE)
        self.multiplier = data.get("hackathon_multiplier", DEFAULT_MULTIPLIER)
        if not data.get("sections"):
            raise EstimateError("estimate: 'sections' must be a non-empty list")
        self.sections = [parse_section(s, n) for n, s in enumerate(data["sections"])]
        self.notes = [(heading, data[key]) for key, heading in NOTE_LISTS if data.get(key)]

    def groups(self):
        return [g for s in self.sections for g in s.groups]

    def base_groups(self):
        return [g for g in self.groups() if not g.optional]

    def optional_groups(self):
        return [g for g in self.groups() if g.optional]

    def dev_hours(self, hackathon_hours):
        return hackathon_hours * self.multiplier

    def cost(self, hackathon_hours):
        return self.dev_hours(hackathon_hours) * self.rate


# --- Markdown


def fmt_hours(value):
    return f"{value:g}"


def fmt_money(value):
    return f"${value:,.0f}"


def optional_label(title, optional):
    return f"{title} (Optional)" if optional else title


def md_table(headers, rows, align):
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---:" if a == "r" else "---" for a in align) + "|",
    ]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return lines


def render_markdown(est):
    def totals(h):
        return [fmt_hours(h), fmt_hours(est.dev_hours(h)), fmt_money(est.cost(h))]

    def summary_row(title, h, bold=False):
        cells = [title] + totals(h)
        return [f"**{c}**" for c in cells] if bold else cells

    out = [f"# {est.title}", ""]
    out += [f"**{label}:** {value}  " for label, value in est.metadata]
    out += [f"**Method:** Hackathon hours × {fmt_hours(est.multiplier)} = dev hours "
            f"(hackathon, polish, feedback, QA) at {fmt_money(est.rate)}/hour", ""]

    # Summary
    optional = est.optional_groups()
    base = sum(g.hackathon_hours for g in est.base_groups())
    rows = [summary_row(g.summary_title, g.hackathon_hours) for g in est.base_groups()]
    rows.append(summary_row("Base Total" if optional else "Total", base, bold=True))
    out += ["## Summary", ""]
    out += md_table(["Category", "Hackathon Hours", "Dev Hours", "Cost"], rows, "lrrr") + [""]

    if optional:
        all_optional = sum(g.hackathon_hours for g in optional)
        rows = [summary_row(g.summary_title, g.hackathon_hours) + [fmt_money(est.cost(base + g.hackathon_hours))]
                for g in optional]
        rows.append(summary_row("All Optional Features", all_optional, bold=True) + [""])
        rows.append(summary_row("Total with All Optional Features", base + all_optional, bold=True) + [""])
        out += ["### Optional Features", "",
                "Not included in the base total. \"Base + Option\" is the total cost "
                "if only that option is added.", ""]
        out += md_table(["Option", "Hackathon Hours", "Dev Hours", "Cost", "Base + Option"], rows, "lrrrr") + [""]

    # Item tables
    for section in est.sections:
        out += [f"## {optional_label(section.title, section.optional)}", ""]
        if section.description:
            out += [section.description, ""]
        for group in section.groups:
            if not group.implicit:
                out += [f"### {optional_label(group.title, group.heading_optional)}", ""]
                if group.description:
                    out += [group.description, ""]
            rows = [[i.name, fmt_hours(i.hackathon_hours), i.justification,
                     fmt_hours(est.dev_hours(i.hackathon_hours)), fmt_money(est.cost(i.hackathon_hours))]
                    for i in group.items]
            h = group.hackathon_hours
            rows.append(["**Subtotal**", f"**{fmt_hours(h)}**", "",
                         f"**{fmt_hours(est.dev_hours(h))}**", f"**{fmt_money(est.cost(h))}**"])
            out += md_table(["Item", "Hackathon Hours", "Justification", "Dev Hours", "Cost"], rows, "lrlrr") + [""]

    for heading, lines in est.notes:
        out += [f"## {heading}", ""] + [f"- {line}" for line in lines] + [""]

    return "\n".join(out).rstrip() + "\n"


# --- Excel


def write_xlsx(est, dst):
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font, PatternFill
    except ImportError:
        sys.exit("Excel output requires openpyxl: pip install openpyxl")

    bold = Font(bold=True)
    heading_font = Font(bold=True, size=12)
    head_fill = PatternFill("solid", fgColor="D9E1F2")
    section_fill = PatternFill("solid", fgColor="B4C6E7")
    money_fmt = '"$"#,##0'
    hours_fmt = "0.##"

    wb = Workbook()
    summary = wb.active
    summary.title = "Summary"
    items_ws = wb.create_sheet("Estimate")

    def header(ws, row, labels):
        for col, label in enumerate(labels, 1):
            c = ws.cell(row, col, label)
            c.font, c.fill = bold, head_fill
            c.alignment = Alignment(horizontal="left" if col == 1 else "center",
                                    vertical="center", wrap_text=True)

    # Rate and multiplier are the only inputs; every other number is a formula over them
    summary["A1"] = est.title
    summary["A1"].font = Font(bold=True, size=14)
    r = 2
    for label, value in est.metadata:
        summary.cell(r, 1, label).font = bold
        summary.cell(r, 2, value)
        r += 1
    rate_row, mult_row = r + 1, r + 2
    summary.cell(rate_row, 1, "Rate ($/hour)").font = bold
    summary.cell(rate_row, 2, est.rate).number_format = money_fmt
    summary.cell(mult_row, 1, "Hackathon multiplier").font = bold
    summary.cell(mult_row, 2, est.multiplier)
    rate = f"Summary!$B${rate_row}"
    mult = f"Summary!$B${mult_row}"

    # Estimate sheet: one block per group, remembering each subtotal row
    subtotal_row = {}
    row = 1
    for section in est.sections:
        items_ws.cell(row, 1, optional_label(section.title, section.optional)).font = heading_font
        for col in range(1, 6):
            items_ws.cell(row, col).fill = section_fill
        row += 1
        if section.description:
            items_ws.cell(row, 1, section.description)
            row += 1
        for group in section.groups:
            if not group.implicit:
                items_ws.cell(row, 1, optional_label(group.title, group.heading_optional)).font = bold
                row += 1
                if group.description:
                    items_ws.cell(row, 1, group.description)
                    row += 1
            header(items_ws, row, ["Item", "Hackathon Hours", "Justification", "Dev Hours", "Cost"])
            row += 1
            first = row
            for item in group.items:
                items_ws.cell(row, 1, item.name)
                items_ws.cell(row, 2, item.hackathon_hours).number_format = hours_fmt
                items_ws.cell(row, 3, item.justification).alignment = Alignment(wrap_text=True, vertical="top")
                items_ws.cell(row, 4, f"=B{row}*{mult}").number_format = hours_fmt
                items_ws.cell(row, 5, f"=D{row}*{rate}").number_format = money_fmt
                row += 1
            items_ws.cell(row, 1, "Subtotal").font = bold
            items_ws.cell(row, 2, f"=SUM(B{first}:B{row - 1})").number_format = hours_fmt
            items_ws.cell(row, 4, f"=B{row}*{mult}").number_format = hours_fmt
            items_ws.cell(row, 5, f"=D{row}*{rate}").number_format = money_fmt
            for col in (2, 4, 5):
                items_ws.cell(row, col).font = bold
            subtotal_row[id(group)] = row
            row += 2
    for col, width in zip("ABCDE", (48, 16, 70, 12, 12)):
        items_ws.column_dimensions[col].width = width

    def summary_line(r, title, hours_formula, is_bold=False):
        summary.cell(r, 1, title)
        summary.cell(r, 2, hours_formula).number_format = hours_fmt
        summary.cell(r, 3, f"=B{r}*$B${mult_row}").number_format = hours_fmt
        summary.cell(r, 4, f"=C{r}*$B${rate_row}").number_format = money_fmt
        if is_bold:
            for col in range(1, 6):
                summary.cell(r, col).font = bold

    r = mult_row + 2
    summary.cell(r, 1, "Summary").font = heading_font
    header(summary, r + 1, ["Category", "Hackathon Hours", "Dev Hours", "Cost"])
    r += 2
    first = r
    for group in est.base_groups():
        summary_line(r, group.summary_title, f"=Estimate!B{subtotal_row[id(group)]}")
        r += 1
    optional = est.optional_groups()
    base_row = r
    summary_line(r, "Base Total" if optional else "Total",
                 f"=SUM(B{first}:B{r - 1})" if r > first else 0, is_bold=True)

    if optional:
        r += 2
        summary.cell(r, 1, "Optional Features").font = heading_font
        summary.cell(r + 1, 1, "Not included in the base total. \"Base + Option\" is the total cost "
                               "if only that option is added.")
        header(summary, r + 2, ["Option", "Hackathon Hours", "Dev Hours", "Cost", "Base + Option"])
        r += 3
        first = r
        for group in optional:
            summary_line(r, group.summary_title, f"=Estimate!B{subtotal_row[id(group)]}")
            summary.cell(r, 5, f"=(B{base_row}+B{r})*$B${mult_row}*$B${rate_row}").number_format = money_fmt
            r += 1
        summary_line(r, "All Optional Features", f"=SUM(B{first}:B{r - 1})", is_bold=True)
        summary_line(r + 1, "Total with All Optional Features", f"=B{base_row}+B{r}", is_bold=True)
    for col, width in zip("ABCDE", (48, 16, 12, 12, 14)):
        summary.column_dimensions[col].width = width

    if est.notes:
        notes = wb.create_sheet("Notes")
        n = 1
        for heading, lines in est.notes:
            notes.cell(n, 1, heading).font = heading_font
            for line in lines:
                n += 1
                notes.cell(n, 1, f"• {line}")
            n += 2
        notes.column_dimensions["A"].width = 100

    centered = Alignment(horizontal="center", vertical="center")
    for ws in wb.worksheets:
        for ws_row in ws.iter_rows():
            for c in ws_row:
                if isinstance(c.value, (int, float)) or (isinstance(c.value, str) and c.value.startswith("=")):
                    c.alignment = centered

    wb.save(dst)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("src", type=Path)
    parser.add_argument("dst", type=Path, nargs="?")
    parser.add_argument("--format", choices=("md", "xlsx"))
    args = parser.parse_args()
    src = args.src
    fmt = args.format or ("xlsx" if args.dst and args.dst.suffix.lower() == ".xlsx" else "md")
    dst = args.dst or src.with_suffix("." + fmt)
    try:
        est = Estimate(json.loads(src.read_text(encoding="utf-8")))
    except (EstimateError, json.JSONDecodeError) as e:
        sys.exit(f"{src}: {e}")
    if fmt == "xlsx":
        write_xlsx(est, dst)
    else:
        dst.write_text(render_markdown(est), encoding="utf-8")
    print(f"Wrote {dst}")


if __name__ == "__main__":
    main()
