# File: inefficient_test.py

def process_data(data_list):
    # This inefficient concatenation in a loop should be detected.
    result_string = ""
    for item in data_list:
        result_string += str(item) + ","

    # This nested loop has O(n^2) complexity and should be detected.
    for x in data_list:
        for y in data_list:
            if x == y:
                print("Found a match")

    return result_string