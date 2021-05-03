from collections import OrderedDict
from auxilliary_functions import *

#memory is a dictionary with key=location in hex-string and value=data in hex-string
memory = OrderedDict()

text_pointer = "0x00000000"
data_pointer = "0x10000000"
stack_pointer = "0x7FFFFFF0"


###   This data needs to be integrated into the main program
cache_size = 128
cache_block_size = 16
blocks_per_set = 2
block_placement_type = 'set_associative'
victim_block_counter = 0
victim_block = []
block_access_counter = 0
block_access = []
num_memory_accesses = 0
num_cache_hits = 0
num_cache_misses = 0


###

#instruction_cache = {}
#data_cache = {}

def add_text_to_memory(instruction):
    global text_pointer
    memory[text_pointer] = instruction[-2:]
    text_pointer = "0x" + format((int(text_pointer, 16) + 1), "0>8x").upper()  # incrementing the text pointer
    memory[text_pointer] = instruction[-4:-2]
    text_pointer = "0x" + format((int(text_pointer, 16) + 1), "0>8x").upper()  # incrementing the text pointer
    memory[text_pointer] = instruction[-6:-4]
    text_pointer = "0x" + format((int(text_pointer, 16) + 1), "0>8x").upper()  # incrementing the text pointer
    memory[text_pointer] = instruction[-8:-6]
    text_pointer = "0x" + format((int(text_pointer, 16) + 1), "0>8x").upper()  # incrementing the text pointer

def add_data_before(data, no_of_byte=4):
    global data_pointer
    if no_of_byte == 1:
        memory[data_pointer] = data[-2:]
        data_pointer = "0x" + format((int(data_pointer, 16) + 1), "0>8x").upper()  # incrementing the location by one for next byte

    # For storing Half Word Data like in sh
    elif no_of_byte == 2:
        memory[data_pointer] = data[-2:]
        data_pointer = "0x" + format((int(data_pointer, 16) + 1), "0>8x").upper()  # incrementing the location by one for next byte
        memory[data_pointer] = data[-4:-2]
        data_pointer = "0x" + format((int(data_pointer, 16) + 1),"0>8x").upper()  # incrementing the location by one for next byte

    # For storing Word Data like in sw
    elif no_of_byte == 4:
        memory[data_pointer] = data[-2:]
        data_pointer = "0x" + format((int(data_pointer, 16) + 1), "0>8x").upper()  # incrementing the location by one for next byte
        memory[data_pointer] = data[-4:-2]
        data_pointer = "0x" + format((int(data_pointer, 16) + 1), "0>8x").upper()  # incrementing the location by one for next byte
        memory[data_pointer] = data[-6:-4]
        data_pointer = "0x" + format((int(data_pointer, 16) + 1), "0>8x").upper()  # incrementing the location by one for next byte
        memory[data_pointer] = data[-8:-6]
        data_pointer = "0x" + format((int(data_pointer, 16) + 1), "0>8x").upper()  # incrementing the location by one for next byte

# Adding data of given bit in a given memory location
def add_data_to_memory(data, location, no_of_byte):
    if no_of_byte == 1:
        memory[location] = data[-2:]

    # For storing Half Word Data like in sh
    elif no_of_byte == 2:
        memory[location] = data[-2:]
        location = "0x" + format((int(location, 16) + 1), "0>8x").upper()  # incrementing the location by one for next byte
        memory[location] = data[-4:-2]

    # For storing Word Data like in sw
    elif no_of_byte == 4:
        memory[location] = data[-2:]
        location = "0x" + format((int(location, 16) + 1), "0>8x").upper()  # incrementing the location by one for next byte
        memory[location] = data[-4:-2]
        location = "0x" + format((int(location, 16) + 1), "0>8x").upper()  # incrementing the location by one for next byte
        memory[location] = data[-6:-4]
        location = "0x" + format((int(location, 16) + 1), "0>8x").upper()  # incrementing the location by one for next byte
        memory[location] = data[-8:-6]

# Getting values for a given memory location and the number of bytes, can be used for lw, lh, lb
def get_data_from_memory(location, no_of_byte):
    if location in memory.keys():
        value = ""
        for i in reversed(range(no_of_byte)):
            value = memory[location] + value
            location = "0x" + format((int(location, 16) + 1), "0>8x").upper()

        value = "0x"+format(value, "0>8")
        return value
    # print("Error")
    return "0x00000000"



def get_text_memory_file():
    #print("Text Memory\n")
    Inst_Mem = OrderedDict()
    for mem, val in memory.items():
        if int(mem,16) < int("0x10000000",16):
            #print(mem, ":", val)
            Inst_Mem[mem] = val
        else:
            break
    #print('\n')
    return Inst_Mem

def get_data_memory_file():
    #print("Data Memory\n")
    data_p = "0x10000000"
    Data_Mem = OrderedDict()
    Stack_Mem = OrderedDict()
    while data_p in memory.keys():
        #print(data_p, ":",memory[data_p])
        Data_Mem[data_p] = memory[data_p]
        data_p = "0x" + format((int(data_p, 16) + 1), "0>8x").upper()

    #print("\nStack Memory\n")
    st_p = "0x" + format((int("0x7FFFFFF0", 16) - 4), "0>8x").upper()
    while st_p in memory.keys():
        #print(st_p, ":", memory[st_p])
        Stack_Mem[st_p] = memory[st_p]
        st_p = "0x" + format((int(st_p, 16) - 1), "0>8x").upper()
        
    return Data_Mem, Stack_Mem



# Functions to make the instruction and data caches
# Both cache_size and cache_block_size are specified in bytes

def make_cache() :

    global cache_size, cache_block_size, blocks_per_set, block_placement_type

    cache = []                      # 1D (for direct mapped) & 2D (for set & fully associative) list storing the data
    tag_array = []                  # 1D (for direct mapped) & 2D (for set & fully associative) list storing the tags of each block
    block_validity = []             # 1D (for direct mapped) & 2D (for set & fully associative) list indicating whether that block has stored any data or not
    block_status = []               # 1D (for direct mapped) & 2D (for set & fully associative) list storing status (as per LRU policy)of each block in a set

    if block_placement_type == 'set_associative' or  block_placement_type == 'fully_associative':
        if block_placement_type == 'fully_associative' :
            blocks_per_set = cache_size//cache_block_size
        for i in range(cache_size//(cache_block_size*blocks_per_set)) :
            cache.append([])
            tag_array.append([])
            block_validity.append([])
            block_status.append([])
            status_initializer = 0
            for j in range(blocks_per_set) :
                cache[i].append('00'*cache_block_size)
                tag_array[i].append('0x' + '0'*8)
                block_validity[i].append('invalid')
                block_status[i].append(status_initializer)
                status_initializer += 1

    elif block_placement_type == 'direct_mapped' :
        for i in range(cache_size//cache_block_size) :
            cache.append('00'*cache_block_size)
            tag_array.append('0x' + '0'*8)
            block_validity[i].append('invalid')

    return cache, tag_array, block_status, block_validity


instruction_cache = {}
data = make_cache()
instruction_cache['cache'] = data[0]
instruction_cache['tag_array'] = data[1]
instruction_cache['block_status'] = data[2]
instruction_cache['block_validity'] = data[3]


data_cache = {}
data = make_cache()
data_cache['cache'] = data[0]
data_cache['tag_array'] = data[1]
data_cache['block_status'] = data[2]
data_cache['block_validity'] = data[3]



def get_tag_index_offest(actual_address) :

    global cache_size, cache_block_size, blocks_per_set, block_placement_type
    num_blocks = cache_size//cache_block_size

    block_size_bits = cache_block_size*8
    address_int = int(actual_address,16)
    tag = bounding_hex(block_size_bits*(address_int//block_size_bits))
    if block_placement_type == 'direct_mapped' :
        index = None
    else :
        index = (address_int//block_size_bits)%(num_blocks//blocks_per_set)
    offset = (int(actual_address,16)-int(tag,16))//8                          
    return tag, index, offset


def read_block_from_memory(tag_address) :

    global cache_size, cache_block_size, blocks_per_set, block_placement_type

    block_of_data = get_data_from_memory(tag_address,cache_block_size)
    return block_of_data


# Reads from the caches following LRU Policy

def read_from_instruction_cache(read_address, index, offest, num_bytes) :

    global cache_size, cache_block_size, blocks_per_set, block_placement_type, num_memory_accesses, num_cache_hits, num_cache_misses, victim_block_counter, victim_block, block_access_counter, block_access
    num_memory_accesses += 1

    final_data = None

    if block_placement_type == 'set_associative' or block_placament_type == 'fully_associative' :

        if block_placement_type == 'fully_associative' :
            blocks_per_set = cache_size//cache_block_size
            index = 0

        match_found = False
        way_number = 0

        for i in range(blocks_per_set) :
            if instruction_cache['tag_array'][index][i] == read_address and instruction_cache['block_validity'][index][i] != 'invalid' :
                match_found = True
                way_number = i
                break

        if match_found == True :
            num_cache_hits += 1
            final_data = '0x' + instruction_cache['cache'][index][way_number][offest:offset+num_bytes*2]
            initial_status = instruction_cache['block_status'][index][way_number]
            for i in range(blocks_per_set) :
                if instruction_cache['block_status'][index][i] > initial_status :
                    instruction_cache['block_status'][index][i] -= 1
            instruction_cache['block_status'][index][way_number] = blocks_per_set - 1
            block_access_counter += 1
            block_access.append(instruction_cache['cache'][index][way_number])
            return final_data
        else :
            num_cache_misses += 1
            final_data = get_data_from_memory(bounding_hex(int(read_address,16)+offest), num_bytes)
            block_of_data = read_block_from_memory(read_address)
            block_access_counter += 1
            block_access.append(block_of_data)
            for i in range(blocks_per_set) :
                if instruction_cache['block_status'][index][i] == 0 :
                    if instruction_cache['block_validity'][index][i] == 'valid' :
                        victim_block_counter += 1
                        victim_block.append(instruction_cache['cache'][index][i])
                    instruction_cache['block_validity'][index][i] = 'valid'
                    instruction_cache['tag_array'][index][i] = read_address
                    instruction_cache['cache'][index][i] = block_of_data
                    way_number = i
                    break
            for i in range(blocks_per_set) :
                if i == way_number :
                    continue
                instruction_cache['block_status'][index][i] -= 1
            instruction_cache['block_status'][index][way_number] = block_index - 1
            return final_data

    else :

        num_blocks = cache_size//cache_block_size
        match_found = False

        if instruction_cache['tag_array'][index] == read_address and instruction_cache['block_validity'][index] != 'invalid' :
            match_found = True

        if match_found == True :
            num_cache_hits += 1
            final_data = '0x' + instruction_cache['cache'][index][offest:offset+num_bytes*2]
            block_access_counter += 1
            block_access.append(instruction_cache['cache'][index])
            return final_data
        else :
            num_cache_misses += 1
            final_data = get_data_from_memory(bounding_hex(int(read_address,16)+offest), num_bytes)
            block_of_data = read_block_from_memory(read_address,cache_block_size)
            block_access_counter += 1
            block_access.append(block_of_data)
            if instruction_cache['block_validity'][index] == 'valid' :
                victim_block_counter += 1
                victim_block.append(instruction_cache['cache'][index])
            instruction_cache['tag_array'][index] = read_address
            instruction_cache['cache'][index] = block_of_data
            instruction_cache['block_validity'][index] = 'valid'
            return final_data





def read_from_data_cache(read_address, index, offest, num_bytes) :

    global cache_size, cache_block_size, blocks_per_set, block_placement_type, num_memory_accesses, num_cache_hits, num_cache_misses, victim_block_counter, victim_block, block_access_counter, block_access
    num_memory_accesses += 1

    final_data = None

    if block_placement_type == 'set_associative' or block_placament_type == 'fully_associative' :

        if block_placement_type == 'fully_associative' :
            blocks_per_set = cache_size//cache_block_size
            index = 0

        match_found = False
        way_number = 0

        for i in range(blocks_per_set) :
            if data_cache['tag_array'][index][i] == read_address and data_cache['block_validity'][index][i] != 'invalid' :
                match_found = True
                way_number = i
                break

        if match_found == True :
            num_cache_hits += 1
            final_data = '0x' + data_cache['cache'][index][way_number][offest:offset+num_bytes*2]
            initial_status = data_cache['block_status'][index][way_number]
            for i in range(blocks_per_set) :
                if data_cache['block_status'][index][i] > initial_status :
                    data_cache['block_status'][index][i] -= 1
            data_cache['block_status'][index][way_number] = blocks_per_set - 1
            block_access_counter += 1
            block_access.append(data_cache['cache'][index][way_number])
            return final_data
        else :
            num_cache_misses += 1
            final_data = get_data_from_memory(bounding_hex(int(read_address,16)+offest), num_bytes)
            block_of_data = read_block_from_memory(read_address,cache_block_size)
            block_access_counter += 1
            block_access.append(block_of_data)
            for i in range(blocks_per_set) :
                if data_cache['block_status'][index][i] == 0 :
                    if data_cache['block_validity'][index][i] == 'valid' :
                        victim_block_counter += 1
                        victim_block.append(data_cache['cache'][index][i])
                    data_cache['block_validity'][index][i] = 'valid'
                    data_cache['tag_array'][index][i] = read_address
                    data_cache['cache'][index][i] = block_of_data
                    way_number = i
                    break
            for i in range(blocks_per_set) :
                if i == way_number :
                    continue
                data_cache['block_status'][index][i] -= 1
            data_cache['block_status'][index][way_number] = block_index - 1
            return final_data

    else :

        num_blocks = cache_size//cache_block_size
        match_found = False

        if data_cache['tag_array'][index] == read_address and data_cache['block_validity'][index] != 'invalid' :
            match_found = True

        if match_found == True :
            num_cache_hits += 1
            final_data = '0x' + data_cache['cache'][index][offest:offset+num_bytes*2]
            block_access_counter += 1
            block_access.append(data_cache['cache'][index])
            return final_data
        else :
            num_cache_misses += 1
            final_data = get_data_from_memory(bounding_hex(int(read_address,16)+offest), num_bytes)
            block_of_data = read_block_from_memory(read_address,cache_block_size)
            block_access_counter += 1
            block_access.append(block_of_data)
            if data_cache['block_validity'][index] == 'valid' :
                victim_block_counter += 1
                victim_block.append(data_cache['cache'][index])
            data_cache['tag_array'][index] = read_address
            data_cache['cache'][index] = block_of_data
            data_cache['block_validity'][index] = 'valid'
            return final_data




def write_to_data_cache(read_address, index, offest, num_bytes, new_data) :

    global cache_size, cache_block_size, blocks_per_set, block_placement_type, num_memory_accesses, num_cache_hits, num_cache_misses, victim_block_counter, victim_block, block_access_counter, block_access
    num_memory_accesses += 1

    if block_placement_type == 'set_associative' or block_placament_type == 'fully_associative' :

        if block_placement_type == 'fully_associative' :
            blocks_per_set = cache_size//cache_block_size
            index = 0

        match_found = False
        way_number = 0

        for i in range(blocks_per_set) :
            if data_cache['tag_array'][index][i] == read_address and data_cache['block_validity'][index][i] != 'invalid' :
                match_found = True
                way_number = i
                break

        if match_found == True :
            num_cache_hits += 1
            initial_status = data_cache['block_status'][index][way_number]
            for i in range(blocks_per_set) :
                if data_cache['block_status'][index][i] > initial_status :
                    data_cache['block_status'][index][i] -= 1
            data_cache['block_status'][index][way_number] = blocks_per_set - 1
            data_cache['cache'][index][way_number][offest:offset+num_bytes*2] = new_data[-(num_bytes*2):]
            block_access_counter += 1
            block_access.append(data_cache['cache'][index][way_number])
            add_data_to_memory(new_data[-(num_bytes*2):],bounding_hex(int(read_address,16)+offest),num_bytes)
        else :
            num_cache_misses += 1
            add_data_to_memory(new_data[-(num_bytes*2):],bounding_hex(int(read_address,16)+offest),num_bytes)
            block_of_data = read_block_from_memory(read_address,cache_block_size)
            block_access_counter += 1
            block_access.append(block_of_data)
            for i in range(blocks_per_set) :
                if data_cache['block_status'][index][i] == 0 :
                    if data_cache['block_validity'][index][i] == 'valid' :
                        victim_block_counter += 1
                        victim_block.append(data_cache['cache'][index][i])
                    data_cache['block_validity'][index][i] = 'valid'
                    data_cache['tag_array'][index][i] = read_address
                    data_cache['cache'][index][i] = block_of_data
                    way_number = i
                    break
            for i in range(blocks_per_set) :
                if i == way_number :
                    continue
                data_cache['block_status'][index][i] -= 1
            data_cache['block_status'][index][way_number] = block_index - 1

    else :

        num_blocks = cache_size//cache_block_size
        match_found = False

        if data_cache['tag_array'][index] == read_address and data_cache['block_validity'][index] != 'invalid' :
            match_found = True

        if match_found == True :
            num_cache_hits += 1
            data_cache['cache'][index][offest:offset+num_bytes*2] = new_data[-(num_bytes*2):]
            block_access_counter += 1
            block_access.append(data_cache['cache'][index])
            add_data_to_memory(new_data[-(num_bytes*2):],bounding_hex(int(read_address,16)+offest),num_bytes)
        else :
            num_cache_misses += 1
            add_data_to_memory(new_data[-(num_bytes*2):],bounding_hex(int(read_address,16)+offest),num_bytes)
            block_of_data = read_block_from_memory(read_address,cache_block_size)
            block_access_counter += 1
            block_access.append(block_of_data)
            if data_cache['block_validity'][index] == 'valid' :
                victim_block_counter += 1
                victim_block.append(data_cache['cache'][index])
            data_cache['tag_array'][index] = read_address
            data_cache['cache'][index] = block_of_data
            data_cache['block_validity'][index] = 'valid'


def read_data_from_memory(actual_address, num_bytes, cache_type) :

    global cache_size, cache_block_size, blocks_per_set, block_placement_type

    num_blocks = cache_size//cache_block_size
    tag, index, offest = get_tag_index_offest(actual_address)
    if cache_type == 'instruction_cache' :
        return read_from_instruction_cache(tag, index, offest, num_bytes)
    else :
        return read_from_data_cache(tag, index, offest, num_bytes)


def write_data_to_memory(new_data, actual_address, num_bytes, cache_type) :

    global cache_size, cache_block_size, blocks_per_set, block_placement_type

    num_blocks = cache_size//cache_block_size
    tag, index, offest = get_tag_index_offest(actual_address)
    if cache_type == 'data_cache' :
        return write_to_data_cache(tag, index, offest, num_bytes, new_data)


def show_victim_blocks() :

    global victim_block_counter, victim_block

    return victim_block


def show_block_accesses() :

    global block_access_counter, block_access
    
    return block_access


def show_instruction_cache_data() :

    global cache_size, cache_block_size, blocks_per_set, block_placement_type


    valid_data = []
    num_blocks = cache_size//cache_block_size

    if block_placement_type == 'direct_mapped' :
        for index in range(num_blocks) :
            if instruction_cache['block_validity'][index] == 'valid' :
                valid_data.append([instruction_cache['tag_array'][index],instruction_cache['cache'][index]])
        return valid_data

    else :
        if block_placement_type == 'fully_associative' :
            blocks_per_set = num_blocks
        num_sets = num_blocks//blocks_per_set
        for index in range(num_sets) :
            for way_number in range(blocks_per_set) :
                if instruction_cache['block_validity'][index][way_number] == 'valid' :
                    valid_data.append([instruction_cache['tag_array'][index][way_number],instruction_cache['cache'][index][way_number]])
        return valid_data


def show_data_cache_data() :

    global cache_size, cache_block_size, blocks_per_set, block_placement_type


    valid_data = []
    num_blocks = cache_size//cache_block_size

    if block_placement_type == 'direct_mapped' :
        for index in range(num_blocks) :
            if data_cache['block_validity'][index] == 'valid' :
                valid_data.append([data_cache['tag_array'][index],data_cache['cache'][index]])
        return valid_data

    else :
        if block_placement_type == 'fully_associative' :
            blocks_per_set = num_blocks
        num_sets = num_blocks//blocks_per_set
        for index in range(num_sets) :
            for way_number in range(blocks_per_set) :
                if data_cache['block_validity'][index][way_number] == 'valid' :
                    valid_data.append([data_cache['tag_array'][index][way_number],data_cache['cache'][index][way_number]])
        return valid_data






