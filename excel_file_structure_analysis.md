# Flow Results Analysis File - Deep Structure Documentation

## Executive Summary

The file `flow_results_processed_SEP25_R1.xlsx` is a comprehensive power flow constraint analysis workbook containing historical data and future projections from July 2025 through May 2026. It features extensive conditional formatting with color scales for data visualization. **All data columns contain static values (no formulas except hyperlinks)**, with VIEW being the primary editable column containing multiple scenario values per constraint cluster.

## File Architecture

### Sheet Organization

The workbook contains 15 sheets organized into 4 functional categories:

1. **Monthly Flow Data Sheets** (11 sheets)
   - `HIST`: Historical baseline (July-August 2025) - 2,224 rows × 274 columns
     - **Unique feature**: No SOURCE/SINK data
     - Contains 60 days of historical data (2 months)
   - `SEP25` through `MAY26`: Monthly projections - ~2,100-2,400 rows × 214-216 columns each
     - **Unique feature**: Contains SOURCE/SINK node data
     - Contains 30 days of projection data per sheet
     - PREV column renamed to include month (e.g., "PREV (SEP25)")

2. **Consolidated Summary** (1 sheet)
   - `Summary`: Aggregated data across all periods - 2,387 rows × 508 columns

3. **Violation Analysis** (3 sheets) - **No conditional formatting**
   - `PNODE_CAPACITY`: Node capacity limits - 7,225 rows × 2 columns
   - `DAILY_REVENUE_VIOLATIONS`: Revenue violations by date/TOU - 413 rows × 8 columns
   - `NODE_USAGE_VIOLATIONS`: Node usage violations - 238 rows × 5 columns

4. **Reference Data** (1 sheet) - **No conditional formatting**
   - `EXISTING_PF`: Existing power flow records - 52,628 rows × 5 columns

## Key Differences: HIST vs Monthly Sheets

| Aspect | HIST Sheet | Monthly Sheets (SEP25-MAY26) |
|--------|------------|------------------------------|
| **Columns** | 274 | 214-216 |
| **Date Coverage** | 60 days (Jul-Aug) | 30 days per month |
| **SOURCE/SINK** | Empty (0 values) | Populated (~1,900 values) |
| **PREV Column** | Named "PREV" | Named "PREV (MONTH)" |
| **Purpose** | Historical baseline | Future projections |

## Column Structure & Classification

### Column Categories

| Category | HIST | Monthly | Columns | Purpose |
|----------|------|---------|---------|---------|
| **Core Columns** | 33 | 33 | A-AD | Constraint parameters and data values |
| **Date Columns** | 60 | 30 | Variable | Daily values (format: YYYY-MM-DD) |
| **LODF Columns** | 60 | 30 | Variable | Line Outage Distribution Factors |
| **Scenario Columns** | 121 | 121 | Variable | Scenario analysis (SCN1-SCN121) |
| **URL Columns** | 3 | 3 | AE-AG | Hyperlinks (only calculated columns) |

### Detailed Column Definitions

#### Data Input Columns (ALL EDITABLE - No Calculations)

**Primary Editable Columns:**
- **VIEW** (Column C): **Primary editable column** - Multiple scenario values per constraint cluster
- **SP** (Column B): Setter Price - One value per constraint cluster (parent row)
- **SHORTLIMIT** (Column AB): Short limit override - Currently unused (all null)

**Statistical Data Columns (Editable):**
- **CSP95** (Column H): 95th percentile value
- **CSP80** (Column I): 80th percentile value
- **CSP50** (Column J): 50th percentile value (median)
- **CSP20** (Column K): 20th percentile value
- **CSP5** (Column L): 5th percentile value

**Other Data Columns:**
- **PREV** (Column D): Previous period value (renamed in monthly sheets)
- **PACTUAL** (Column E): Actual probability value
- **PEXPECTED** (Column F): Expected probability value
- **VIEWLG** (Column G): Logarithmic view value

#### Constraint Information Columns

- **MON** (Column M): Monitor/element name (e.g., "NEWTON 3 TR2 XFORMER")
- **CONT** (Column N): Contingency description (e.g., "Jordan- Massac 345kV")
- **DIRECTION** (Column O): Flow direction indicator (-1.0 or 1.0)
- **SOURCE** (Column P): Source node - **Populated in monthly sheets only**
- **SINK** (Column Q): Sink node - **Populated in monthly sheets only**
- **SENS** (Column R): Sensitivity value (currently unused)
- **PRICE** (Column S): Price value
- **LIMIT** (Column T): MW limit (25.35 to 9999 MW, where 9999 = unconstrained)
- **FLOW** (Column X): Flow value in MW (0 to 5215.21 MW)

#### Calculated Columns (Formulas)

**Only these columns contain formulas:**
- **PURL** (Column AD): `=HYPERLINK("file:///Users/jmetzler/ftr/tmp/predict...")`
- **URL1** (Column AE): `=HYPERLINK("file:///Users/jmetzler/ftr/./tmp/contr...")`
- **URL2** (Column AF): Additional constraint hyperlinks
- **URL3** (Column AG): Tertiary reference hyperlinks

## Row Structure & Constraint Grouping

### Hierarchical Constraint Organization

1. **Cluster Structure**
   - 281 unique clusters (IDs: 6 to 5655, non-consecutive with 116 gaps)
   - Each cluster = one transmission constraint/monitored element
   - Rows per cluster: 1-42 (average: 7.9, mode: 2)

2. **Parent-Child Row Pattern**
   ```
   Cluster X:
     Row 1 (Parent):  SP=value, VIEW=empty    <- Single setter value
     Row 2 (Child):   SP=empty, VIEW=value1   <- Scenario 1
     Row 3 (Child):   SP=empty, VIEW=value2   <- Scenario 2
     Row 4 (Child):   SP=empty, VIEW=value3   <- Scenario 3
     ...
   ```

3. **Cluster Size Distribution**
   ```
   2 rows:  54 clusters (19.2%) - Most common
   3 rows:  23 clusters (8.2%)
   4 rows:  28 clusters (10.0%)
   5-15 rows: Majority of remaining clusters
   42 rows: Maximum cluster size
   ```

## Conditional Formatting Architecture

### Exact Formatting Ranges

**HIST Sheet (4,460 total rows):**
- **Core Columns**: B2:B4460 through L2:L4460 (SP, VIEW, PREV, CSPs)
- **Error Validation**: H2:L4460 (CSP columns grouped)
- **Date/Time Series**: AH2:CO4460 (individual row ranges)
- **Scenario Columns**: Variable ranges for SCN1-SCN121
- **Single Cell Validations**: O115, O147, O184, etc. (critical points)

**Monthly Sheets (e.g., SEP25 with 4,557 rows):**
- **Core Columns**: B2:B4557 through L2:L4557
- **Date Ranges**: AH1000:BK1000 (row-by-row formatting)
- **Error Checks**: AA1016, AA1044, AA1046, etc. (specific cells)

### Formatting Logic & Purpose

#### Color Scale Gradients (2,200-2,400 rules per sheet)

**Purpose**: Visual identification of constraint risk levels using exact thresholds

#### Exact Color Thresholds by Column Type

**1. Core Columns (SP, VIEW, PREV, CSPs) - Columns B-L:**
| Value Range | Color | Interpretation |
|------------|-------|----------------|
| ≤ 0.5 | White | Minimal concern |
| 0.5 to 4th percentile | White → Yellow | Low values |
| 4th percentile to 20 | Yellow → Red | Increasing concern |
| > 20 | **Red** | **Critical - High risk constraint** |

**2. RECENT_DELTA (Column AC):**
| Value | Color | Interpretation |
|-------|-------|----------------|
| -50 | Blue | Large negative change |
| 0 | White | No change |
| +50 | Red | Large positive change |

**3. Date Columns - SP Rows (Parent):**
| Value Range | Color | Interpretation |
|------------|-------|----------------|
| 0 | White | No activity |
| 0 to 10th percentile | White → Yellow | Normal range |
| 10th percentile to 100 | Yellow → Red | Elevated activity |
| > 100 | **Red** | **Critical day** |

**4. Date Columns - VIEW Rows (Children):**
| Value Range | Color | Interpretation |
|------------|-------|----------------|
| 0 | White | No activity |
| 0 to 150 | White → Black gradient | Scenario intensity |
| > 150 | **Black** | **High scenario value** |

**5. LODF Columns (Outage Factors):**
| Value | Color | Interpretation |
|-------|-------|----------------|
| -1.0 | Red | Negative impact |
| 0.0 | White | No impact |
| +1.0 | Green | Positive impact |

**Column-Specific Applications:**
| Column | Color Trigger | Critical Threshold |
|--------|--------------|-------------------|
| VIEW (C) | Red > 20 | Values above 20 need attention |
| SP (B) | Red > 20 | Setter prices above 20 are critical |
| CSP95-CSP5 (H-L) | Red > 20 | Statistical values above 20 |
| Date columns (SP rows) | Red > 100 | Daily values above 100 |
| Date columns (VIEW rows) | Black > 150 | Scenario values above 150 |
| SCN columns | Red > 20 | Scenario results above 20 |
| LODF columns | Red/Green at ±1 | Full positive/negative impact |

#### Error Validation Rules (50-260 per sheet)

**Formula**: `NOT(ISERROR(cell))`
- **H2:L4460**: Validates all statistical calculations
- **Individual cells**: Critical calculation points
- **Purpose**: Suppresses #DIV/0!, #VALUE!, #REF! display

### Why These Specific Ranges?

1. **Row 2 Start**: Skips header row for clean visualization
2. **Full Column Coverage**: Ensures all future data automatically formatted
3. **Grouped Ranges (H2:L)**: Related statistics formatted together
4. **Individual Cells**: Specific validation points in data
5. **Row-by-row Date Formatting**: Enables horizontal pattern recognition

## Data Relationships & Value Patterns

### SP-VIEW Relationship

**Not calculated, but follows pattern:**
```
Cluster 7 Example:
  SP value: 0.199881 (one value)
  VIEW values: 0.246611, 0.000000, 0.005466... (multiple unique values)
  VIEW/SP ratios: 1.234, 0.000, 0.027 (no fixed relationship)
```

### Statistical Value Spreads

**Typical CSP/SP Ratios (vary by constraint):**
- CSP95/SP: 2-5x (upper confidence bound)
- CSP80/SP: 1-3x
- CSP50/SP: 0.5-1x (median)
- CSP20/SP: 0.2-0.6x
- CSP5/SP: 0.1-0.3x (lower confidence bound)

## Key Metrics & Statistics

### Constraint Monitoring
- **1,830 unique monitors** (MON column)
- **752 unique contingencies** (CONT column)
- **Flow direction**: Bidirectional (-1.0 or 1.0)

### Common Limit Values
1. 9999 MW: 30 occurrences (unconstrained)
2. 480 MW: 22 occurrences
3. 177 MW: 18 occurrences
4. 157 MW: 14 occurrences

### SOURCE/SINK Nodes (Monthly Sheets Only)
- **~1,900 populated rows per monthly sheet**
- Examples: 'GIBSNAEP24 KV UN5 WVPA', 'SULLIVAN-AEP'
- Critical for identifying constraint endpoints

## Usage Workflow

### Data Entry Process

1. **Open monthly sheet** (not HIST - that's historical reference)
2. **Locate constraint cluster** by CLUSTER ID
3. **Edit VIEW values** (Column C) for each scenario row
4. **Optionally edit SP value** (Column B) for parent row
5. **Review color gradients** to identify high-risk areas
6. **Check violation sheets** for constraint violations

### Interpretation Guidelines

- **Color Intensity**: Darker = Higher risk/value
- **Multiple VIEW Rows**: Each represents different scenario/probability
- **Blank SOURCE/SINK in HIST**: Historical data lacks node details
- **9999 MW Limits**: Effectively unconstrained elements
- **Error Validation**: Cells with errors won't display values

## Data Quality & Validation

### Current Data State
- **HIST Sheet**: SOURCE/SINK empty (historical limitation)
- **Monthly Sheets**: SOURCE/SINK populated (~88% rows)
- **SENS Column**: Unused across all sheets
- **SHORTLIMIT Column**: Available but unused
- **URL Formulas**: Contains hardcoded paths to original user's system

### Validation Architecture
- **2,200+ color scales**: Immediate visual validation
- **260+ error checks**: Prevents error propagation
- **Consistent row patterns**: Maintains data integrity
- **Cluster grouping**: Preserves constraint relationships

## Performance Considerations

### File Complexity
- **>25,000 conditional format rules** total
- **>1 million data cells**
- **Real-time color calculations** on data change
- **121 parallel scenarios** per constraint

### Optimization Tips
- Disable automatic calculation when making bulk edits
- Consider removing unused conditional formatting from static sheets
- Update hyperlink paths for local system
- Archive historical months to reduce file size

---

*Document generated from deep analysis of flow_results_processed_SEP25_R1.xlsx*
*Analysis date: August 26, 2025*
*Key Insight: VIEW column contains the primary editable scenario data with no calculated columns except hyperlinks*