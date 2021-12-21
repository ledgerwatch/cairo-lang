import json

from starkware.cairo.lang.compiler.program import Program, ProgramBase
from starkware.cairo.grpc.helper import InvokeParams, get_feeder_gateway_client_wrapper, get_gateway_client_wrapper
from starkware.cairo.lang.vm.cairo_runner import CairoRunner
from starkware.cairo.lang.vm.utils import RunResources

from starkware.starknet.compiler.compile import get_selector_from_name
from starkware.starknet.public.abi_structs import identifier_manager_from_abi
from starkware.starknet.services.api.gateway.transaction import InvokeFunction
from starkware.starknet.cli.starknet_cli import validate_arguments, parse_inputs, get_gateway_client, get_feeder_gateway_client, handle_network_param
from starkware.starkware_utils.error_handling import StarkErrorCode

def call_cairo_run(params: {}, code) -> []:
    proof_mode = False
    steps_input = None

    program: ProgramBase = json.loads(code)
    runner = CairoRunner(
        program=Program.Schema().load(program),
        layout="small",
        proof_mode=proof_mode
    )
    runner.initialize_segments()
    entrypoint = runner.initialize_main_entrypoint()

    runner.initialize_vm(hint_locals={"program_input": params})
    try:
        callback = runner.vm.program.get_label(params['function'] if params['function'] is not None else 'default')
        runner.vm.static_locals.update({"callback": callback})
    except Exception as exc:
        callback = runner.vm.program.get_label('default')
        runner.vm.static_locals.update({"callback": callback})

    additional_steps = 1 if proof_mode else 0

    max_steps = steps_input - additional_steps if steps_input is not None else None
    runner.run_until_pc(entrypoint, run_resources=RunResources(steps=max_steps))
    if proof_mode:
        # Run one more step to make sure the last pc that was executed (rather than the pc
        # after it) is __end__.
        runner.run_for_steps(1)

    runner.original_steps = runner.vm.current_step

    disable_trace_padding = False

    runner.end_run(disable_trace_padding=disable_trace_padding)

    runner.read_return_values()

    output_runner = runner.builtin_runners["output_builtin"]
    _, size = output_runner.get_used_cells_and_allocated_size(runner)
    return_values = []
    for i in range(size):
        val = runner.vm_memory.get(output_runner.base + i)
        return_values.append(val)

    return return_values


async def call_starknet_run(params_dict: {}):
    params = InvokeParams(params_dict)

    call = False if params.type == "invoke" else True

    inputs = parse_inputs(params.inputs)
    signature = parse_inputs(params.signature)

    abi = json.loads(params.abi)

    assert params.address.startswith("0x"), f"The address must start with '0x'. Got: {params.address}."
    try:
        address = int(params.address, 16)
    except ValueError:
        raise ValueError(f"Invalid address format: {params.address}.")

    for abi_entry in abi:
        if abi_entry["type"] == "function" and abi_entry["name"] == params.function:
            validate_arguments(
                inputs=inputs,
                abi_entry=abi_entry,
                identifier_manager=identifier_manager_from_abi(abi=abi),
            )
            break
    else:
        raise Exception(f"Function {params.function} not found.")

    selector = get_selector_from_name(params.function)
    calldata = inputs
    handle_network_param(params)

    tx = InvokeFunction(
        contract_address=address,
        entry_point_selector=selector,
        calldata=calldata,
        signature=signature,
    )

    result = []

    if call:
        feeder_client = get_feeder_gateway_client_wrapper(params)
        gateway_response = await feeder_client.call_contract(
            invoke_tx=tx, block_hash=params.block_hash, block_number=params.block_number
        )
        result.append(gateway_response["result"])
    else:
        gateway_client = get_gateway_client_wrapper(params)
        gateway_response = await gateway_client.add_transaction(tx=tx)
        assert (
                gateway_response["code"] == StarkErrorCode.TRANSACTION_RECEIVED.name
        ), f"Failed to send transaction. Response: {gateway_response}."
        result.append(gateway_response["code"])
        result.append(gateway_response["transaction_hash"])

    return result
