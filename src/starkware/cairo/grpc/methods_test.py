import pytest
import os
import re
import json

from starkware.cairo.grpc.methods import call_cairo_run, call_starknet_run
from starkware.cairo.grpc.helper import MockGateway
from starkware.cairo.lang.cairo_constants import DEFAULT_PRIME
from starkware.cairo.lang.compiler.cairo_compile import compile_cairo_files
from starkware.cairo.lang.vm.vm_exceptions import VmException

CODE_FILE = os.path.join(os.path.dirname(__file__), "test.cairo")
CONTRACT_FILE = os.path.join(os.path.dirname(__file__), "test_contract.cairo")

from starkware.starknet.testing.contract import StarknetContract
from starkware.starknet.testing.starknet import Starknet
from starkware.starkware_utils.error_handling import StarkErrorCode

@pytest.fixture
async def starknet() -> Starknet:
    return await Starknet.empty()


@pytest.fixture
async def contract(starknet: Starknet) -> StarknetContract:
    return await starknet.deploy(source=CONTRACT_FILE)


@pytest.mark.asyncio
async def test_cairo_call():
    number = 25
    code_definition = compile_cairo_files([CODE_FILE], debug_info=True, prime=DEFAULT_PRIME)
    code = code_definition.serialize()
    params = {"input": number, "function": "double"}
    result = call_cairo_run(params, code)
    assert len(result) == 1
    assert result[0] == number * 2

    params = {"input": number, "function": "pow"}
    result = call_cairo_run(params, code)
    assert len(result) == 1
    assert result[0] == number * number

    params = {"input": number, "function": "unknown"}
    result = call_cairo_run(params, code)
    assert len(result) == 1
    assert result[0] == number

    params = {"function": "pow"}
    with pytest.raises(
        VmException, match=re.escape("KeyError: 'input'")
    ):
        call_cairo_run(params, code)


@pytest.mark.asyncio
async def test_starknet_call(contract: StarknetContract):

    abi = [v for k, v in contract._abi_function_mapping.items()]

    paramsDict = {
        "type": "call",
        "address": hex(contract.contract_address),
        "function": "get_balance",
        "abi": json.dumps(abi),
        "testing": True
    }

    result = await call_starknet_run(paramsDict)
    print("++++++++++++++++")
    print("++++++++++++++++")
    print(result)
    assert len(result) == 1
    assert result[0] == MockGateway.CALL_RESULT


@pytest.mark.asyncio
async def test_starknet_invoke(contract: StarknetContract):

    abi = [v for k, v in contract._abi_function_mapping.items()]

    paramsDict = {
        "type": "invoke",
        "address": hex(contract.contract_address),
        "function": "increase_balance",
        "inputs": "1234",
        "abi": json.dumps(abi),
        "testing": True
    }

    result = await call_starknet_run(paramsDict)
    assert len(result) == 2
    assert result[0] == StarkErrorCode.TRANSACTION_RECEIVED.name
    assert result[1] == MockGateway.INVOKE_RESULT


@pytest.mark.asyncio
async def test_starknet_address_error(contract: StarknetContract):
    abi = [v for k, v in contract._abi_function_mapping.items()]

    paramsDict = {
        "type": "invoke",
        "address": "123123",
        "function": "increase_balance",
        "inputs": "1234",
        "abi": json.dumps(abi),
        "testing": True
    }
    with pytest.raises(
        AssertionError, match=re.escape("The address must start with '0x'")
    ):
        await call_starknet_run(paramsDict)

@pytest.mark.asyncio
async def test_starknet_unknown_function_error(contract: StarknetContract):
    abi = [v for k, v in contract._abi_function_mapping.items()]

    paramsDict = {
        "type": "invoke",
        "address": hex(contract.contract_address),
        "function": "unknown",
        "inputs": "1234",
        "abi": json.dumps(abi),
        "testing": True
    }
    with pytest.raises(
        Exception, match=re.escape(f"Function {paramsDict['function']} not found.")
    ):
        await call_starknet_run(paramsDict)
