import re
from enum import Enum

def extract_blocks(file_path):
    with open(file_path, 'r') as file:
        solidity_code = file.readlines()

    in_curly = False
    in_curly_level = 0 
    main_block = []
    curr_block_data = []
    blocks = []

    for line in solidity_code: 
        main_block.append(line)
        line_added = False

        if in_curly:
            # normal code or comment line
            curr_block_data.append(line)
            line_added = True

        if "{" in line and "}" in line: 
            if not line_added:
                curr_block_data.append(l)

        elif "{" in line : 
            in_curly = True
            in_curly_level += 1

        elif "}" in line: 
            in_curly_level -= 1
            in_curly = True if in_curly_level else False
            if in_curly_level == 1:
                blocks.append(curr_block_data)
                curr_block_data = []
        
        
    blocks.append(main_block)
    
    return blocks

class COMMENTTYPE(Enum): 
    SINGLELINE=0
    SINGLE_INLINE=1
    MULTILINE_START=2
    MULTILINE_BETWEEN=3
    MULTILINE_END=4
    NATSPEC_START=5
    NO_COMMENT=6
    SINGLELINE_NATSP=7

def get_comment_type(line:str):
    
    if line.strip().startswith('///'):
        return COMMENTTYPE.SINGLELINE_NATSP
    elif line.strip().startswith('//'):
        return COMMENTTYPE.SINGLELINE
    elif "//" in line.strip():
        return COMMENTTYPE.SINGLE_INLINE
    elif line.strip().startswith('/*'):
        return COMMENTTYPE.MULTILINE_START
    elif line.strip().startswith('/**'):
        return COMMENTTYPE.NATSPEC_START
    elif line.strip().startswith('*/'):
        return COMMENTTYPE.MULTILINE_END
    elif line.strip().startswith('*'):
        return COMMENTTYPE.MULTILINE_BETWEEN
    else:
        return COMMENTTYPE.NO_COMMENT


def extract_solidity_comment_and_code(code):
    comment_code_pairs = []
    comments = ""
    in_curly = False
    take_next_line = False
    after_comment = False
    in_curly_lines = []
    next_lines_up_to_com = []
    befor_curly = []
    befor_curly_com = ""
    got_before_curly_comment = False
    take_line_reset = 5
    max_take_lines = take_line_reset

    for line in code: 

        if "{" in line:
            in_curly= True

        if after_comment and not in_curly:
            befor_curly.append(line)

        if in_curly :
            in_curly_lines.append(line)
            
            if not got_before_curly_comment:
                for l in befor_curly:
                    in_curly_lines.append(l)

                befor_curly = []
                befor_curly_com = comments
                comments = ""
                got_before_curly_comment = True
                take_next_line = False

        
        # Comment processing
        cm = get_comment_type(line)
        if cm is COMMENTTYPE.MULTILINE_START or cm is COMMENTTYPE.NATSPEC_START:
            comments += line
            take_next_line = False
            after_comment = False

        elif cm is COMMENTTYPE.MULTILINE_BETWEEN: 
            comments += line
            take_next_line = False
            after_comment = False
        
        elif cm is COMMENTTYPE.MULTILINE_END:
            comments += line
            after_comment = True

        elif cm is COMMENTTYPE.SINGLELINE_NATSP:
            comments += line
            take_next_line = True
            max_take_lines = take_line_reset

        elif cm is COMMENTTYPE.SINGLELINE :
            comments += line
            take_next_line = True
            max_take_lines = take_line_reset

        if (cm is COMMENTTYPE.NO_COMMENT or cm is COMMENTTYPE.SINGLE_INLINE) and take_next_line:
            if comments != "":
                comment_code_pairs.append([comments, [line]])
                comments = ""
            else: 
                cm, cd = comment_code_pairs[-1]

                has_curly = False
                for c in cd: 
                    if "{" in c:
                        has_curly = True
                if "}" in line:
                    if has_curly:
                        cd.append(line)
                        comment_code_pairs[-1] = [cm, cd]
                else:
                    cd.append(line)
                    comment_code_pairs[-1] = [cm, cd]
            
            max_take_lines -=1
            if "}" in line: 
                max_take_lines = 0
            take_next_line = True if max_take_lines>0 else False
            
    comment_code_pairs.append([befor_curly_com, in_curly_lines])

    return comment_code_pairs


def get_comments_code_blocks(file_path):
    all_blocks = []
    blocks = extract_blocks(file_path)  
    
    for blk in blocks[:-1]: # discard main file / block for duplications
        cp = extract_solidity_comment_and_code(blk)
        for cm, cd in cp:
            all_blocks.append([cm, "".join(cd)])

    last = blocks[-1] # main block
    cp = extract_solidity_comment_and_code(last)
    cm, cd  = cp[-1]
    all_blocks.append([cm, "".join(cd)])

    return all_blocks
    
def main():
    file_path = 'test/Storage.sol'  # Replace with the path to your Solidity file
    
    cp = get_comments_code_blocks(file_path)
    for cm, cd in cp:
        print('_'*200)
        print('Comment - Code Pair')
        print('comment\n', cm)
        print('code\n', ''.join(cd))
        print()

    # blocks = extract_blocks(file_path)
    # for blk in blocks[:-1]:
    #     print('_'*200)
    #     print('--- block ---')
    #     print(''.join(blk))
    #     print()
    #     print('--- Code comment ---')
    #     cp = extract_solidity_comment_and_code(blk)
    #     for cm, cd in cp:
    #         print('Comment - Code Pair')
    #         print('comment\n', cm)
    #         print('code\n', ''.join(cd))
    #         print()

    # last = blocks[-1] # main block
    # cp = extract_solidity_comment_and_code(last)
    # cm, cd  = cp[-1]
    # print('_'*200)
    # print('--- block ---')
    # print(''.join(last))

    # print('Last Comment - Code Pair')
    # print('last comment\n', cm)
    # print('last code\n', ''.join(cd))
    # print()
if __name__ == '__main__':
    main()