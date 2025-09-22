# File: low_quality_test.py

# Naming violation: should be PascalCase
class low_quality_class:
    # Missing docstring for the class

    def i_am_a_good_function(self):
        """This function is well-documented and correctly named."""
        # This block will be detected as duplicated
        print("Repeating line 1")
        print("Repeating line 2")
        print("Repeating line 3")
        print("Repeating line 4")

    # Naming violation: should be snake_case
    # Missing docstring for the function
    def BadFunctionName(self):
        # Naming violation: variable should be snake_case
        BAD_VARIABLE = "test"
        
        # This block is a duplicate of the one above
        print("Repeating line 1")
        print("Repeating line 2")
        print("Repeating line 3")
        print("Repeating line 4")
        return BAD_VARIABLE