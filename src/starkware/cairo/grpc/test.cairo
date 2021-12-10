%builtins output

from starkware.cairo.common.serialize import serialize_word
from starkware.cairo.common.alloc import alloc
from starkware.cairo.common.registers import get_label_location
from starkware.cairo.common.invoke import invoke

func double(num) -> (multiply):
    return (multiply=num * 2)
end

func pow(num) -> (multiply):
    return (multiply=num * num)
end

func default(value) -> (value):
    return (value=value)
end

func main{output_ptr : felt*}():
    %{ memory[ap] = callback %}
    [ap] = [ap]; ap++
    let (callback) = get_label_location([ap-1])

    %{ memory[ap] = program_input['input'] %}
    [ap] = [ap]; ap++

    call abs callback

    [ap] = [ap-1]
    [ap] = [output_ptr]; ap++
    [ap] = output_ptr + 1; ap++

    ret
end