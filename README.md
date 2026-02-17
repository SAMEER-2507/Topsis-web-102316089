# Topsis-Sameer-102316089

A Python package that implements **TOPSIS** (Technique for Order of Preference by Similarity to Ideal Solution) — a multi-criteria decision-making method.

## Installation

```bash
pip install Topsis-Sameer-102316089
```

## Usage

Run from the command line:

```bash
topsis <InputDataFile> <Weights> <Impacts> <OutputResultFileName>
```

### Example

```bash
topsis data.csv "1,1,1,2" "+,+,-,+" output.csv
```

### Parameters

| Parameter | Description |
|-----------|-------------|
| `InputDataFile` | Path to input CSV/Excel file |
| `Weights` | Comma-separated weights (e.g., `"1,1,1,2"`) |
| `Impacts` | Comma-separated impacts, `+` or `-` (e.g., `"+,+,-,+"`) |
| `OutputResultFileName` | Path for the output CSV file |

## Input File Format

- The input file must contain **three or more columns**.
- The **first column** is the name/label of each alternative (e.g., M1, M2, …).
- **Column 2 onwards** must contain **numeric values only**.

### Sample Input (`data.csv`)

| Fund Name | P1   | P2   | P3  | P4   | P5    |
|-----------|------|------|-----|------|-------|
| M1        | 0.67 | 0.45 | 6.5 | 42.6 | 12.56 |
| M2        | 0.60 | 0.36 | 3.6 | 53.3 | 14.47 |
| M3        | 0.82 | 0.67 | 3.8 | 63.1 | 17.10 |

## Output File Format

The output file contains all original columns plus two new columns:

| Column | Description |
|--------|-------------|
| `Topsis Score` | The computed TOPSIS score (0 to 1) |
| `Rank` | Rank based on score (1 = best) |

### Sample Output (`output.csv`)

| Fund Name | P1   | P2   | P3  | P4   | P5    | Topsis Score | Rank |
|-----------|------|------|-----|------|-------|-------------|------|
| M1        | 0.67 | 0.45 | 6.5 | 42.6 | 12.56 | 20.58       | 2    |
| M2        | 0.60 | 0.36 | 3.6 | 53.3 | 14.47 | 40.83       | 4    |
| M3        | 0.82 | 0.67 | 3.8 | 63.1 | 17.10 | 30.07       | 3    |

## Input Validations

The program checks for the following:

1. **Correct number of parameters** — exactly 4 arguments required
2. **File not found** — shows an appropriate error message
3. **Minimum columns** — input file must have ≥ 3 columns
4. **Numeric values** — columns 2 onwards must be numeric
5. **Count match** — number of weights, impacts, and criteria columns must be equal
6. **Valid impacts** — impacts must be `+` or `-` only
7. **Comma-separated** — weights and impacts must be separated by commas

## License

MIT © Sameer
