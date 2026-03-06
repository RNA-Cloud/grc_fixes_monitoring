from __future__ import annotations
import argparse
import csv
from dataclasses import dataclass, fields
import logging
import sys
from pathlib import Path

from grc_fixes_monitor.parsers.grc_issues import GRCIssuesParser
from grc_fixes_monitor.parsers.patch_type import PatchTypeParser
from grc_fixes_monitor.parsers.scaffoled_placement import ScaffoldPlacementParser, to_per_issue_scaffold_placements

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class OutputRecord:
    issue_id: str
    type: str
    status: str
    last_updated: str
    affects_version: str
    fix_version: str
    summary: str
    description: str
    experiment_type: str
    report_type: str
    resolution: str
    resolution_text: str
    scaffold_type: str
    alt_scaf_name: str
    parent_type: str
    parent_name: str
    parent_acc: str
    parent_start: int
    parent_stop: int
    ori: str
    alt_scaf_acc: str
    alt_scaf_start: int
    alt_scaf_stop: int

def check_data_files(data_folder: Path):
    logger.info("Checking required data files in %s", data_folder)
    chr_issue_files = sorted(data_folder.glob("chr*.xml"))
    if not chr_issue_files:
        logger.error("No chr*.xml files found in %s. Please ensure the data files are present.", data_folder)
    else:
        logger.info("Found %d chr*.xml files", len(chr_issue_files))
        logger.debug("chr*.xml files: %s", [p.name for p in chr_issue_files])

    alt_scaffold_file = data_folder / "alt_scaffold_placement.txt"
    if not alt_scaffold_file.exists():
        logger.error("alt_scaffold_placement.txt not found in %s. Please ensure the data files are present.", data_folder)
        raise FileNotFoundError(f"alt_scaffold_placement.txt not found in {data_folder}")
    logger.debug("Found required file: %s", alt_scaffold_file)

    patch_type_file = data_folder / "patch_type"
    if not patch_type_file.exists():
        logger.error("patch_type not found in %s. Please ensure the data files are present.", data_folder)
        raise FileNotFoundError(f"patch_type not found in {data_folder}")
    logger.debug("Found required file: %s", patch_type_file)

def write_output(records: list[OutputRecord], output_file: Path) -> None:
    header = [field.name for field in fields(OutputRecord)]
    logger.info("Writing %d records to %s", len(records), output_file)
    logger.debug("Output header has %d columns: %s", len(header), header)
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(header)
        for record in records:
            writer.writerow([getattr(record, field) for field in header])
    logger.info("Wrote %d records to %s", len(records), output_file)

def main() -> None:
    arg_parser = argparse.ArgumentParser(
        description="GRC Fix Monitoring Tool - Process NCBI genome assembly fix patches",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python parse_grc_fixes.py -d /path/to/data -o grc_fixes.csv
        """,
    )

    arg_parser.add_argument("-d", "--data-folder", type=Path, help="Folder containing the data files", required=True)
    arg_parser.add_argument("-o", "--output-file", type=Path, default=Path("grc_fixes.csv"), help="Output CSV file path (default: grc_fixes.csv)")
    arg_parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")

    args = arg_parser.parse_args()

    # Configure logging
    logging_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=logging_level, format="%(asctime)s - %(levelname)s - %(message)s")

    logger.info("Starting GRC Fix Monitoring Tool")
    logger.info(f"Data folder     : {args.data_folder}")
    logger.info(f"Output file     : {args.output_file}")
    logger.info(f"Verbose logging : {'enabled' if args.verbose else 'disabled'}")

    # Check for required data files
    check_data_files(args.data_folder)

    logger.info("Parsing patch type information")
    patch_types_parser = PatchTypeParser.from_file(args.data_folder / "patch_type")
    fix_patches = patch_types_parser.get_fix_patches()
    logger.info(f"Found {len(fix_patches)} fix patches")

    logger.info("Parsing scaffold placement information")
    scaffold_placement_parser = ScaffoldPlacementParser.from_file(args.data_folder / "alt_scaffold_placement.txt")
    scaffold_placements = scaffold_placement_parser.scaffold_placements
    logger.info(f"Found {len(scaffold_placements)} scaffold placements")

    logger.info("Filtering scaffold placements for fix patches")
    fix_patch_names = {patch.alt_scaf_name for patch in fix_patches}
    fix_scaffold_placements = [p for p in scaffold_placements if p.alt_scaf_name in fix_patch_names]
    logger.info(f"Found {len(fix_scaffold_placements)} FIX scaffold placements")
    logger.debug("Unique FIX patch names considered: %d", len(fix_patch_names))

    per_issue_scaffold_placements = to_per_issue_scaffold_placements(fix_scaffold_placements)
    logger.debug(f"Expanded {len(fix_scaffold_placements)} to {len(per_issue_scaffold_placements)} per-issue scaffold placements")

    logger.info("Parsing GRC fixes information")
    grc_issues_parser = GRCIssuesParser.from_directory(args.data_folder)
    logger.info(f"Parsed {len(grc_issues_parser)} GRC issues")

    final_records = []
    logger.info("Joining per-issue scaffold placements with GRC issue details")

    for issue_id, scaffold_placement in per_issue_scaffold_placements.items():
        issue_details = grc_issues_parser.get(issue_id)
        
        if not issue_details:
            logger.error(f"No GRC issue found for key {issue_id} (scaffold {scaffold_placement.alt_scaf_name})")
            raise ValueError(f"No GRC issue found for key {issue_id} (scaffold {scaffold_placement.alt_scaf_name})")

        record = OutputRecord(
            issue_id=issue_details.key,
            type=issue_details.type,
            status=issue_details.status,
            last_updated=issue_details.update,
            affects_version=issue_details.affect_version,
            fix_version=issue_details.fix_version,
            summary=issue_details.summary,
            description=issue_details.description,
            experiment_type=issue_details.experiment_type,
            report_type=issue_details.report_type,
            resolution=issue_details.resolution,
            resolution_text=issue_details.resolution_text,
            scaffold_type="FIX",
            alt_scaf_name=scaffold_placement.alt_scaf_name,
            parent_type=scaffold_placement.parent_type,
            parent_name=scaffold_placement.parent_name,
            parent_acc=scaffold_placement.parent_acc,
            parent_start=scaffold_placement.parent_start,
            parent_stop=scaffold_placement.parent_stop,
            ori=scaffold_placement.ori,
            alt_scaf_acc=scaffold_placement.alt_scaf_acc,
            alt_scaf_start=scaffold_placement.alt_scaf_start,
            alt_scaf_stop=scaffold_placement.alt_scaf_stop
        )
        final_records.append(record)
        logger.debug("Built output record for issue %s and scaffold %s", issue_id, scaffold_placement.alt_scaf_name)

    logger.info(f"Generated {len(final_records)} output records")
    write_output(final_records, args.output_file)
    
if __name__ == "__main__":
    main()
