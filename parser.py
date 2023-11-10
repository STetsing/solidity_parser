from enum import Enum
import argparse
import subprocess
import os

parse_args = argparse.ArgumentParser()
parse_args.add_argument('--file', type=str, default='./test_files/Storage.sol')

class COMMENTTYPE(Enum): 
    SINGLELINE=0
    SINGLE_INLINE=1
    MULTILINE_START=2
    MULTILINE_BETWEEN=3
    MULTILINE_END=4
    NATSPEC_START=5
    NO_COMMENT=6
    SINGLELINE_NATSP=7

class Fragment():

    def __init__(self, parent_frag=None) -> None:
        self.parent_frag = parent_frag
        self.has_parent = True if parent_frag is not None else False
        self.data = []
        self.comments = []
        self.sub_fragments = []

    def add(self, line):
        self.data.append(line)
    
    def append_data(self, data):
        for l in data:
            self.add(l)

def get_file_content(filename):
    with open(filename, 'r') as fl:
        data = fl.readlines()
    return  data

def prettify(filename):
    try:
        cmd = ["npx", "prettier", "--write", "--plugin=prettier-plugin-solidity", f'{filename}']
        p = subprocess.run(cmd,
            cwd='./',
            shell=False,  
            stderr=subprocess.DEVNULL,
            capture_output = True,
            universal_newlines=False)
        if p.stdout == '':
            print("WARNING: Error occured during the prettification")
    except Exception as ex:
        print("WARNING: Error occured during the prettification")

   

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

def fragment_code(data):
    unframed_code = []
    ufcs = []
    fragments = []
    in_fragment = 0
    main_frag = Fragment()
    subfrag_curr = None
    in_comment = False
    curr_comments = []
    closed = True
    function_multilines = []

    for line in data:

        # Comment processing
        cm = get_comment_type(line)
        if cm is COMMENTTYPE.MULTILINE_START or cm is COMMENTTYPE.NATSPEC_START:
            in_comment = True
            curr_comments.append(line)
            continue

        elif in_comment and cm is COMMENTTYPE.MULTILINE_BETWEEN: 
            curr_comments.append(line)
            continue
        
        elif in_comment and cm is COMMENTTYPE.MULTILINE_END:
            curr_comments.append(line)
            in_comment = False
            continue

        elif cm is COMMENTTYPE.SINGLELINE_NATSP or cm is COMMENTTYPE.SINGLELINE_NATSP:
            curr_comments.append(line)
            continue            

        elif cm is COMMENTTYPE.SINGLE_INLINE:
            s = line.split('//')
            code = s[0]
            com = list(s[1:])
            f = Fragment()
            f.add(code)
            f.comments.append(com)
            fragments.append([com, [code]])
            continue

        if cm is COMMENTTYPE.SINGLELINE and not closed and in_fragment:
            if subfrag_curr is not None:
                subfrag_curr.comments.append(line)
                curr_comments = []
            continue

        elif cm is COMMENTTYPE.SINGLELINE and closed:
            curr_comments.append(line)
            continue
        
        elif cm is COMMENTTYPE.SINGLELINE and not in_fragment:
            if 'SPDX' in line: # ignore comments with lisence
                continue
            curr_comments.append(line)
            continue


        # opened and closed curly bracked processing in single line     
        if '{' in line and '}' in line and in_fragment:
            f = Fragment()
            f.add(line)
            [f.comments.append(c) for c in curr_comments]
            curr_comments = []
            main_frag.sub_fragments.append(f)
            continue

        elif '{' in line and '}' in line:
            f = Fragment()
            f.add(line)
            [f.comments.append(c) for c in curr_comments]
            curr_comments = []
            main_frag.sub_fragments.append(f)
            continue


        # opened curly bracked processing in single line     
        if '{' in line and not in_fragment:
            if len(ufcs)>0:
                f = Fragment()
                f.append_data(ufcs)
                unframed_code.append(ufcs)
                fragments.append([[], f.data])
                ufcs = []


            in_fragment += 1
            closed = False
            subfrag_curr = main_frag
            [main_frag.comments.append(c) for c in curr_comments]
            curr_comments = []
        
        elif '{' in line and in_fragment:
            if len(ufcs)>0:
                unframed_code.append(ufcs)
                ufcs = []

            # start a new fragment
            in_fragment += 1
            closed = False
            # only allow up to level 2 collection
            if in_fragment == 2:
                subfrag_curr = Fragment(subfrag_curr)
            
            [subfrag_curr.comments.append(c) for c in curr_comments]
            curr_comments = []
            
            # Multiline functions 
            if len(function_multilines):
                subfrag_curr.append_data(function_multilines)
                function_multilines = []

            main_frag.sub_fragments.append(subfrag_curr)
        
        # closed curly bracked processing in single line     
        elif '}' in line:
            closed = True
            if in_fragment == 1:
                for frag in main_frag.sub_fragments:
                    main_frag.append_data(frag.data)
                
                main_frag.add(line)
                fragments.append([main_frag.comments, main_frag.data])

                for frag in main_frag.sub_fragments:
                    fragments.append([frag.comments, frag.data])

                in_fragment = 0
                # enable multi level. Not only 1 contract
                main_frag = Fragment()

            if subfrag_curr != None and in_fragment>0:
                in_fragment -= 1
        
        # between fragments
        if closed and ("function" in line or len(function_multilines)):
            function_multilines.append(line)
            continue 
        
        if len(curr_comments)>0 and closed:
            f = Fragment()
            f.add(line)
            [f.comments.append(c) for c in curr_comments]
            curr_comments = []
            main_frag.sub_fragments.append(f)
            continue

        if in_fragment==0 and '{' not in line and '}' not in line:
            ufcs.append(line)
        else:
            if in_fragment > 0:
                subfrag_curr.add(line)

    # filter only commented code
    comment_codes = []
    for cm , co in fragments:
        if len(cm):
            comment_codes.append([cm, co])
    return comment_codes #,fragments, unframed_code


def main(args):
    prettify(args.file)
    data = get_file_content(args.file)
    f= fragment_code(data)

if __name__=='__main__':
    args = parse_args.parse_args()
    main(args)