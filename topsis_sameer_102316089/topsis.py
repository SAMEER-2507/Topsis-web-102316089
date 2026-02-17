import sys
import os
import pandas as pd
import numpy as np


def validate_inputs(argv):
    """Validate command-line arguments and return parsed inputs."""
    # Check correct number of parameters
    if len(argv) != 5:
        raise SystemExit(
            "Usage: topsis <InputDataFile> <Weights> <Impacts> <OutputResultFileName>\n"
            'Example: topsis data.csv "1,1,1,2" "+,+,-,+" output.csv'
        )

    input_file = argv[1]
    weights_str = argv[2]
    impacts_str = argv[3]
    output_file = argv[4]

    # Check if input file exists
    if not os.path.isfile(input_file):
        raise FileNotFoundError(f'File not found — "{input_file}"')

    # Read the input file
    try:
        if input_file.endswith(".xlsx") or input_file.endswith(".xls"):
            df = pd.read_excel(input_file)
        else:
            df = pd.read_csv(input_file)
    except Exception as e:
        raise Exception(f"Could not read file — {e}")

    # Input file must contain three or more columns
    if df.shape[1] < 3:
        raise ValueError("Input file must contain three or more columns.")

    # From 2nd to last columns must contain numeric values only
    numeric_cols = df.iloc[:, 1:]
    for col in numeric_cols.columns:
        if not pd.to_numeric(numeric_cols[col], errors="coerce").notnull().all():
            raise ValueError(
                f'Column "{col}" contains non-numeric values. '
                "From 2nd to last columns must contain numeric values only."
            )

    # Parse weights (comma-separated)
    try:
        weights = [float(w.strip()) for w in weights_str.split(",")]
    except ValueError:
        raise ValueError("Weights must be numeric values separated by commas.")

    # Parse impacts (comma-separated)
    impacts = [i.strip() for i in impacts_str.split(",")]

    # Impacts must be either +ve or -ve
    for impact in impacts:
        if impact not in ("+", "-"):
            raise ValueError('Impacts must be either +ve or -ve (use "+" or "-").')

    num_criteria = df.shape[1] - 1  # exclude the first column (name/label)

    # Number of weights, impacts, and columns (from 2nd to last) must be the same
    if len(weights) != num_criteria:
        raise ValueError(
            f"Number of weights ({len(weights)}) must match the number of "
            f"criteria columns ({num_criteria})."
        )

    if len(impacts) != num_criteria:
        raise ValueError(
            f"Number of impacts ({len(impacts)}) must match the number of "
            f"criteria columns ({num_criteria})."
        )

    return df, np.array(weights), impacts, output_file


def topsis(df, weights, impacts):
    """
    Perform TOPSIS analysis.

    Parameters
    ----------
    df : pd.DataFrame — full dataframe (first column is label, rest are criteria)
    weights : np.ndarray — weight for each criterion
    impacts : list of str — '+' or '-' for each criterion

    Returns
    -------
    scores : np.ndarray — TOPSIS score for each alternative
    ranks : np.ndarray — rank (1 = best)
    """
    # Step 1: Extract the decision matrix (columns 2 onwards)
    matrix = df.iloc[:, 1:].values.astype(float)

    # Step 2: Normalise — divide each value by the root-sum-of-squares of its column
    rss = np.sqrt((matrix ** 2).sum(axis=0))
    norm_matrix = matrix / rss

    # Step 3: Weighted normalised matrix
    weighted_matrix = norm_matrix * weights

    # Step 4: Determine ideal best and ideal worst
    ideal_best = np.zeros(weighted_matrix.shape[1])
    ideal_worst = np.zeros(weighted_matrix.shape[1])

    for j in range(weighted_matrix.shape[1]):
        if impacts[j] == "+":
            ideal_best[j] = weighted_matrix[:, j].max()
            ideal_worst[j] = weighted_matrix[:, j].min()
        else:
            ideal_best[j] = weighted_matrix[:, j].min()
            ideal_worst[j] = weighted_matrix[:, j].max()

    # Step 5: Euclidean distance from ideal best and ideal worst
    dist_best = np.sqrt(((weighted_matrix - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted_matrix - ideal_worst) ** 2).sum(axis=1))

    # Step 6: TOPSIS score
    scores = dist_worst / (dist_best + dist_worst)

    # Step 7: Rank (higher score = better = rank 1)
    ranks = scores.argsort()[::-1].argsort() + 1

    return scores, ranks


def main():
    """Entry point for the topsis command-line tool."""
    try:
        df, weights, impacts, output_file = validate_inputs(sys.argv)
        scores, ranks = topsis(df, weights, impacts)

        # Build output dataframe: original data + Topsis Score + Rank
        result = df.copy()
        result["Topsis Score"] = np.round(scores, 2)
        result["Rank"] = ranks.astype(int)

        # Save to output file
        result.to_csv(output_file, index=False)
        print(f"Result saved to {output_file}")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except SystemExit:
        raise
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
