#!/usr/bin/env python3
"""
GRC Fix Monitoring Tool

A CLI tool to process GRC fix patches from NCBI genome assemblies.
This tool fetches patch placement data, identifies fix patches, and extracts
issue information from the GRC website.
"""

import argparse
import csv
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin
from dataclasses import dataclass, asdict
import requests
from bs4 import BeautifulSoup


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class PatchPlacement:
    """Data class for patch placement information"""

    alt_asm_name: str
    prim_asm_name: str
    alt_scaf_name: str
    alt_scaf_acc: str
    parent_type: str
    parent_name: str
    parent_acc: str
    region_name: str
    ori: str
    alt_scaf_start: int
    alt_scaf_stop: int
    parent_start: int
    parent_stop: int
    alt_start_tail: int
    alt_stop_tail: int


@dataclass
class PatchType:
    """Data class for patch type information"""

    alt_scaf_name: str
    alt_scaf_acc: str
    patch_type: str


@dataclass
class IssueInfo:
    """Data class for GRC issue information"""

    issue_id: str
    summary: str = ""
    description: str = ""
    status: str = ""
    type: str = ""
    last_updated: str = ""
    experiment_type: str = ""
    affects_version: str = ""
    fix_version: str = ""
    resolution: str = ""
    scaffold_type: str = ""
    comment: str = ""


@dataclass
class FinalRecord:
    """Data class for the final combined record"""

    alt_scaf_name: str
    patch_type: str
    parent_type: str
    parent_name: str
    parent_acc: str
    parent_start: int
    parent_stop: int
    ori: str
    alt_scaf_acc: str
    alt_scaf_start: int
    alt_scaf_stop: int
    issue_id: str
    summary: str = ""
    description: str = ""
    status: str = ""
    type: str = ""
    last_updated: str = ""
    experiment_type: str = ""
    affects_version: str = ""
    fix_version: str = ""
    resolution: str = ""
    scaffold_type: str = ""
    comment: str = ""


class GRCFixMonitor:
    """Main class for GRC fix monitoring operations"""

    BASE_URL = "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/000/001/405/GCA_000001405.29_GRCh38.p14/GCA_000001405.29_GRCh38.p14_assembly_structure/PATCHES/alt_scaffolds/"
    GRC_ISSUES_URL = "https://www.ncbi.nlm.nih.gov/grc/human/issues/"

    def __init__(self, debug: bool = False):
        self.debug = debug
        if debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Debug mode enabled")

    def fetch_alt_scaffold_placement(self) -> List[PatchPlacement]:
        """
        Fetch and parse alt scaffold placement data from NCBI

        Returns:
            List of PatchPlacement objects
        """
        url = urljoin(self.BASE_URL, "alt_scaffold_placement.txt")
        logger.info(f"Fetching alt scaffold placement data from: {url}")

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            placements = []
            lines = response.text.strip().split("\n")

            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                try:
                    parts = line.split("\t")
                    if len(parts) >= 15:
                        placement = PatchPlacement(
                            alt_asm_name=parts[0],
                            prim_asm_name=parts[1],
                            alt_scaf_name=parts[2],
                            alt_scaf_acc=parts[3],
                            parent_type=parts[4],
                            parent_name=parts[5],
                            parent_acc=parts[6],
                            region_name=parts[7],
                            ori=parts[8],
                            alt_scaf_start=int(parts[9]),
                            alt_scaf_stop=int(parts[10]),
                            parent_start=int(parts[11]),
                            parent_stop=int(parts[12]),
                            alt_start_tail=int(parts[13]),
                            alt_stop_tail=int(parts[14]),
                        )
                        placements.append(placement)
                        logger.debug(f"Parsed placement: {placement.alt_scaf_name}")
                    else:
                        logger.warning(
                            f"Line {line_num}: Insufficient columns ({len(parts)})"
                        )

                except (ValueError, IndexError) as e:
                    logger.error(f"Line {line_num}: Error parsing line - {e}")
                    continue

            logger.info(f"Successfully parsed {len(placements)} patch placements")
            return placements

        except requests.RequestException as e:
            logger.error(f"Failed to fetch alt scaffold placement data: {e}")
            raise

    def fetch_patch_types(self) -> List[PatchType]:
        """
        Fetch and parse patch type data from NCBI

        Returns:
            List of PatchType objects
        """
        url = urljoin(self.BASE_URL, "patch_type")
        logger.info(f"Fetching patch type data from: {url}")

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            patch_types = []
            lines = response.text.strip().split("\n")

            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                try:
                    parts = line.split("\t")
                    if len(parts) >= 3:
                        patch_type = PatchType(
                            alt_scaf_name=parts[0],
                            alt_scaf_acc=parts[1],
                            patch_type=parts[2],
                        )
                        patch_types.append(patch_type)
                        logger.debug(
                            f"Parsed patch type: {patch_type.alt_scaf_name} -> {patch_type.patch_type}"
                        )
                    else:
                        logger.warning(
                            f"Line {line_num}: Insufficient columns ({len(parts)})"
                        )

                except (ValueError, IndexError) as e:
                    logger.error(f"Line {line_num}: Error parsing line - {e}")
                    continue

            logger.info(f"Successfully parsed {len(patch_types)} patch types")
            return patch_types

        except requests.RequestException as e:
            logger.error(f"Failed to fetch patch type data: {e}")
            raise

    def filter_fix_patches(self, patch_types: List[PatchType]) -> List[str]:
        """
        Filter patch types to get only FIX patches

        Args:
            patch_types: List of PatchType objects

        Returns:
            List of alt_scaf_names that are FIX patches
        """
        fix_patches = [pt.alt_scaf_name for pt in patch_types if pt.patch_type == "FIX"]
        logger.info(f"Found {len(fix_patches)} FIX patches")
        logger.debug(f"FIX patches: {fix_patches}")
        return fix_patches

    def extract_issue_ids(self, alt_scaf_name: str) -> List[str]:
        """
        Extract issue IDs from alt scaffold name

        Args:
            alt_scaf_name: The alt scaffold name (e.g., "HG1342_HG2282_PATCH")

        Returns:
            List of issue IDs (e.g., ["HG-1342", "HG-2282"])
        """
        # Pattern to match HG followed by numbers
        pattern = r"HG(\d+)"
        matches = re.findall(pattern, alt_scaf_name)
        issue_ids = [f"HG-{match}" for match in matches]

        logger.debug(f"Extracted issue IDs from {alt_scaf_name}: {issue_ids}")
        return issue_ids

    def fetch_issue_info(self, issue_id: str) -> IssueInfo:
        """
        Fetch issue information from GRC website

        Args:
            issue_id: The issue ID (e.g., "HG-2095")

        Returns:
            IssueInfo object with extracted information
        """
        url = urljoin(self.GRC_ISSUES_URL, issue_id)
        logger.debug(f"Fetching issue info from: {url}")

        issue_info = IssueInfo(issue_id=issue_id)

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            issue_info_node = soup.find("div", attrs={"id": "issue-summary"}).find(
                "dl", attrs={"id": "issue_info"}
            )

            if not issue_info_node:
                logger.warning(f"No issue info found for {issue_id}")
                raise ValueError(f"No issue info found for {issue_id}")

            issue_info_keys = issue_info_node.find_all("dt")
            issue_info_values = issue_info_node.find_all("dd")

            patches_and_alts_node = soup.find(
                "div", attrs={"id": "patches-and-alts"}
            ).find("dl", attrs={"id": "issue_info"})
            patches_and_alts_keys = patches_and_alts_node.find_all("dt")
            patches_and_alts_values = patches_and_alts_node.find_all("dd")

            issue_info_keys_list = [
                key.get_text(strip=True).replace(":", "").lower()
                for key in issue_info_keys
            ]
            issue_info_values_list = [re.sub(r"[\t\n\r]+", " ", value.get_text()) for value in issue_info_values]  # type: ignore

            patches_and_alts_keys_list = [
                key.get_text(strip=True).replace(":", "").lower()
                for key in patches_and_alts_keys
            ]
            patches_and_alts_values_list = [re.sub(r"[\t\n\r]+", " ", value.get_text()) for value in patches_and_alts_values]  # type: ignore

            issue_info_keys_list.extend(patches_and_alts_keys_list)
            issue_info_values_list.extend(patches_and_alts_values_list)

            for key, value in zip(issue_info_keys_list, issue_info_values_list):
                if key == "summary":
                    issue_info.summary = value
                elif key == "description":
                    issue_info.description = value
                elif key == "status":
                    issue_info.status = value
                elif key == "type":
                    issue_info.type = value
                elif key == "last updated":
                    issue_info.last_updated = value
                elif key == "experiment type":
                    issue_info.experiment_type = value
                elif key == "affects version":
                    issue_info.affects_version = value
                elif key == "fix version":
                    issue_info.fix_version = value
                elif key == "resolution":
                    issue_info.resolution = value
                elif key == "scaffold type":
                    issue_info.scaffold_type = value
                elif key == "comment":
                    issue_info.comment = value

            logger.debug(f"Successfully fetched issue info for {issue_id}")

        except requests.RequestException as e:
            logger.error(f"Failed to fetch issue info for {issue_id}: {e}")
        except Exception as e:
            logger.error(f"Error parsing issue info for {issue_id}: {e}")

        return issue_info

    def process_fixes(self, sample: bool = False) -> List[FinalRecord]:
        """
        Main processing function that combines all steps

        Returns:
            List of FinalRecord objects with complete information
        """
        logger.info("Starting GRC fix processing workflow")

        # Step 1: Fetch all data
        placements = self.fetch_alt_scaffold_placement()
        patch_types = self.fetch_patch_types()

        # Step 2: Filter for FIX patches
        fix_patch_names = self.filter_fix_patches(patch_types)

        if sample:
            # If sample mode is enabled, limit the number of FIX patches processed
            fix_patch_names = fix_patch_names[:10]
            logger.info(
                f"Sample mode enabled, processing only {len(fix_patch_names)} FIX patches"
            )

        # Create lookup dictionaries
        placement_dict = {p.alt_scaf_name: p for p in placements}
        patch_type_dict = {pt.alt_scaf_name: pt for pt in patch_types}

        # Step 3: Process each FIX patch
        final_records = []

        for fix_name in fix_patch_names:
            if fix_name not in placement_dict:
                logger.warning(f"No placement data found for FIX patch: {fix_name}")
                continue

            placement = placement_dict[fix_name]
            patch_type = patch_type_dict[fix_name]

            # Extract issue IDs
            issue_ids = self.extract_issue_ids(fix_name)

            if not issue_ids:
                logger.error(f"No issue IDs found for: {fix_name}")
                raise ValueError(f"No issue IDs found for: {fix_name}")

            # Fetch issue information for each issue ID
            for issue_id in issue_ids:
                issue_info = self.fetch_issue_info(issue_id)

                record = FinalRecord(
                    alt_scaf_name=placement.alt_scaf_name,
                    patch_type=patch_type.patch_type,
                    parent_type=placement.parent_type,
                    parent_name=placement.parent_name,
                    parent_acc=placement.parent_acc,
                    parent_start=placement.parent_start,
                    parent_stop=placement.parent_stop,
                    ori=placement.ori,
                    alt_scaf_acc=placement.alt_scaf_acc,
                    alt_scaf_start=placement.alt_scaf_start,
                    alt_scaf_stop=placement.alt_scaf_stop,
                    issue_id=issue_info.issue_id,
                    summary=issue_info.summary,
                    description=issue_info.description,
                    status=issue_info.status,
                    type=issue_info.type,
                    last_updated=issue_info.last_updated,
                    experiment_type=issue_info.experiment_type,
                    affects_version=issue_info.affects_version,
                    fix_version=issue_info.fix_version,
                    resolution=issue_info.resolution,
                    scaffold_type=issue_info.scaffold_type,
                    comment=issue_info.comment,
                )
                final_records.append(record)

        logger.info(
            f"Processing complete. Generated {len(final_records)} final records"
        )
        return final_records

    def save_to_tsv(self, records: List[FinalRecord], output_path: Path) -> None:
        """
        Save final records to TSV file

        Args:
            records: List of FinalRecord objects
            output_path: Path to output TSV file
        """
        logger.info(f"Saving {len(records)} records to: {output_path}")

        try:
            with open(output_path, "w", newline="", encoding="utf-8") as tsvfile:
                if records:
                    fieldnames = asdict(records[0]).keys()
                    writer = csv.DictWriter(
                        tsvfile, fieldnames=fieldnames, delimiter="\t"
                    )
                    writer.writeheader()

                    for record in records:
                        writer.writerow(asdict(record))

                logger.info(f"Successfully saved data to: {output_path}")

        except Exception as e:
            logger.error(f"Failed to save data to TSV: {e}")
            raise


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="GRC Fix Monitoring Tool - Process NCBI genome assembly fix patches",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -o output.csv
  %(prog)s --output-file results.csv --debug
  %(prog)s --help
        """,
    )

    parser.add_argument(
        "-o",
        "--output-file",
        type=Path,
        default=Path("grc_fixes.csv"),
        help="Output CSV file path (default: grc_fixes.csv)",
    )

    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Enable debug logging for verbose output",
    )

    parser.add_argument(
        "-s",
        "--sample",
        action="store_true",
        help="Only process a sample of the data for testing purposes (default: False)",
        default=False,
    )

    args = parser.parse_args()

    try:
        # Initialize the monitor
        monitor = GRCFixMonitor(debug=args.debug)

        # Process the fixes
        records = monitor.process_fixes(args.sample)

        if not records:
            logger.warning("No records generated. Check the logs for errors.")
            sys.exit(1)

        # Save results
        monitor.save_to_tsv(records, args.output_file)

        print(f"✅ Successfully processed {len(records)} records")
        print(f"📄 Output saved to: {args.output_file}")

    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        if args.debug:
            raise
        sys.exit(1)


if __name__ == "__main__":
    main()
