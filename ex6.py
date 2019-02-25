
import sublime_plugin
import sublime

import os, json, re

import shutil, tempfile



empty_root_node = {'alive_time':0,'isdir':True,'mtime':0,'exclude_patterns':[
    r'_.*'
]}

cache={
    'roots':{},
    'cur_time':{}
}

pats={
    'forin_capture_uislp':r"^\s*--\^\s*forin\s+([.\w /]+)\s*$"
}

compiled_re={
    'forin':re.compile(r"\s*--\^\s*forin\s+(.*[^\s])\s*"),
    'non_space_tokenizer':re.compile(r"[^\s]+")
}


verbosity={
    'debug':True,
    'default':True
}

def iter_to_list_match_groupx_start_end_s(iter_,*group_ids):
    list_={}
    for id_ in group_ids:
        list_[id_] = {}
        list_[id_]['str'] = []
        list_[id_]['start']  = []
        list_[id_]['end'] = []

    for match in iter_:
        for id_ in group_ids:
            list_[id_]['str'].append(match.group(id_))
            list_[id_]['start'].append(match.start(id_))
            list_[id_]['end'].append(match.end(id_))
    
    return list_


def print_in(indentx,s,tag = 'default'):
    if verbosity[tag]:
        print(indentx*'\t'+s)

def print_err(indentx,s):
    print(indentx*'\t'+" ERROR !! : "+s)

def fp_root_xsep_to_fp_tree_json(fp_root_xsep):
    return fp_root_xsep + os.sep + "_namodular" + os.sep + "tree.json" 

def get_root(fp_root_xsep):
    return cache['roots'][fp_root_xsep]

def is_file(node):
    if node['isdir']:
        return False
    else:
        return True

def is_dir(node):
    if node['isdir']:
        return True
    else:
        return False

def is_alive(fp_root_xsep,node):

    if cache['cur_time'][fp_root_xsep] == node['alive_time']:
        return True
    else:
        return False

def get_or_make_list(parent_node):
    if 'list' not in parent_node:
        parent_node['list'] = {}
    return parent_node['list']

def get_or_make_child_node(parent_node,name):
    list_ = get_or_make_list(parent_node)    
    if name not in list_:
        list_[name] = {
            'isdir':False,
            'alive_time':-1,
            'mtime':-1
        }
    return list_[name]

def listify_nodes_in_rb_slp(fp_root_xsep,rb_slp_node_xxsep,call_stack = 0):

    print_in(call_stack+1,"listify_nodes_in_rb_slp : ")

    list_ = []

    names = rb_slp_node_xxsep.split('/') if rb_slp_node_xxsep else []
    print_in(call_stack + 2," got names : " +str(names))

    cur_node = get_root(fp_root_xsep)
    list_.append(cur_node) 
    for name in names:
        cur_node = get_or_make_child_node(cur_node,name)
        list_.append(cur_node)     

    return list_


def get_or_make_alive_list_and_update_path(fp_root_xsep,rb_slp_node_xxsep,input_node,call_stack = 0):
    list_ = get_or_make_list(input_node)
    
    if ('alive_list_time' not in input_node):
        input_node['alive_list'] = {}
        input_node['alive_list_time'] = -1    

    alive_list = input_node['alive_list']

    cur_time = cache['cur_time'][fp_root_xsep]

    if input_node['alive_list_time'] != cur_time:
        has_changed = False

        for name in list_:
            if list_[name]['alive_time'] == cur_time:
                if name not in alive_list:
                    alive_list[name] = True
                    has_changed = True
            else :
                if name in alive_list:
                    alive_list.pop(name)
                    has_changed = True
        
        if has_changed:
            for node in listify_nodes_in_rb_slp(fp_root_xsep,rb_slp_node_xxsep,call_stack+1):
                print_in(call_stack,"changing mtime to :" + str(cur_time))
                node['mtime'] = cur_time

        input_node['alive_list_time'] = cache['cur_time'][fp_root_xsep]

    return input_node['alive_list']

def link_output_file(input_node,fp_file_xsep):
    if 'output_files' not in input_node:
        input_node['output_files'] = {}

    input_node['output_files'][fp_file_xsep] = {'mtime':-1,'input_mtime':-1}


def fp_to_rb_namestack(fp_root_xsep,fp_file_xsep):
    return [] if fp_root_xsep == fp_file_xsep else fp_file_xsep[(len(fp_root_xsep)+len(os.sep)):].split(os.sep)

def fp_to_node(fp_root_xsep,fp_node):
    return get_node_by_rb_namestack(fp_root_xsep,fp_to_rb_namestack(fp_root_xsep,fp_node))

def get_node_by_rb_namestack(fp_root_xsep,rb_namestack):

    node = cache['roots'][fp_root_xsep]

    for name in rb_namestack:
        node = get_or_make_child_node(node,name)

    return node


def open_or_make_json(fp_json,default = {}):
    count = 0
    obj = None
    while count < 3:
        print("attempting : " + fp_json)
        count += 1
        try:
            with open(fp_json) as f:
                obj = json.load(f)
        except: 
            obj = None
            print('oops')

        if obj is None:
            os.makedirs(os.path.dirname(fp_json), exist_ok=True)
            with open(fp_json, "w") as f:
                f.write(json.dumps(default))
        else:
            return obj

def save_or_make_json(fp_json,obj):
    os.makedirs(os.path.dirname(fp_json), exist_ok=True)
    with open(fp_json, "w") as f:
        f.write(json.dumps(obj))


def uislp_to_full_path(fp_root_xsep,fp_file_xsep,uislp,call_stack=0):
    
    unnorm_path = ""
    if uislp[0] == "/":
        unnorm_path = os.path.join(fp_root_xsep,os.path.normpath(uislp[1:]))
    else:
        unnorm_path = os.path.join(os.path.dirname(fp_file_xsep),os.path.normpath(uislp))


    print_in(call_stack," fp_file : " + fp_file_xsep + " uislp : " + uislp)
    print_in(call_stack,"got path" + os.path.normpath(unnorm_path))

    return os.path.normpath(unnorm_path)


lua_suffix = re.compile(r".*\.lua")
def is_lua_suffixed(name):
    if lua_suffix.match(name):
        return True 


def update_file_tree(fp_root_xsep,fp_file_xsep,parent_node,current_node,call_stack):
    
    print_in(call_stack,fp_file_xsep+" is alive")
    current_node['alive_time'] = cache['cur_time'][fp_root_xsep]
    
    if os.path.isdir(fp_file_xsep):
        
        print_in(call_stack+1," is a directory")
        dir_node = current_node
        dir_node['isdir'] = True

        # 실제 현재 폴더의 내용물을 갖고 온다. 
        # 그렇기 때문에 데스 마킹 없이도 데드 폴더는 안들어가게 된다.
        list_of_dir = os.listdir(fp_file_xsep)
        for name1 in list_of_dir :
            exclude_patterns_reres = None

            if 'exclude_patterns' in current_node:
                for pat in current_node['exclude_patterns']:
                    exclude_patterns_reres = re.match(pat,name1)
                    if exclude_patterns_reres:
                        print_in(call_stack+1,name1 + ' excluded by pattern :' + pat)
                        break
            if exclude_patterns_reres:
                continue
                
            child_node = get_or_make_child_node(current_node,name1)
            update_file_tree(fp_root_xsep, os.path.join(fp_file_xsep,name1),dir_node,child_node,call_stack+1)
    
    else:
        
        print_in(call_stack+1," NOT a directory")
        current_node['isdir'] = False            


def get_argstrxxws_s_from_file(fp_file,call_stack):
    argstrxxws_s = []
    with open(fp_file) as f:
        for line in f:
            print_in(call_stack,"> "+line[:len(line)-1],"debug")

            reres_forin = compiled_re['forin'].match(line)
            if reres_forin:
                argstrxxws = reres_forin_to_argstrxxws(reres_forin)
                print_in(call_stack,"got :" + argstrxxws,"debug")
                argstrxxws_s.append(argstrxxws)

    return argstrxxws_s


def get_or_make_cached_argstrxxws_s(file_node):
    if 'cached_argstrxxws_s' not in file_node:
        file_node["cached_argstrxxws_s"] = {}

    return file_node['cached_argstrxxws_s']


def reres_forin_to_argstrxxws(reres_forin):
    return reres_forin.group(1)



def reres_forin_to_uislp(reres_forin):

    argstrxxws = reres_forin_to_argstrxxws(reres_forin)

    iter_ = compiled_re['non_space_tokenizer'].finditer(argstrxxws)
    list_ = iter_to_list_match_groupx_start_end_s(iter_,0)


    str_list = list_[0]['str']
    len_list = len(str_list)
    idx = -1 

    uislp = None 

    while idx < len_list:
        idx += 1 
        chunck = str_list[idx]

        if chunck not in ["-r","-xself"]:
            uislp = argstrxxws[list_[0]['start'][idx]:]
            return uislp

def extract_uislp_s(fp_file,call_stack):

    with open(fp_file) as f:
        
        uislps = []

        for line in f:
            reres_forin = compiled_re['forin'].match(line)
            if reres_forin:
                
                uislp = reres_forin_to_uislp(reres_forin)
                
                if uislp:
                    uislps.append(uislp)

        return uislps                



def slp_a_to_b(fp_a_xsep,fp_b_xsep,call_stack):


    print_in(call_stack,"slp_a_to_b:")
    print_in(call_stack+1,fp_a_xsep)
    print_in(call_stack+1,fp_b_xsep)

    if fp_b_xsep.find(fp_a_xsep) == 0:
        if len(fp_b_xsep) == len(fp_a_xsep):
            return ""
        elif fp_b_xsep[len(fp_a_xsep)] == os.sep:
            return fp_b_xsep[(len(fp_a_xsep)+1):].replace(os.sep,'/')
    else:
        return None


def link_output_blocks(fp_root_xsep,fp_file_xsep,current_node,call_stack):

    print_in(call_stack,os.path.basename(fp_file_xsep)+" :")

    mtime = os.path.getmtime(fp_file_xsep)

    # print(str(current_node))
    if is_file(current_node) and is_lua_suffixed(fp_file_xsep):
        if (mtime != current_node['mtime']):
            print_in(call_stack+1,"parsing uislps :")
            
            uislps = extract_uislp_s(fp_file_xsep,call_stack)

            for uislp in uislps:
                fp_input_node = uislp_to_full_path(fp_root_xsep,fp_file_xsep,uislp,call_stack+2)
                print_in(call_stack+2,"interpreted to : "+fp_input_node)
                input_node_rb_namestack = fp_to_rb_namestack(fp_root_xsep,fp_input_node)
                input_node = get_node_by_rb_namestack(fp_root_xsep,input_node_rb_namestack)
                
                link_output_file(input_node,fp_file_xsep)

            current_node['mtime'] = mtime           
        else:
            print_in(call_stack+1,"no change since last traversal")
    elif current_node['isdir'] and 'list' in current_node:
        print_in(call_stack+1,"has list :")
        alive_list = get_or_make_alive_list_and_update_path(fp_root_xsep,slp_a_to_b(fp_root_xsep,fp_file_xsep,call_stack+1),current_node,call_stack+1)

        for name in alive_list:
            link_output_blocks(fp_root_xsep,os.path.join(fp_file_xsep,name),current_node['list'][name],call_stack+2)




def find_nth_x(str_,target_n,x):

    print(" in :"+str_ + " the " + str(target_n) + "-th "+x+" is at :")

    mag_ = abs(target_n)
    dir_ = 1 if target_n > 0 else -1
    idx = -1 if target_n > 0 else len(str_)

    count = 0

    while True:
        idx += dir_
        if idx < 0 or idx >= len(str_):
            break

        if str_[idx] == x:
            count += 1
            if count == mag_:
                print("      "+ str(count))
                return idx
    

def num_x(str_,x):
    count = 0
    for idx in range(0,len(str_)-1):
        if str_[idx] == x:
            count += 1
    
    return count


compiled_re['tokenize_printable_format_iter'] = re.compile(r"(?<!\\)(\\\\){0,}(?P<stoken>(\{\{)\s+"+r"(?P<xxws>(((?<!\})(\}))|[^}]|((?<!\\)\\(\\\\){0,}(\}\}))){1,})"+r"\s+\}\})")
compiled_re['nonspace_chunck_iter'] = re.compile(r"[^\s]+")
# compiled_re['tokenize_printable_format_iter'] = re.compile(r"(?<=(\\\\){0,})(\{\{)(((?<!\})(\}))|[^}]|(\\\}\})){1,}(?<!\\)(\}\})"))

compiled_re['typeA'] = re.compile(r"(n|y)(f|l)")
compiled_re['typeB'] = re.compile(r"(e|o)(?:([frib])((?:\+|-)\d+)?)(?:([frib])((?:\+|-)\d+)?)")

def pf_to_tokens(printable_format_xxws,call_stack = 0):
    iter_ = compiled_re['tokenize_printable_format_iter'].finditer(printable_format_xxws)
    list_ = iter_to_list_match_groupx_start_end_s(iter_,'xxws','stoken')

    tokens = []
    idx_stoken_args_xxws = -1
    prev_token_end = 0

    for stoken_args_xxws in list_['xxws']['str']:
        idx_stoken_args_xxws += 1

        print_in(call_stack,str(stoken_args_xxws))

        iter_1 = compiled_re['nonspace_chunck_iter'].finditer(stoken_args_xxws)
        list_1 = iter_to_list_match_groupx_start_end_s(iter_1,0)


        print_in(call_stack+1,str(list_1))


        chuncks = list_1[0]['str']
        starts = list_1[0]['start']
        ends = list_1[0]['end']

        stoken = {}

        idx = -1
        chunck = None
        passed_stoken = True

        def next():
            nonlocal idx
            nonlocal chunck
            idx += 1
            if idx < len(chuncks):
                chunck = chuncks[idx]
                return True
            else:
                idx = len(chuncks) -1 
                return False


        def get_chunk_sausage():
            if next():

                delim = chunck[0]
                
                start_idx = idx

                while chunck[-1] != delim and next():
                    pass

                end_idx = idx

                return stoken_args_xxws[starts[start_idx]:ends[end_idx]]

        while next():
            
            print_in(call_stack+1,chunck)

            passed = False
            
            if idx == 0:

                reres_A = compiled_re['typeA'].match(chunck)
                reres_B = compiled_re['typeB'].match(chunck)

                passed = False

                if reres_A:

                    stoken['target_idx'] = "start" if chunck[1]=='f' else "end"
                    stoken['should'] = True if chunck[0]=='y' else False

                    sausage = get_chunk_sausage()

                    if sausage:
                        stoken['str'] = sausage[1:-1]
                        passed = True 

                elif reres_B:

                    arg_names = ['which_eoi','from','from_add','to','to_add']
                    groups = reres_B.groups()

                    for i in range(0,len(arg_names)):

                        if i == 2 or i == 4:
                            if groups[i]:
                                int_ = int(groups[i][1:]) 
                                if groups[i][0] == '+':
                                    stoken[arg_names[i]] = int_
                                else:
                                    stoken[arg_names[i]] = int_ * -1
                            else :
                                stoken[arg_names[i]] = 0

                            
                        else:
                            stoken[arg_names[i]] = groups[i]

                    passed = True

                print_in(call_stack+1,"yes passed idx0") if passed else print_in(call_stack+1,"not passed idx0")

            else:
                option_name = chunck
                if chunck in ["-rei","-xrei","-sep"]:
                    
                    sausage = get_chunk_sausage()
                    print_in(call_stack+3,sausage)

                    if sausage and len(sausage) >= 3:
                        stoken[option_name] = sausage[1:-1]
                        passed = True

                elif chunck in ["-reog"]:
                    if next() and chunck.isdigit():
                        stoken[option_name] = int(chunck)
                        passed = True

                elif chunck[0] == '-' :
                    stoken[option_name] = True
                    passed = True

            if not passed :
                passed_stoken = False
                break

        if passed_stoken:

            tokens.append(printable_format_xxws[prev_token_end:list_['stoken']['start'][idx_stoken_args_xxws]])
            tokens.append(stoken)
            prev_token_end = list_['stoken']['end'][idx_stoken_args_xxws]
        

        print_in(call_stack,str(stoken))       

    tokens.append(printable_format_xxws[prev_token_end:])

    return tokens


def expand_B_tokens(tokens,fp_root_xsep,rb_slp_s,e_i_idx,call_stack):
    res_tokens = []
    # not str_
    
    for tok in tokens :

        if 'which_eoi' in tok:
            stok = tok
            
            which_eoi = stok['which_eoi']

            slp = rb_slp_s[which_eoi]
            num_sl = num_x(slp,'/') if slp else -1

            frib_idx = {
               
                "f":-10,
                "r":0,
                "i":e_i_idx if which_eoi == 'e' else num_sl,
                "b":num_sl + 1
            }

            if slp :

                sl_idx = {}

                last_sl_idx = num_sl + 1
                
                for k in ['from','to']:
                    sl_idx[k] = frib_idx[stok[k]] + stok[k+'_add']
                    if sl_idx[k] < 0 :
                        sl_idx[k] = 0
                    if sl_idx[k] > last_sl_idx :
                        sl_idx[k] = last_sl_idx
                  
                if sl_idx['from'] >= sl_idx['to']:
                    slp = ""
                else:

                    cidx = {}
                    for k in sl_idx:
                        if sl_idx[k] >= last_sl_idx:
                            cidx[k] = len(slp)
                        elif sl_idx[k] <= 0:
                            cidx[k] = -1 
                        else:
                            cidx[k] = find_nth_x(slp,sl_idx[k],'/')

                    slp = slp[cidx['from']+1:cidx['to']]        
            else:
                slp = ""

            reires = None

            if 'compiled-xrei' in stok:
                xreires = stok['compiled-xrei'].match(slp)
                if xreires :
                    return None
            
            if 'compiled-rei' in stok:
                reires = stok['compiled-rei'].match(slp)
                if not reires :
                    return None

            if '-xf' in stok:
                dot_pos = find_nth_x(slp,-1,'.')
                slp = slp[:dot_pos]

            if '-sep' in stok:
                slp = slp.replace('/',stok['-sep'])

            if '-reog' in stok and reires:
                slp = reires.group(stok['-reog'])

            if '-iv' in stok:
                slp = ""

            res_tokens.append(slp)

        else:
            res_tokens.append(tok)

    return res_tokens

def expand_A_tokens(tokens,idx,last_idx):
    res_tokens = []
    # not str_
    
    for tok in tokens :
        if 'target_idx' in tok:
            stok = tok

            target_idx = 0 if tok['target_idx'] == 'start' else last_idx

            should = tok['should']
            
            if idx == target_idx:
                if should:
                    res_tokens.append(stok['str'])
            else:
                if not should:
                    res_tokens.append(stok['str'])

        else:
            res_tokens.append(tok)

    return res_tokens



def join_slp(a,b):
    if a and b:
        return a + '/' + b 
    else:
        return a + b

def join_osp(a,b):
    return os.path.join(a,b)

def list_rb_slp_s_r(fp_root_xsep,rb_slp_node,node,list_):

    alive_list = get_or_make_alive_list_and_update_path(fp_root_xsep,rb_slp_node,node)

    for name in alive_list:
        child_rb_slp = join_slp(rb_slp_node,name)
        if is_dir(node['list'][name]):
            list_rb_slp_s_r(fp_root_xsep,child_rb_slp,node['list'][name],list_)
        else:
            list_.append(child_rb_slp)

    return list_




def fill_block(fp_root_xsep,rb_slp_input_dir_xxsep,input_node,rb_slp_outfile,tmp_file,indent,pf_xxws,call_stack):




    
    print_in(call_stack,"start of fill_block :")
    o = {"fp_root_xsep":fp_root_xsep,"rb_slp_input_dir_xxsep":rb_slp_input_dir_xxsep,"input_node":input_node,"rb_slp_outfile":rb_slp_outfile,"indent":indent,"pf_xxws":pf_xxws,"call_stack":call_stack}
    print_in(call_stack + 1,"args :")
    for k in o:
        print_in(call_stack+2, ""+k + " : " + str(o[k]))

    tokens = pf_to_tokens(pf_xxws)

    idx = -1
    while idx < len(tokens):
        tok = tokens[idx]
        
        if not isinstance(tok, str):
            compiled_tok = {}
            for k in tok:
                if k in ['-rei','-xrei']:
                    compiled_tok['compiled'+k] = re.compile(tok[k])    
                else:
                    compiled_tok[k] = tok[k]

            tokens[idx] = compiled_tok

        idx += 1

    list_ = list_rb_slp_s_r(fp_root_xsep,rb_slp_input_dir_xxsep,input_node,[])
    
    rb_slp_s = {
        'o':rb_slp_outfile,
        'e':None
    }

    e_i_idx = num_x(rb_slp_input_dir_xxsep,'/') + 1 if rb_slp_input_dir_xxsep else 0


    passed = []
    
    for rb_slp in list_:
        
        rb_slp_s['e'] = rb_slp
        #def tokens_to_output(tokens,fp_root_xsep,rb_slp_s,e_i_idx,idx,last_idx):
        output = expand_B_tokens(tokens,fp_root_xsep,rb_slp_s,e_i_idx,call_stack)
        passed.append(output) if output else None
    
    idx = -1
    last_idx = len(passed) - 1
    for tokens in passed:
        idx += 1
        tokens = expand_A_tokens(tokens,idx,last_idx)

        line = indent + "".join(tokens)
        tmp_file.write(line + '\n')



def write_to_file(fp_root_xsep,fp_input_dir_xsep,rb_slp_input_dir_xxsep,input_node,fp_output_file,rb_slp_outfile,call_stack):
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
        with open(fp_output_file) as src_file:
            
            expect = None
            line_buffer = []
            printable_format_xxws = None
            indent = ""

            for line in src_file:


                print_in(call_stack+0,"got line "+line[:-1])
                print_in(call_stack+0,"expecting : "+str(expect))

                if expect == "printable_format":
                    reres_printable_format = re.match(r"(\s*)-->\s*(.*[^\s])\s*",line)
                    if reres_printable_format :
                        print_in(call_stack+1,"got a printable_format")
                        indent = reres_printable_format.group(1)
                        printable_format_xxws = reres_printable_format.group(2)
                        tmp_file.write(line)
                        expect = "end_or_nots"
                    else :
                        print_in(call_stack+1,"didn't meet expectation")
                        line_buffer.append(line)
                        expect = "invalidation"
                
                elif expect == "end_or_nots":
                    reres_namodular_syntax = re.match(r"\s*--[><^$].*",line)
                    if reres_namodular_syntax:
                        print_in(call_stack+1,"got a reres_namodular_syntax")
                        reres_block_end = re.match(r"\s*--\$.*",line)
                        if reres_block_end :
                            print_in(call_stack+2,"got a reres_block_end")
                            # def fill_block(fp_root_xsep,rb_slp_input_dir_xxsep,input_node,rb_slp_outfile,tmp_file,indent,pf_xxws,call_stack):
                            fill_block(fp_root_xsep,rb_slp_input_dir_xxsep,input_node,rb_slp_outfile,tmp_file,indent,printable_format_xxws,call_stack)
                            line_buffer = []
                            tmp_file.write(line)
                            expect = None
                        else:
                            print_in(call_stack+2,"didn't get a reres_block_end")
                            expect = "invalidation"
                    else:
                        print_in(call_stack+1,"didn't get a reres_namodular_syntax just appending to buffer")
                        line_buffer.append(line)
                elif expect == "invalidation":
                    to_check = [line]
                    to_check.append(line_buffer[0]) if line_buffer else False 
                    reres_invalidation = None
                    for line1 in to_check:
                        reres_invalidation = re.match(r"\s*--<\s*invalid\scmd\sblock(\s*:.*)?\s*",line1)
                        if reres_invalidation:
                            break

                    if not reres_invalidation:
                        print_in(call_stack+1,"invalidation is not marked, marking .. ")
                        tmp_file.write("--< invalid cmd block \n")
                    for line1 in line_buffer:
                        print_in(call_stack+1,"releasing line : " + line1[:-1])
                        tmp_file.write(line1)
                    line_buffer = []
                    tmp_file.write(line)
                    expect = None
                else:
                    tmp_file.write(line)

                reres_forin = compiled_re['forin'].match(line)
                if reres_forin:
                    uislp = reres_forin_to_uislp(reres_forin)
                    fp_input_dir_uislp = uislp_to_full_path(fp_root_xsep,fp_output_file,uislp,call_stack+2)
                    print_in(call_stack+1, "comparing "+fp_input_dir_xsep + " & " + fp_input_dir_uislp)
                    if fp_input_dir_xsep == fp_input_dir_uislp:
                        expect = "printable_format" 

            if line_buffer:

                if not re.match(r"\s*--<\s*invalid\scmd\sblock(\s*:.*)?\s*",line_buffer[0]):
                    tmp_file.write("--< invalid cmd block \n")

                for line in line_buffer:
                    tmp_file.write(line)

    shutil.copystat(fp_output_file, tmp_file.name)
    shutil.move(tmp_file.name, fp_output_file)





def out_put_r(fp_root_xsep,fp_input_dir_xsep,rb_slp_input_dir_xxsep,node,call_stack):

    print_in(call_stack,"out_put_r : "+fp_root_xsep)

    if ( 'output_files' in node ):
        
        to_del = []

        for fp in node['output_files']:
            print_in(call_stack+1,"outputing to : "+fp)
            try:
                output_file_mtime = os.path.getmtime(fp)
            except Exception as e:
                to_del.append(fp)
                continue

            if output_file_mtime != node['output_files'][fp]['mtime'] or node['output_files'][fp]['input_mtime'] != node['mtime']: 
                #def write_to_file(fp_root_xsep,fp_input_dir_xsep,rb_slp_input_dir_xxsep,input_node,fp_output_file,rb_slp_outfile,call_stack):
                write_to_file(fp_root_xsep,fp_input_dir_xsep,rb_slp_input_dir_xxsep,node,fp,slp_a_to_b(fp_root_xsep,fp,call_stack+1),call_stack+1)
                node['output_files'][fp]['mtime'] = output_file_mtime
                node['output_files'][fp]['input_mtime'] = node['mtime']

        for fp in to_del:
            node['output_files'].pop(fp)

    if ( 'list' in node ): 
        for name in node['list']:
            child = node['list'][name]
            fp_child = os.path.join(fp_input_dir_xsep,name)
            out_put_r(fp_root_xsep,fp_child,join_slp(rb_slp_input_dir_xxsep,name),child,call_stack+1)

 


def reset(fp_root_xsep):
    path = os.path.join(fp_root_xsep,"_namodular") 
    try:
        shutil.rmtree(path)
    except:
        print("failed to remove : " + path)
        pass
    
    print("reseting all storage")
    global cache
    cache['roots'][fp_root_xsep] = None

class ex6Command(sublime_plugin.TextCommand):
    
    def get_window_path(self):
        window = self.view.window()
        for item in window.folders():
            return item


    def run(self,edit,should_reset=False):
        fp_root_xsep = self.get_window_path()

        if should_reset:
            reset(fp_root_xsep)
            return  
        
        fp_tree_json = fp_root_xsep_to_fp_tree_json(fp_root_xsep)
        if fp_root_xsep not in cache['roots'] or not cache['roots'][fp_root_xsep]:  
            cache['roots'][fp_root_xsep] = open_or_make_json(fp_tree_json,empty_root_node)
            if not cache['roots'][fp_root_xsep]:
                print("cannot load or make tree.json")
                return 

        root = cache['roots'][fp_root_xsep]


        cache['cur_time'][fp_root_xsep] = root['alive_time']+1

        update_file_tree(fp_root_xsep,fp_root_xsep,None,root,0)

        link_output_blocks(fp_root_xsep,fp_root_xsep,root,0)

        # (fp_root_xsep,fp_input_dir_xsep,rbp_input_dir_xxsep,input_node,call_stack):
        out_put_r(fp_root_xsep,fp_root_xsep,"", root,0)

        with open(fp_root_xsep_to_fp_tree_json(fp_root_xsep),"w") as f:
            f.write(json.dumps(root)) 

