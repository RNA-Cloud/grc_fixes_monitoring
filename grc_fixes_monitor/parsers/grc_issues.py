from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

logger = logging.getLogger(__name__)


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
        logger.info("Parsing GRC issues XML file: %s", xml_file)
        try:
            tree = ET.parse(xml_file)
        except FileNotFoundError:
            logger.error("XML file not found: %s", xml_file)
            raise FileNotFoundError(f"XML file not found: {xml_file}")
        except ET.ParseError as e:
            logger.error("Failed to parse XML file %s: %s", xml_file, e)
            raise ValueError(f"Failed to parse XML file {xml_file}: {e}") from e

        root = tree.getroot()
        issue_elements = root.findall("issue")
        logger.debug("Found %d <issue> elements in %s", len(issue_elements), xml_file)
        issues = cls._build_index(cls._parse_issue(issue_el) for issue_el in issue_elements)
        logger.info("Parsed %d issues from %s", len(issues), xml_file)
        return cls(issues)

    @classmethod
    def from_directory(cls, data_dir: Path) -> GRCIssuesParser:
        logger.info("Parsing GRC issues from directory: %s", data_dir)
        if not data_dir.is_dir():
            logger.error("Not a directory: %s", data_dir)
            raise NotADirectoryError(f"Not a directory: {data_dir}")

        merged: dict[str, Issue] = {}
        xml_files = sorted(data_dir.glob("*.xml"))
        logger.info("Found %d XML files in %s", len(xml_files), data_dir)
        logger.debug("XML files: %s", [xml_file.name for xml_file in xml_files])
        for xml_file in xml_files:
            parser = cls.from_file(xml_file)
            duplicates = merged.keys() & parser._issues.keys()
            if duplicates:
                logger.error("Duplicate issue keys found while merging %s: %s", xml_file.name, sorted(duplicates))
                raise ValueError(f"Duplicate keys found in {xml_file.name}: {duplicates}")
            merged.update(parser._issues)
            logger.debug("Merged %d issues after processing %s", len(merged), xml_file.name)

        logger.info("Parsed %d unique issues from directory %s", len(merged), data_dir)
        return cls(merged)

    @staticmethod
    def _build_index(issues: Iterable[Issue]) -> dict[str, Issue]:
        index: dict[str, Issue] = {}
        for issue in issues:
            if issue.key is None:
                logger.error("Encountered issue with missing key: %s", issue)
                raise ValueError(f"Issue with no key encountered: {issue}")
            if issue.key in index:
                logger.error("Duplicate issue key found while indexing: %s", issue.key)
                raise ValueError(f"Duplicate key found: {issue.key}")
            index[issue.key] = issue
        logger.debug("Built issue index with %d entries", len(index))
        return index

    def get(self, key: str) -> Issue:
        issue = self._issues.get(key)
        if issue is None:
            logger.debug("Issue key %s was not found in index", key)
        else:
            logger.debug("Issue key %s resolved to issue type %s", key, issue.type)
        return issue

    def __len__(self) -> int:
        return len(self._issues)

    def __contains__(self, key: str) -> bool:
        return key in self._issues

    @staticmethod
    def _parse_issue(issue_el: ET.Element) -> Issue:
        def text(tag: str) -> str:
            el = issue_el.find(tag)
            return el.text if el is not None else None

        issue = Issue(
            type=text("type"),
            key=text("key"),
            assigned_chr=text("assignedChr"),
            accession1=text("accession1"),
            accession2=text("accession2"),
            report_type=text("reportType"),
            summary=text("summary"),
            status=text("status"),
            status_text=text("status_text"),
            description=text("description").replace("\n", "") if text("description") is not None else "",
            experiment_type=text("experiment_type"),
            external_info_type=text("external_info_type"),
            update=text("update"),
            resolution=text("resolution"),
            resolution_text=text("resolution_text").replace("\n", "") if text("resolution_text") is not None else "",
            affect_version=text("affectVersion"),
            fix_version=text("fixVersion"),
            locations=tuple(GRCIssuesParser._parse_locations(issue_el)),
        )
        logger.debug("Parsed issue %s with %d location(s)", issue.key, len(issue.locations))
        return issue

    @staticmethod
    def _parse_locations(issue_el: ET.Element) -> list[Position]:
        positions = [
            GRCIssuesParser._parse_position(pos)
            for pos in issue_el.findall("location/position")
        ]
        logger.debug("Parsed %d position(s) for issue element", len(positions))
        return positions

    @staticmethod
    def _parse_position(pos: ET.Element) -> Position:
        map_seq_el = pos.find("mapSequence")
        quality_el = pos.find("quality")

        position = Position(
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
        logger.debug(
            "Parsed position name=%s map_seq_type=%s quality_present=%s",
            position.name,
            position.map_seq_type,
            position.quality is not None,
        )
        return position

    @staticmethod
    def _parse_quality(quality_el: ET.Element) -> Quality:
        quality = Quality(
            versions_mapped=tuple(
                VersionMapped(acc=vm.get("acc"), version=vm.text)
                for vm in quality_el.findall("version_mapped")
            ),
            method_acc1=quality_el.findtext("method_acc1"),
            method_acc2=quality_el.findtext("method_acc2"),
        )
        logger.debug(
            "Parsed quality with %d version mapping(s), method_acc1=%s, method_acc2=%s",
            len(quality.versions_mapped),
            quality.method_acc1,
            quality.method_acc2,
        )
        return quality
