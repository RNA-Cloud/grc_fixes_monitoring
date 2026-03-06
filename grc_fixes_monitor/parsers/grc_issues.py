from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class VersionMapped:
    acc: str
    version: str


@dataclass(frozen=True)
class Quality:
    versions_mapped: tuple[VersionMapped, ...]
    method_acc1: str
    method_acc2: str


@dataclass(frozen=True)
class Position:
    name: str
    gb_asm_acc: str
    ref_asm_acc: str
    asm_status: str
    map_status: str
    map_sequence: str
    map_seq_gb_acc: str
    map_seq_ref_acc: str
    map_seq_type: str
    start: str
    stop: str
    quality: Quality


@dataclass(frozen=True)
class Issue:
    type: str
    key: str
    assigned_chr: str
    accession1: str
    accession2: str
    report_type: str
    summary: str
    status: str
    status_text: str
    description: str
    experiment_type: str
    external_info_type: str
    update: str
    resolution: str
    resolution_text: str
    affect_version: str
    fix_version: str
    locations: tuple[Position, ...] = field(default_factory=tuple)

class GRCIssuesParser:
    """Parser for GRC fixes XML files."""

    def __init__(self, issues: dict[str, Issue]):
        self._issues = issues

    @classmethod
    def from_file(cls, xml_file: Path) -> GRCIssuesParser:
        try:
            tree = ET.parse(xml_file)
        except FileNotFoundError:
            raise FileNotFoundError(f"XML file not found: {xml_file}")
        except ET.ParseError as e:
            raise ValueError(f"Failed to parse XML file {xml_file}: {e}") from e

        root = tree.getroot()
        return cls(cls._build_index(
            cls._parse_issue(issue_el) for issue_el in root.findall("issue")
        ))

    @classmethod
    def from_directory(cls, data_dir: Path) -> GRCIssuesParser:
        if not data_dir.is_dir():
            raise NotADirectoryError(f"Not a directory: {data_dir}")

        merged: dict[str, Issue] = {}
        for xml_file in sorted(data_dir.glob("*.xml")):
            parser = cls.from_file(xml_file)
            duplicates = merged.keys() & parser._issues.keys()
            if duplicates:
                raise ValueError(f"Duplicate keys found in {xml_file.name}: {duplicates}")
            merged.update(parser._issues)

        return cls(merged)

    @staticmethod
    def _build_index(issues: Iterable[Issue]) -> dict[str, Issue]:
        index: dict[str, Issue] = {}
        for issue in issues:
            if issue.key is None:
                raise ValueError(f"Issue with no key encountered: {issue}")
            if issue.key in index:
                raise ValueError(f"Duplicate key found: {issue.key}")
            index[issue.key] = issue
        return index

    def get(self, key: str) -> Issue:
        return self._issues.get(key)

    def __len__(self) -> int:
        return len(self._issues)

    def __contains__(self, key: str) -> bool:
        return key in self._issues

    @staticmethod
    def _parse_issue(issue_el: ET.Element) -> Issue:
        def text(tag: str) -> str:
            el = issue_el.find(tag)
            return el.text if el is not None else None

        return Issue(
            type=text("type"),
            key=text("key"),
            assigned_chr=text("assignedChr"),
            accession1=text("accession1"),
            accession2=text("accession2"),
            report_type=text("reportType"),
            summary=text("summary"),
            status=text("status"),
            status_text=text("status_text"),
            description=text("description"),
            experiment_type=text("experiment_type"),
            external_info_type=text("external_info_type"),
            update=text("update"),
            resolution=text("resolution"),
            resolution_text=text("resolution_text"),
            affect_version=text("affectVersion"),
            fix_version=text("fixVersion"),
            locations=tuple(GRCIssuesParser._parse_locations(issue_el)),
        )

    @staticmethod
    def _parse_locations(issue_el: ET.Element) -> list[Position]:
        return [
            GRCIssuesParser._parse_position(pos)
            for pos in issue_el.findall("location/position")
        ]

    @staticmethod
    def _parse_position(pos: ET.Element) -> Position:
        map_seq_el = pos.find("mapSequence")
        quality_el = pos.find("quality")

        return Position(
            name=pos.get("name"),
            gb_asm_acc=pos.get("gb_asm_acc"),
            ref_asm_acc=pos.get("ref_asm_acc"),
            asm_status=pos.get("asm_status"),
            map_status=pos.findtext("mapStatus"),
            map_sequence=map_seq_el.text if map_seq_el is not None else None,
            map_seq_gb_acc=map_seq_el.get("gb_acc") if map_seq_el is not None else None,
            map_seq_ref_acc=map_seq_el.get("ref_acc") if map_seq_el is not None else None,
            map_seq_type=map_seq_el.get("type") if map_seq_el is not None else None,
            start=pos.findtext("start"),
            stop=pos.findtext("stop"),
            quality=GRCIssuesParser._parse_quality(quality_el) if quality_el is not None else None,
        )

    @staticmethod
    def _parse_quality(quality_el: ET.Element) -> Quality:
        return Quality(
            versions_mapped=tuple(
                VersionMapped(acc=vm.get("acc"), version=vm.text)
                for vm in quality_el.findall("version_mapped")
            ),
            method_acc1=quality_el.findtext("method_acc1"),
            method_acc2=quality_el.findtext("method_acc2"),
        )