import unittest
from main import generate_viva_questions  # Import the generate_viva_questions function from main.py
from main import OpenAI
from dotenv import load_dotenv
import os

load_dotenv() # Loading env file for future data retrieval

# VERY IMPORTANT PLEASE IMPLEMENT VARIABLES IN ENV FILE AS NAMED HERE:
client = OpenAI( 
  api_key= os.getenv("OPENAI_API_KEY"),  
  organization= os.getenv("OPENAI_ORG_KEY"),
  project= os.getenv("OPENAI_PROJ_KEY")  
)

# Test cases for Question Generation
def test_generate_questions_single_file():
    # Sample input
    file_path = "sample_assignment.pdf"
    # Expected output (you can adjust this based on real expected output)
    expected_output_length = 5  # Expected number of generated questions
    result = generate_viva_questions(file_path)
    assert len(result['questions']) == expected_output_length, f"Should generate {expected_output_length} questions"

def test_generate_questions_batch():
    # Simulating batch upload with multiple files
    file_paths = ["sample1.pdf", "sample2.pdf", "sample3.pdf"]
    # Expected output length
    expected_output_length = 3  # As there are 3 files
    results = [generate_viva_questions(file) for file in file_paths]
    assert len(results) == expected_output_length, "Should process all files in batch"

def test_invalid_file_format():
    # Testing with an invalid file format
    file_path = "invalid_file.txt"
    try:
        generate_viva_questions(file_path)
        assert False, "Expected ValueError for unsupported file format"
    except ValueError:
        pass  # Expected outcome

def test_empty_file():
    # Simulating an empty file (no content)
    file_path = "empty_assignment.pdf"
    result = generate_viva_questions(file_path)
    assert len(result['questions']) == 0, "Should return an empty list for empty input files"

def test_large_file():
    # Simulating a large file upload
    file_path = "large_assignment.pdf"
    result = generate_viva_questions(file_path)
    # Assuming large file should still generate the expected 5 questions
    assert len(result['questions']) == 5, "Should handle large files and generate 5 questions"

# Run all tests
if __name__ == '__main__':
    test_generate_questions_single_file()
    test_generate_questions_batch()
    test_invalid_file_format()
    test_empty_file()
    test_large_file()
    print("All tests passed.")