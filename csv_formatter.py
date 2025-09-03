import re

def modify_csv_format(input_filepath, output_filepath):
    """
    Modifies a CSV file:
    1. Changes column delimiter from ',' to a temporary '|'.
    2. Changes decimal separator from '.' to ',' for numbers.
    3. Changes the temporary delimiter '|' to the final ';'.
    """
    try:
        with open(input_filepath, 'r', encoding='utf-8') as infile:
            content = infile.readlines()

        modified_content = []
        for line in content:
            # Step 1: Change original column delimiter ',' to a temporary '|'
            # This prevents new commas (from decimal conversion) from being treated as delimiters.
            temp_line_delimiter_changed = line.replace(',', '|')

            # Step 2: Change decimal separator from '.' to ',' for numbers.
            # This regex finds sequences of digits, a dot, and more digits (e.g., "123.45")
            # and replaces the dot with a comma.
            temp_line_decimal_changed = re.sub(r'(\d+)\.(\d+)', r'\1,\2', temp_line_delimiter_changed)

            # Step 3: Change the temporary delimiter '|' to the final ';'
            final_modified_line = temp_line_decimal_changed.replace('|', ';')

            modified_content.append(final_modified_line)

        with open(output_filepath, 'w', encoding='utf-8') as outfile:
            outfile.writelines(modified_content)
        return True, "CSV file modified successfully."
    except FileNotFoundError:
        return False, f"Error: Input file not found at {input_filepath}"
    except Exception as e:
        return False, f"An error occurred: {e}"