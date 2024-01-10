import re

def extract_comment_code_pairs(file_path):
    with open(file_path, 'r') as file:
        content = file.read()

        # Regular expression to match Solidity comments
        comment_pattern = re.compile(r'\/\/.*|\/\*[\s\S]*?\*\/')

        # Find all matches of comments in the content
        comment_matches = re.finditer(comment_pattern, content)

        # Create pairs of comments and associated code
        comment_code_pairs = []
        code_above_comments = []

        current_comment = ""
        inside_curly_brackets = False
        opening_bracket_indentation = 0

        for match in comment_matches:
            comment_start, comment_end = match.span()
            comment = content[comment_start:comment_end].strip()

            # Skip comments at level 1 or higher within curly brackets
            if inside_curly_brackets:
                comment_indentation = len(re.match(r'\s*', comment).group())
                if comment_indentation <= opening_bracket_indentation:
                    continue

            # Append the comment to the current comment
            current_comment += " " + comment if current_comment else comment

            # Find the code section following the comment using curly brackets
            code_start = comment_end
            code_end = len(content)

            # Look for the opening curly bracket
            opening_bracket_pos = content.find('{', code_start)
            if opening_bracket_pos != -1:
                bracket_counter = 1
                code_start = opening_bracket_pos + 1

                # Find the closing curly bracket matching the opening bracket
                while code_start < len(content) and bracket_counter > 0:
                    if content[code_start] == '{':
                        bracket_counter += 1
                    elif content[code_start] == '}':
                        bracket_counter -= 1
                    code_start += 1 # alwas increase until hit

                code_end = code_start

                # Update inside_curly_brackets flag and opening_bracket_indentation
                inside_curly_brackets = bracket_counter > 0
                if inside_curly_brackets:
                    opening_bracket_indentation = len(re.match(r'\s*', content[opening_bracket_pos + 1:]).group())

            # Append the comment-code pair to the list when a code section is found
            if code_start < len(content) and not inside_curly_brackets and not content[comment_end:code_end].strip().startswith('//'):
                comment_code_pairs.append((current_comment, content[comment_end:code_end].strip(), content[:comment_end].strip()))
                current_comment = ""
                code_above_comments.append(content[:comment_end].strip())

        return comment_code_pairs


if __name__ == "__main__":
    # Replace 'your_file.sol' with the path to your Solidity source file
    file_path = 'test/Storage.sol'

    pairs = extract_comment_code_pairs(file_path)

    for comment, code_section, context in pairs:
        print("Comment:")
        print(comment)
        print("\nCode Section:")
        print(code_section)
        print("\n" + "="*40 + "\n")
        print("\ncontext:")
        print(context)
        print("\n" + "="*40 + "\n")
        print()
        print()
        print()
        print()

file_path = 'test/Storage.sol'
