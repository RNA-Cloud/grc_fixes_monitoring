# GRC Fix Monitoring Tool 🧬

> A simple tool to track genome assembly fixes and improvements from the Genome Reference Consortium (GRC)

## What does this tool do?

The human genome reference is constantly being improved as scientists discover errors or find better sequences. When researchers find problems in the genome assembly, they report "issues" to the GRC, who then create "patches" to fix these problems.

This tool automatically:
- 📥 Downloads the latest patch information from NCBI
- 🔍 Identifies which patches are actual "fixes" (not just alternatives)
- 🏷️ Extracts the issue numbers that each patch addresses  
- 📋 Fetches detailed information about each issue from the GRC website
- 📊 Combines everything into a single, easy-to-read CSV file

### Visual flowchart
```mermaid
---
config:
  theme: mc
  layout: dagre
  flowchart:
    htmlLabels: true
---
flowchart TD
    A[Start] --> B[Parse CLI Arguments]
    B --> C[Fetch Data from NCBI]
    C --> D[Filter for FIX Patches]
    D --> E[Extract Issue IDs from Patch Names]
    E --> F[Fetch Issue Details from GRC Website]
    F --> G[Combine All Data]
    G --> H[Save to CSV]
    H --> I[End]
    
    %% Error handling
    C -.->|Network Error| J[Exit with Error]
    F -.->|Parse Error| K[Continue with Partial Data]
    H -.->|File Error| J
    
    %% Styling
    classDef startEnd fill:#4CAF50,stroke:#2E7D32,stroke-width:3px,color:#fff
    classDef process fill:#2196F3,stroke:#1565C0,stroke-width:2px,color:#fff
    classDef error fill:#F44336,stroke:#C62828,stroke-width:2px,color:#fff
    
    class A,I startEnd
    class B,C,D,E,F,G,H process
    class J,K error
```

## Why is this useful?

Instead of manually browsing through multiple websites and files to understand what genome fixes are available, this tool gives you a comprehensive overview in minutes. Perfect for:

- **Researchers** who need to know about recent genome improvements
- **Bioinformaticians** tracking assembly changes for their pipelines
- **Quality control teams** monitoring genome reference updates
- **Anyone** curious about how the human genome reference evolves over time

## What you get

The tool produces a CSV file with information like:
- Which chromosome or region was fixed
- What the specific problem was (from the issue description)
- When the fix was made
- The exact genomic coordinates affected
- Current status of each issue

## Quick Start

```bash
# Install dependencies
pip install requests beautifulsoup4

# Run the tool (creates grc_fixes.csv)
python grc_fix_monitor.py

# Or specify a custom output file
python grc_fix_monitor.py -o my_genome_fixes.csv
```

## Example Output

| Patch Name | Issue ID | Summary | Status | Chromosome | 
|------------|----------|---------|---------|------------|
| HG2095_PATCH | HG-2095 | Fix assembly gap on chromosome 14 | Fixed | chr14 |
| HG2183_PATCH | HG-2183 | Correct sequence error in centromere | Resolved | chr3 |

